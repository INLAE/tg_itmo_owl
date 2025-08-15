# repository.py
import os, sqlite3
from typing import Iterable, List, Optional
from domain import Program, Course
from config import DB_PATH, DATA_DIR

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS programs(
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  plan_url TEXT,
  about_html TEXT,
  faq_text TEXT
);
CREATE TABLE IF NOT EXISTS courses(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  program_code TEXT NOT NULL,
  name TEXT NOT NULL,
  semester INTEGER,
  type TEXT,
  hours INTEGER,
  credits REAL,
  raw TEXT,
  tags TEXT,
  FOREIGN KEY(program_code) REFERENCES programs(code)
);
"""

class Repository:
    def __init__(self, path: str = DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys=ON;")
        for stmt in SCHEMA.strip().split(";"):
            if stmt.strip():
                self.conn.execute(stmt)
        self.conn.commit()

    def upsert_program(self, p: Program) -> None:
        self.conn.execute(
            """INSERT INTO programs(code,name,url,plan_url,about_html,faq_text)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(code) DO UPDATE SET
                 name=excluded.name, url=excluded.url, plan_url=excluded.plan_url,
                 about_html=excluded.about_html, faq_text=excluded.faq_text""",
            (p.code, p.name, p.url, p.plan_url, p.about_html, p.faq_text),
        )
        self.conn.commit()

    def replace_courses(self, program_code: str, courses: Iterable[Course]) -> None:
        self.conn.execute("DELETE FROM courses WHERE program_code=?", (program_code,))
        self.conn.executemany(
            """INSERT INTO courses(program_code,name,semester,type,hours,credits,raw,tags)
               VALUES(?,?,?,?,?,?,?,?)""",
            [
                (
                    c.program_code,
                    c.name,
                    c.semester,
                    c.type,
                    c.hours,
                    c.credits,
                    c.raw,
                    ",".join(c.tags or []),
                )
                for c in courses
            ],
        )
        self.conn.commit()

    def get_program(self, code: str) -> Optional[Program]:
        row = self.conn.execute(
            "SELECT code,name,url,plan_url,about_html,faq_text FROM programs WHERE code=?", (code,)
        ).fetchone()
        if not row:
            return None
        return Program(*row)

    def list_programs(self) -> List[Program]:
        rows = self.conn.execute("SELECT code,name,url,plan_url,about_html,faq_text FROM programs").fetchall()
        return [Program(*r) for r in rows]

    def list_courses(self, program_code: Optional[str] = None) -> List[Course]:
        cur = self.conn.cursor()
        if program_code:
            cur.execute(
                "SELECT program_code,name,semester,type,hours,credits,raw,tags FROM courses WHERE program_code=?",
                (program_code,),
            )
        else:
            cur.execute("SELECT program_code,name,semester,type,hours,credits,raw,tags FROM courses")
        res = []
        for row in cur.fetchall():
            tags = row[7].split(",") if row[7] else []
            res.append(Course(row[0], row[1], row[2], row[3], row[4], row[5], row[6], tags))
        return res