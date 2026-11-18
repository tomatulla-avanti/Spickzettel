import json
import os
import shutil
from datetime import datetime

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import db, ingest, recipes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app = FastAPI(title="Spickzettel")
db.init_db()


def fts_query(q):
    tokens = [t.replace('"', "") for t in q.split() if t.strip()]
    return " ".join('"{}"'.format(t) for t in tokens)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: str = "", cook: str = "", uploaded: int = 0):
    conn = db.get_conn()
    results = []
    if q.strip():
        try:
            results = conn.execute(
                "SELECT d.*, rank FROM documents_fts "
                "JOIN documents d ON d.id = documents_fts.rowid "
                "WHERE documents_fts MATCH ? ORDER BY rank LIMIT 50",
                (fts_query(q),),
            ).fetchall()
        except Exception:
            results = []
    docs = conn.execute(
        "SELECT * FROM documents ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    recs = conn.execute("SELECT * FROM recipes ORDER BY title").fetchall()
    cook_results = []
    if cook.strip():
        have = [h.strip() for h in cook.split(",") if h.strip()]
        scored = []
        for r in recs:
            ings = json.loads(r["ingredients"] or "[]")
            s, matched = recipes.score_recipe(ings, have)
            if s > 0:
                scored.append({"score": s, "recipe": r, "matched": matched})
        scored.sort(key=lambda x: x["score"], reverse=True)
        cook_results = scored
    recipes_prepared = [
        {"r": r, "ings": json.loads(r["ingredients"] or "[]")} for r in recs
    ]
    conn.close()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "q": q,
            "results": results,
            "docs": docs,
            "recipes": recipes_prepared,
            "cook": cook,
            "cook_results": cook_results,
            "uploaded": uploaded,
            "ocr_available": ingest.OCR_AVAILABLE,
        },
    )


@app.post("/upload")
def upload(
    files: list[UploadFile] = File(...),
    title: str = Form(""),
    tags: str = Form(""),
    note: str = Form(""),
    kind: str = Form("dokument"),
):
    conn = db.get_conn()
    saved = 0
    for file in files:
        original = os.path.basename((file.filename or "").replace("\\", "/"))
        if not original:
            continue
        saved += 1
        print("UPLOAD empfangen:", original, flush=True)
        stored_name = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + original
        stored_path = os.path.join(db.UPLOAD_DIR, stored_name)
        with open(stored_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        text = ingest.extract_text(stored_path)
        now = datetime.now().isoformat(timespec="seconds")
        if kind == "rezept":
            ingredients, steps = recipes.parse_recipe_text(text)
            conn.execute(
                "INSERT INTO recipes (title, source, ingredients, steps, notes, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (
                    title or os.path.splitext(original)[0],
                    original,
                    json.dumps(ingredients, ensure_ascii=False),
                    "\n".join(steps),
                    note,
                    now,
                ),
            )
        else:
            conn.execute(
                "INSERT INTO documents (filename, stored_path, title, tags, note, extracted_text, filetype, created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    original,
                    stored_path,
                    title or original,
                    tags,
                    note,
                    text,
                    os.path.splitext(original)[1].lower(),
                    now,
                ),
            )
    conn.commit()
    conn.close()
    print("UPLOAD fertig: %d Datei(en) gespeichert" % saved, flush=True)
    return RedirectResponse(url="/?uploaded=%d" % saved, status_code=303)


@app.post("/import-uploads")
def import_uploads():
    conn = db.get_conn()
    existing = {r[0] for r in conn.execute("SELECT filename FROM documents")}
    existing |= {r[0] for r in conn.execute("SELECT source FROM recipes")}
    saved = 0
    for name in sorted(os.listdir(db.UPLOAD_DIR)):
        path = os.path.join(db.UPLOAD_DIR, name)
        if not os.path.isfile(path) or name in existing:
            continue
        text = ingest.extract_text(path)
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO documents (filename, stored_path, title, tags, note, extracted_text, filetype, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (name, path, name, "", "", text, os.path.splitext(name)[1].lower(), now),
        )
        saved += 1
        print("IMPORT:", name, flush=True)
    conn.commit()
    conn.close()
    print("IMPORT fertig: %d neue Datei(en)" % saved, flush=True)
    return RedirectResponse(url="/?uploaded=%d" % saved, status_code=303)


@app.post("/recipe/add")
def add_recipe(
    title: str = Form(...),
    ingredients: str = Form(""),
    steps: str = Form(""),
    notes: str = Form(""),
):
    ings = [
        l.strip().lstrip("-•*– ") for l in ingredients.splitlines() if l.strip()
    ]
    now = datetime.now().isoformat(timespec="seconds")
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO recipes (title, source, ingredients, steps, notes, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (title, "manuell", json.dumps(ings, ensure_ascii=False), steps, notes, now),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/document/{doc_id}", response_class=HTMLResponse)
def document_detail(request: Request, doc_id: int):
    conn = db.get_conn()
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    if not doc:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "document.html", {"doc": doc})


@app.post("/document/{doc_id}/delete")
def delete_document(doc_id: int):
    conn = db.get_conn()
    doc = conn.execute(
        "SELECT stored_path FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    if doc and doc["stored_path"] and os.path.exists(doc["stored_path"]):
        os.remove(doc["stored_path"])
    return RedirectResponse(url="/", status_code=303)
