import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "app.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    stored_path TEXT,
    title TEXT,
    tags TEXT,
    note TEXT,
    extracted_text TEXT,
    filetype TEXT,
    created_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title, tags, note, extracted_text,
    content='documents', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, tags, note, extracted_text)
    VALUES (new.id, new.title, new.tags, new.note, new.extracted_text);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, tags, note, extracted_text)
    VALUES ('delete', old.id, old.title, old.tags, old.note, old.extracted_text);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, tags, note, extracted_text)
    VALUES ('delete', old.id, old.title, old.tags, old.note, old.extracted_text);
    INSERT INTO documents_fts(rowid, title, tags, note, extracted_text)
    VALUES (new.id, new.title, new.tags, new.note, new.extracted_text);
END;

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    source TEXT,
    ingredients TEXT,
    steps TEXT,
    notes TEXT,
    created_at TEXT
);
"""


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
