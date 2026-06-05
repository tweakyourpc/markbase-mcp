import unittest

import mcp_server


class SaveNoteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.original_request = mcp_server._request

    async def asyncTearDown(self) -> None:
        mcp_server._request = self.original_request

    async def test_save_note_request_payload_includes_provenance(self) -> None:
        captured = {}

        async def fake_request(method, path, **kwargs):
            captured["method"] = method
            captured["path"] = path
            captured["json"] = kwargs["json"]
            return {"path": "notes/example", "title": "Example"}

        mcp_server._request = fake_request

        result = await mcp_server.save_note("Example", "Body", ["#markbase"])

        self.assertEqual(result, {"path": "notes/example", "title": "Example"})
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["path"], "/api/note")
        self.assertEqual(captured["json"]["title"], "Example")
        self.assertEqual(captured["json"]["tags"], ["#markbase"])
        self.assertEqual(captured["json"]["created_via"], "markbase-mcp")
        self.assertEqual(captured["json"]["authorship"], "agent-authored")
        self.assertEqual(captured["json"]["ai_processing"], "none")
        self.assertTrue(captured["json"]["content"].startswith("---\n"))
        self.assertIn('created_via: "markbase-mcp"', captured["json"]["content"])
        self.assertIn('authorship: "agent-authored"', captured["json"]["content"])
        self.assertIn('ai_processing: "none"', captured["json"]["content"])
        self.assertTrue(captured["json"]["content"].endswith("Body"))

    async def test_save_note_remains_compatible_with_existing_fields(self) -> None:
        captured = {}

        async def fake_request(method, path, **kwargs):
            captured.update(kwargs["json"])
            return {"path": "notes/compat", "title": kwargs["json"]["title"]}

        mcp_server._request = fake_request

        result = await mcp_server.save_note("Compat", "Plain content")

        self.assertEqual(result["path"], "notes/compat")
        self.assertEqual(captured["title"], "Compat")
        self.assertIn("Plain content", captured["content"])
        self.assertEqual(captured["tags"], [])

    async def test_save_note_humanizes_older_api_errors(self) -> None:
        async def fake_request(method, path, **kwargs):
            return {"error": "MarkBase is unreachable or returned an error at http://example"}

        mcp_server._request = fake_request

        result = await mcp_server.save_note("Compat", "Plain content")

        self.assertEqual(result, "MarkBase is unreachable or returned an error at http://example")

    def test_save_note_payload_allows_authorship_override(self) -> None:
        payload = mcp_server._save_note_payload(
            title="Manual",
            content="Body",
            tags=[],
            authorship="agent-assisted",
        )

        self.assertEqual(payload["authorship"], "agent-assisted")
        self.assertIn('authorship: "agent-assisted"', payload["content"])


if __name__ == "__main__":
    unittest.main()
