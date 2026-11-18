import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, ConfigDict
from backend.app.categories import CATEGORIES
from backend.app.history import History
from ml.inference import Predictor

ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger('codeguard')
logging.basicConfig(level=logging.INFO, format='%(message)s')
MAX_BYTES = 100_000

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=1, max_length=20000)
    language: str = Field(min_length=1, max_length=20)

    @field_validator('code')
    @classmethod
    def code_valid(cls, value):
        if not value.strip() or '\x00' in value: raise ValueError('Code must be nonempty text without null bytes')
        return value

def create_app(artifact_dir=None, history_enabled=None, database_url=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.predictor = None
        app.state.history = None
        try:
            app.state.predictor = Predictor(artifact_dir or os.getenv('MODEL_DIR', str(ROOT / 'ml/artifacts')))
        except Exception as error:
            logger.error(json.dumps(dict(event='model_unavailable', error_type=type(error).__name__)))
        enabled = history_enabled if history_enabled is not None else os.getenv('HISTORY_ENABLED', 'false').lower() == 'true'
        if enabled:
            app.state.history = History(database_url or os.getenv('DATABASE_URL', 'sqlite:///./history.db'))
        yield
        if app.state.history: app.state.history.engine.dispose()

    app = FastAPI(title='CodeGuard AI', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080').split(','), allow_methods=['GET','POST','DELETE'], allow_headers=['Content-Type'])

    @app.middleware('http')
    async def limit_and_log(request: Request, call_next):
        start = time.monotonic()
        # Enforce actual streamed byte count, including requests without Content-Length.
        size = 0
        chunks = []
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_BYTES: return JSONResponse(status_code=413, content={'detail': 'Request exceeds 100 KB limit'})
            chunks.append(chunk)
        request._body = b''.join(chunks)
        response = await call_next(request)
        logger.info(json.dumps(dict(event='request', method=request.method, status=response.status_code, duration_ms=round((time.monotonic()-start)*1000))))
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Pydantic's default errors echo the source input; omit it.
        return JSONResponse(status_code=422, content={'detail': [{'location': list(e['loc']), 'message': e['msg']} for e in error.errors()]})

    @app.exception_handler(Exception)
    async def internal_error(request, error):
        logger.error(json.dumps(dict(event='internal_error', error_type=type(error).__name__)))
        return JSONResponse(status_code=500, content={'detail': 'Internal service error'})

    def predictor():
        if app.state.predictor is None: raise HTTPException(503, 'Model unavailable. Download data and run preparation and training.')
        return app.state.predictor

    @app.get('/api/health')
    def health():
        return dict(status='ok' if app.state.predictor else 'degraded', model_ready=app.state.predictor is not None, history_enabled=app.state.history is not None)

    @app.get('/api/categories')
    def categories(): return CATEGORIES

    @app.get('/api/model-info')
    def model_info(): return predictor().metadata

    @app.post('/api/predict')
    def predict(payload: PredictRequest):
        model = predictor()
        language = payload.language.strip().lower()
        if language not in model.metadata['supported_languages']:
            raise HTTPException(422, f"Unsupported language. Choose from: {', '.join(model.metadata['supported_languages'])}")
        result = model.predict(payload.code, language)
        category = CATEGORIES[result['leading_class_id']]
        result.update(explanation=category, severity='Not assessed' if result['uncertain'] else category['severity'],
                      severity_note='Heuristic only; actual severity depends on exploitability and application context.',
                      highlighted_lines=[], localization='Function-level classification; exact line location not determined.',
                      confidence_note='Calibrated model estimate on synthetic Juliet data; not a guarantee.',
                      language=language, history_id=None)
        if app.state.history:
            result['history_id'] = app.state.history.add(language, {k: result[k] for k in ['predicted_category','class_id','confidence','uncertain','model_version']})
        return result

    @app.get('/api/history')
    def history():
        return dict(enabled=app.state.history is not None, scans=app.state.history.list() if app.state.history else [],
                    summary=app.state.history.summary() if app.state.history else None)

    @app.delete('/api/history/{scan_id}', status_code=204)
    def delete_history(scan_id: int):
        if not app.state.history: raise HTTPException(404, 'History is disabled')
        if not app.state.history.delete(scan_id): raise HTTPException(404, 'Scan not found')

    frontend_dist = ROOT / 'frontend' / 'dist'
    if frontend_dist.exists():
        app.mount('/', StaticFiles(directory=frontend_dist, html=True), name='frontend')

    return app

app = create_app()
