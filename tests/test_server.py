import asyncio
import importlib.util
import json
import unittest
from pathlib import Path


SERVER_PATH = Path(__file__).parents[1] / "web" / "server.py"
SPEC = importlib.util.spec_from_file_location("server", SERVER_PATH)
assert SPEC is not None and SPEC.loader is not None
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class ServerTest(unittest.TestCase):
    def request(self, path: str, method: str = "GET") -> list[dict]:
        messages: list[dict] = []

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            messages.append(message)

        scope = {"type": "http", "method": method, "path": path}
        asyncio.run(server.app(scope, receive, send))
        return messages

    def test_health(self) -> None:
        response = self.request("/health")

        self.assertEqual(response[0]["status"], 200)
        self.assertEqual(json.loads(response[1]["body"]), {"status": "ok"})

    def test_missing_route(self) -> None:
        response = self.request("/missing")

        self.assertEqual(response[0]["status"], 404)
        self.assertEqual(json.loads(response[1]["body"]), {"error": "not_found"})

    def test_head_omits_body(self) -> None:
        response = self.request("/health", method="HEAD")

        self.assertEqual(response[0]["status"], 200)
        self.assertEqual(response[1]["body"], b"")

    def test_login_renders_jinja_template(self) -> None:
        response = self.request("/login")

        self.assertEqual(response[0]["status"], 200)
        self.assertIn(b"text/html", dict(response[0]["headers"])[b"content-type"])
        self.assertIn(b'<form method="post" action="/api/login">', response[1]["body"])

    def test_signup_renders_jinja_template(self) -> None:
        response = self.request("/signup")

        self.assertEqual(response[0]["status"], 200)
        self.assertIn(b"Monero wallet address", response[1]["body"])


if __name__ == "__main__":
    unittest.main()
