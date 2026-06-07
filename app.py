from __future__ import annotations

from copy import deepcopy
import json
import os
from io import BytesIO
from typing import Any

import anthropic
import pdfplumber
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

SYSTEM_PROMPT = """You are an expert technical recruiter and resume coach specializing in software engineering and AI/ML roles.

Analyze the resume provided and return ONLY a valid JSON object with this exact structure:

{
  "overall_score": <integer 0-100>,
  "summary": "<2-3 sentence honest overall assessment>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
  "missing_keywords": ["<keyword 1>", "<keyword 2>", "..."],
  "suggestions": [
    { "section": "<section name>", "issue": "<what's wrong>", "fix": "<specific fix>" },
    { "section": "<section name>", "issue": "<what's wrong>", "fix": "<specific fix>" },
    { "section": "<section name>", "issue": "<what's wrong>", "fix": "<specific fix>" }
  ],
  "ats_score": <integer 0-100>,
  "ats_notes": "<1-2 sentences on ATS compatibility>"
}"""

DEMO_ANALYSIS = {
    "overall_score": 84,
    "summary": (
        "This resume reads like a strong early-career to mid-level software engineer profile with clear product impact and a solid technical foundation. "
        "The biggest opportunity is tightening the narrative around measurable outcomes and making AI/ML experience more explicit for target roles."
    ),
    "strengths": [
        "Clear progression across internships, projects, and hands-on engineering work",
        "Strong technical stack coverage across backend, frontend, and cloud tooling",
        "Impact-oriented bullets that already hint at ownership and collaboration",
    ],
    "weaknesses": [
        "Several bullets describe responsibilities without quantifying business impact",
        "AI/ML exposure is present but not positioned strongly enough for AI-focused roles",
        "Skills section could be grouped more cleanly for faster recruiter and ATS scanning",
    ],
    "missing_keywords": [
        "LLM evaluation",
        "RAG",
        "vector databases",
        "system design",
        "CI/CD",
        "observability",
    ],
    "suggestions": [
        {
            "section": "Experience",
            "issue": "Bullets show solid work but do not consistently quantify results.",
            "fix": "Add metrics such as latency reduction, revenue impact, user growth, or time saved for at least the top 3 bullets.",
        },
        {
            "section": "Projects",
            "issue": "The strongest technical projects are not framed around the problem solved and the architecture used.",
            "fix": "Lead each project bullet with the outcome, then mention the stack and one technical challenge you solved.",
        },
        {
            "section": "Skills",
            "issue": "The skills list is broad but visually flat, which makes it harder to scan quickly.",
            "fix": "Split skills into categories such as Languages, Frameworks, Cloud, and AI/ML to improve readability and ATS parsing.",
        },
    ],
    "ats_score": 88,
    "ats_notes": (
        "The resume is generally ATS-friendly because it uses readable headings and straightforward formatting. "
        "It would score even better with tighter keyword alignment to the exact target job description."
    ),
    "demo_mode": True,
    "source_name": "Demo Candidate - Software Engineer Resume",
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[assignment]

    @app.get("/")
    def index() -> str:
        return render_template("index.html", max_upload_mb=MAX_UPLOAD_BYTES // (1024 * 1024))

    @app.get("/api/demo")
    def demo() -> tuple[dict[str, Any], int]:
        return deepcopy(DEMO_ANALYSIS), 200

    @app.get("/api/health")
    def health() -> tuple[dict[str, Any], int]:
        return {
            "ok": True,
            "anthropic_api_key_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "model": os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
            "demo_available": True,
        }, 200

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_: RequestEntityTooLarge) -> tuple[dict[str, str], int]:
        max_upload_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return {
            "error": f"File is too large. Upload a PDF up to {max_upload_mb} MB.",
        }, 413

    @app.post("/api/analyze")
    def analyze() -> tuple[dict[str, Any], int] | Any:
        uploaded_file = request.files.get("resume")
        if uploaded_file is None:
            return jsonify({"error": "No file uploaded."}), 400

        if not is_pdf(uploaded_file):
            return jsonify({"error": "Only PDF files are supported."}), 400

        try:
            resume_text = extract_text_from_pdf(uploaded_file)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:  # pragma: no cover - depends on malformed user files
            return jsonify({"error": f"Could not read PDF: {exc}"}), 400

        if not resume_text.strip():
            return jsonify({"error": "Could not extract readable text from the PDF."}), 400

        try:
            result = analyze_resume(resume_text)
            return jsonify(result), 200
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 503
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse the AI response as JSON."}), 502
        except anthropic.APIError as exc:
            return jsonify({"error": f"Anthropic API error: {exc}"}), 502
        except Exception as exc:  # pragma: no cover - defensive fallback
            return jsonify({"error": f"Unexpected server error: {exc}"}), 500

    return app


def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your environment or .env file.")
    return anthropic.Anthropic(api_key=api_key)


def is_pdf(uploaded_file: FileStorage) -> bool:
    filename = (uploaded_file.filename or "").lower()
    return filename.endswith(".pdf")


def extract_text_from_pdf(uploaded_file: FileStorage) -> str:
    file_bytes = uploaded_file.read()
    if not file_bytes:
        raise ValueError("Uploaded PDF is empty.")

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]

    return "\n".join(page for page in pages if page.strip())


def analyze_resume(resume_text: str) -> dict[str, Any]:
    client = get_anthropic_client()
    message = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=1500,
        temperature=0.2,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze this resume and respond with JSON only:\n\n{resume_text}",
                    }
                ],
            }
        ],
    )

    raw_response = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    ).strip()

    if not raw_response:
        raise RuntimeError("The AI returned an empty response.")

    return parse_json_payload(raw_response)


def parse_json_payload(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            cleaned = "\n".join(lines[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(cleaned[start : end + 1])

    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("Top-level JSON value must be an object.", cleaned, 0)

    return parsed


app = create_app()


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=debug_mode, host="127.0.0.1", port=port)
