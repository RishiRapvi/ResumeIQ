from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app import app, get_template_context
from scripts.build_github_pages import build_pages


class ResumeIQAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

    def test_homepage_loads(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ResumeIQ", response.data)
        self.assertIn(b"What This Project Demonstrates", response.data)
        self.assertIn(b"Recruiter-Friendly Demo", response.data)
        self.assertIn(b"Try Demo Mode", response.data)

    def test_sample_resume_page_loads(self) -> None:
        response = self.client.get("/sample-resume")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Maya Chen", response.data)
        self.assertIn(b"ResumeIQ Demo Artifact", response.data)

    def test_static_template_context_uses_relative_links(self) -> None:
        context = get_template_context("static")

        self.assertEqual(context["site_mode"], "static")
        self.assertFalse(context["upload_enabled"])
        self.assertEqual(context["home_href"], "./index.html")
        self.assertEqual(context["sample_resume_href"], "./sample-resume.html")

    def test_health_endpoint_returns_json(self) -> None:
        response = self.client.get("/api/health")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["demo_available"])
        self.assertIn("model", payload)

    def test_demo_endpoint_returns_sample_analysis(self) -> None:
        response = self.client.get("/api/demo")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["demo_mode"])
        self.assertEqual(payload["source_name"], "Demo Candidate - Software Engineer Resume")
        self.assertIn("overall_score", payload)
        self.assertIn("suggestions", payload)

    def test_analyze_requires_file(self) -> None:
        response = self.client.post("/api/analyze", data={}, content_type="multipart/form-data")
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["error"], "No file uploaded.")

    def test_analyze_rejects_non_pdf(self) -> None:
        response = self.client.post(
            "/api/analyze",
            data={"resume": (BytesIO(b"plain text"), "resume.txt")},
            content_type="multipart/form-data",
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["error"], "Only PDF files are supported.")

    def test_static_build_outputs_docs_site(self) -> None:
        with TemporaryDirectory() as tmpdir:
            build_pages(tmpdir)

            index_html = Path(tmpdir, "index.html").read_text(encoding="utf-8")
            sample_resume_html = Path(tmpdir, "sample-resume.html").read_text(encoding="utf-8")

            self.assertIn("Static GitHub Pages preview", index_html)
            self.assertIn("./sample-resume.html", index_html)
            self.assertIn("View Flask Source", index_html)
            self.assertIn("./index.html", sample_resume_html)


if __name__ == "__main__":
    unittest.main()
