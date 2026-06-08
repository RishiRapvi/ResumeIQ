from __future__ import annotations

from pathlib import Path
import sys

from flask import render_template

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app, get_template_context


def build_pages(output_dir: str = "docs") -> None:
    docs_dir = Path(output_dir)
    if not docs_dir.is_absolute():
        docs_dir = ROOT_DIR / docs_dir
    docs_dir.mkdir(parents=True, exist_ok=True)

    context = get_template_context("static")

    with app.app_context():
        index_html = render_template("index.html", **context)
        sample_resume_html = render_template("sample_resume.html", **context)

    (docs_dir / "index.html").write_text(index_html, encoding="utf-8")
    (docs_dir / "sample-resume.html").write_text(sample_resume_html, encoding="utf-8")
    (docs_dir / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    build_pages()
