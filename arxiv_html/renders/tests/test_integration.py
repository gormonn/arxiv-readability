import time
import os

from django.conf import settings
from django.test import override_settings
from rest_framework.test import APITestCase
import timeout_decorator


@override_settings(
    ARXIV_SOURCE_URL_FORMAT="/code/arxiv_html/renders/tests/fixtures/{paper_id}.tex"
)
class IntegrationTest(APITestCase):
    """
    Tests the entire rendering system using a local file.
    """

    @timeout_decorator.timeout(10)
    def test_creating_a_render(self):
        response = self.client.put("/renders?id_type=arxiv&paper_id=helloworld")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id_type"], "arxiv")
        self.assertEqual(response.data["paper_id"], "helloworld")
        self.assertEqual(response.data["state"], "PENDING")
        self.assertEqual(response.data["output_url"], None)

        while response.data["state"] in ("PENDING", "STARTED"):
            response = self.client.put("/renders?id_type=arxiv&paper_id=helloworld")
            self.assertEqual(response.status_code, 200)
            time.sleep(0.1)

        render_id = response.data["id"]
        self.assertEqual(response.data["state"], "SUCCESS")
        self.assertEqual(
            response.data["output_url"], f"/media/render-output/{render_id}"
        )
        self.assertIn("No obvious problems", response.data["logs"])
        self.assertIn("Document successfully rendered", response.data["logs"])

        output_path = os.path.join(
            settings.MEDIA_ROOT, "render-output", str(render_id), "index.html"
        )
        with open(output_path) as fh:
            html = fh.read()
            self.assertIn("Generated by LaTeXML", html)
            self.assertIn('<p class="ltx_p">Hello world</p>', html)

    @timeout_decorator.timeout(10)
    def test_creating_a_failing_render(self):
        response = self.client.put("/renders?id_type=arxiv&paper_id=broken")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id_type"], "arxiv")
        self.assertEqual(response.data["paper_id"], "broken")
        self.assertEqual(response.data["state"], "PENDING")
        self.assertEqual(response.data["output_url"], None)

        while response.data["state"] in ("PENDING", "STARTED"):
            response = self.client.put("/renders?id_type=arxiv&paper_id=broken")
            self.assertEqual(response.status_code, 200)
            time.sleep(0.1)

        self.assertEqual(response.data["state"], "FAILURE")
        self.assertIn("1 fatal error", response.data["logs"])
