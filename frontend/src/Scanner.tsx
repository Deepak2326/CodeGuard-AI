import { useRef, useState } from "react";
import {
  ArrowRight,
  Upload,
  Trash2,
  ShieldCheck,
  TriangleAlert,
  LoaderCircle,
  Code2,
} from "lucide-react";
import CodeEditor from "./CodeEditor";
import { api, errorMessage } from "./api";
import type { Prediction } from "./types";
const samples: Record<string, string> = {
  c: "// Demonstration snippet — result comes from the model.\nvoid copy_input(const char *input) {\n    char destination[16];\n    strcpy(destination, input);\n}",
  cpp: "// Demonstration snippet — result comes from the model.\nvoid copy_input(const char *input) {\n    char destination[16];\n    std::strcpy(destination, input);\n}",
  java: '// Demonstration snippet — result comes from the model.\npublic void render(HttpServletRequest request,\n                   HttpServletResponse response) throws Exception {\n    String value = request.getParameter("name");\n    response.getWriter().println("<p>" + value + "</p>");\n}',
};
export default function Scanner({
  languages,
  onScan,
}: {
  languages: string[];
  onScan: () => void;
}) {
  const [language, setLanguage] = useState("c");
  const [code, setCode] = useState("");
  const [result, setResult] = useState<Prediction | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  function edit(value: string) {
    setCode(value);
    setResult(null);
    setError("");
  }
  async function analyze() {
    setBusy(true);
    setResult(null);
    setError("");
    try {
      setResult(await api.predict(code, language));
      onScan();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function upload(file?: File) {
    if (!file) return;
    setResult(null);
    setError("");
    if (file.size > 20000) {
      setError("Upload a source file smaller than 20 KB.");
      return;
    }
    const ext = file.name.split(".").pop()?.toLowerCase();
    const lang =
      ext === "java"
        ? "java"
        : ["cpp", "cc", "cxx"].includes(ext || "")
          ? "cpp"
          : ext === "c"
            ? "c"
            : null;
    if (!lang || !languages.includes(lang)) {
      setError("Choose a supported .c, .cpp, .cc, .cxx, or .java source file.");
      return;
    }
    try {
      const text = await file.text();
      if (text.includes("\0"))
        throw new Error("This file is not plain-text source code.");
      setLanguage(lang);
      edit(text);
    } catch (e) {
      setError(errorMessage(e));
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">WORKSPACE / CODE SCANNER</p>
          <h1>A second look at your code.</h1>
          <p className="muted">
            Analyze a function with a trained machine learning model.
          </p>
        </div>
        <span className="chip">
          <Code2 size={14} /> Function-level analysis
        </span>
      </div>
      <div className="scanner-grid">
        <section className="panel editor-panel">
          <div className="panel-heading">
            <h2>Source code</h2>
            <span className="muted text-xs">Never executed</span>
          </div>
          <div className="editor-toolbar">
            <label>
              Language{" "}
              <select
                aria-label="Language"
                value={language}
                disabled={busy}
                onChange={(e) => {
                  setLanguage(e.target.value);
                  edit(code);
                }}
              >
                {languages.map((l) => (
                  <option key={l} value={l}>
                    {l === "cpp" ? "C++" : l === "java" ? "Java" : "C"}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex gap-2">
              <button
                className="text-button"
                disabled={busy}
                onClick={() => edit(samples[language])}
              >
                Load example
              </button>
              <button
                className="icon-button"
                aria-label="Clear editor"
                disabled={busy}
                onClick={() => edit("")}
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
          <CodeEditor
            code={code}
            language={language}
            onChange={edit}
            disabled={busy}
          />
          <div className="editor-footer">
            <span>{code.length.toLocaleString()} / 20,000 characters</span>
            <span>UTF-8</span>
          </div>
          <div className="scan-actions">
            <input
              ref={fileInput}
              type="file"
              aria-label="Upload source file"
              accept=".c,.cpp,.cc,.cxx,.java"
              hidden
              onChange={(e) => {
                void upload(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
            <button
              className="secondary"
              disabled={busy}
              onClick={() => fileInput.current?.click()}
            >
              <Upload size={16} />
              Upload file
            </button>
            <button
              className="primary"
              disabled={busy || !code.trim() || code.length > 20000}
              onClick={analyze}
            >
              {busy ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <ShieldCheck size={17} />
              )}{" "}
              {busy ? "Analyzing…" : "Analyze code"}
              {!busy && <ArrowRight size={16} />}
            </button>
          </div>
        </section>
        <section className="panel result-panel" aria-live="polite">
          <div className="panel-heading">
            <h2>Analysis report</h2>
            <span className="tiny-label">LIVE INFERENCE</span>
          </div>
          {error ? (
            <div role="alert" className="notice error">
              <TriangleAlert />
              <h3>Analysis could not finish</h3>
              <p>{error}</p>
            </div>
          ) : busy ? (
            <div className="empty-state">
              <LoaderCircle className="spin" size={36} />
              <h3>Inspecting your code</h3>
              <p>Running the trained classifier…</p>
            </div>
          ) : result ? (
            <Result result={result} />
          ) : (
            <div className="empty-state">
              <div className="scan-symbol">
                <ShieldCheck size={36} />
              </div>
              <h3>Ready when you are</h3>
              <p>
                Paste a function or upload a source file.
                <br />
                Your analysis will appear here.
              </p>
              <div className="steps">
                <span>01 / Add code</span>
                <span>02 / Analyze</span>
                <span>03 / Review</span>
              </div>
            </div>
          )}
        </section>
      </div>
      <div className="inline-note">
        <TriangleAlert size={16} />
        <span>
          Research baseline. Review every finding in context. A “Safe Code”
          prediction does not establish security.
        </span>
      </div>
    </>
  );
}
export function Result({ result: r }: { result: Prediction }) {
  return (
    <div className="result-content">
      <div
        className={`verdict ${r.uncertain ? "uncertain" : r.class_id === 4 ? "safe" : "vulnerable"}`}
      >
        <span className="tiny-label">
          {r.uncertain
            ? "MANUAL REVIEW"
            : r.class_id === 4
              ? "NO TARGET WEAKNESS INFERRED"
              : "POTENTIAL VULNERABILITY"}
        </span>
        <h3>{r.predicted_category}</h3>
        <div className="flex gap-2 flex-wrap">
          {r.explanation.cwe.map((c) => (
            <span className="chip" key={c}>
              {c}
            </span>
          ))}
          <span className="chip">{r.severity}</span>
        </div>
      </div>
      <div className="confidence">
        <span>Leading class estimate</span>
        <strong>{(r.confidence * 100).toFixed(1)}%</strong>
      </div>
      <p className="caption">{r.confidence_note}</p>
      {r.uncertain && (
        <ul className="notice">
          {r.uncertainty_reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      <h4>
        {r.uncertain
          ? `Leading hypothesis: ${r.explanation.name}`
          : "What this may mean"}
      </h4>
      <p>{r.explanation.description}</p>
      <h4>Recommended remediation</h4>
      <p>{r.explanation.mitigation}</p>
      <p className="caption">{r.explanation.guidance}</p>
      <details>
        <summary>Class probabilities & scope</summary>
        <div className="probabilities">
          {r.probabilities.map((p) => (
            <div key={p.class_id}>
              <div>
                <span>{p.category}</span>
                <strong>{(p.probability * 100).toFixed(1)}%</strong>
              </div>
              <div className="bar-track">
                <div style={{ width: `${p.probability * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
        <p className="caption">{r.localization}</p>
        <p className="caption">{r.severity_note}</p>
        <p className="caption">Model {r.model_version}</p>
      </details>
    </div>
  );
}
