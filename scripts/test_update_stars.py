from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.parse
import xml.etree.ElementTree as ET

from update_stars import fetch_total_stars, update_svg


def repo(stars, owner="thanhdo257205", fork=False, private=False):
    return {"stargazers_count": stars, "owner": {"login": owner}, "fork": fork, "private": private}


class StarsTests(unittest.TestCase):
    def test_all_pages_and_only_owned_public_non_forks(self):
        first = [repo(9), repo(900, fork=True), repo(800, owner="other"), repo(700, private=True)]
        first += [repo(0)] * (100 - len(first))
        calls = []

        def opener(request, timeout):
            page = int(urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)["page"][0])
            calls.append(page)
            return io.BytesIO(json.dumps(first if page == 1 else [repo(5)]).encode())

        self.assertEqual(fetch_total_stars("thanhdo257205", opener=opener), 14)
        self.assertEqual(calls, [1, 2])

    def test_api_error_payload_is_not_interpreted_as_zero(self):
        with self.assertRaises(ValueError):
            fetch_total_stars("thanhdo257205", opener=lambda *a, **k: io.BytesIO(b'{"message":"error"}'))

    def test_svg_updates_number_accessibility_and_time_preserving_design(self):
        original = Path(__file__).resolve().parents[1] / "assets/stars.svg"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "stars.svg"
            path.write_bytes(original.read_bytes())
            instant = datetime(2026, 10, 19, 3, 0, tzinfo=timezone.utc)
            update_svg(path, "thanhdo257205", 12345, instant)
            result = path.read_bytes()
            nodes = {node.get("id"): node for node in ET.fromstring(result).iter() if node.get("id")}
            self.assertEqual(nodes["star-count"].text, "12345")
            self.assertLess(float(nodes["star-count"].get("font-size")), 65)
            self.assertIn("10:00 GMT+7", nodes["stats-updated"].text)
            self.assertIn("12345", nodes["t"].text)
            self.assertIn("Spring Boot", result.decode())
            update_svg(path, "thanhdo257205", 12345, instant)
            self.assertEqual(result, path.read_bytes())

    def test_invalid_template_does_not_overwrite_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "stars.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                update_svg(path, "thanhdo257205", 9, datetime.now(timezone.utc))
            self.assertEqual(original, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
