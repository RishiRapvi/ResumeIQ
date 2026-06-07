from io import BytesIO
import unittest

from app import app


class ResumeIQAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

    def test_homepage_loads(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ResumeIQ", response.data)

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


if __name__ == "__main__":
    unittest.main()
