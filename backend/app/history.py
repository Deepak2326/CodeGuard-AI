"""Opt-in, metadata-only local history. Submitted source is never persisted."""
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, Text, select, func
from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase): pass

class Scan(Base):
    __tablename__ = 'scans'
    id = Column(Integer, primary_key=True)
    created_at = Column(Text, nullable=False)
    language = Column(Text, nullable=False)
    result = Column(Text, nullable=False)

class History:
    def __init__(self, url):
        self.engine = create_engine(url)
        Base.metadata.create_all(self.engine)

    def add(self, language, result):
        with Session(self.engine) as session:
            row = Scan(created_at=datetime.now(timezone.utc).isoformat(), language=language, result=json.dumps(result))
            session.add(row)
            session.commit()
            return row.id

    def list(self):
        with Session(self.engine) as session:
            return [dict(id=r.id, created_at=r.created_at, language=r.language, **json.loads(r.result)) for r in session.scalars(select(Scan).order_by(Scan.id.desc()).limit(100))]

    def delete(self, scan_id):
        with Session(self.engine) as session:
            row = session.get(Scan, scan_id)
            if row is None: return False
            session.delete(row)
            session.commit()
            return True

    def summary(self):
        """Aggregate all saved results, independently of the recent-record limit."""
        counts = {str(i): 0 for i in range(5)}
        uncertain = 0
        category = func.json_extract(Scan.result, '$.class_id')
        with Session(self.engine) as session:
            for class_id, count in session.execute(select(category, func.count(Scan.id)).group_by(category)):
                if class_id is None:
                    uncertain += count
                else:
                    counts[str(class_id)] += count
        return dict(total=sum(counts.values()) + uncertain, vulnerable=sum(counts[str(i)] for i in range(4)),
                    safe=counts['4'], uncertain=uncertain, categories=counts)
