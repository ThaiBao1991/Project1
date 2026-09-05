import unittest
from unittest.mock import patch, MagicMock

import gemini_safe
from gemini_safe import GeminiCoordinator, ErrorKind, extract_text


class GeminiSafeFallbackTests(unittest.TestCase):
    def test_extract_text_multiple_parts_and_thoughts(self):
        # Case 1: normal single part
        body1 = {"candidates": [{"content": {"parts": [{"text": "Hello world"}]}}]}
        self.assertEqual(extract_text(body1), "Hello world")

        # Case 2: thought block followed by real text
        body2 = {"candidates": [{"content": {"parts": [
            {"thought": "Thinking about the question..."},
            {"text": "Actual answer here"}
        ]}}]}
        self.assertEqual(extract_text(body2), "Actual answer here")

        # Case 3: multiple text parts
        body3 = {"candidates": [{"content": {"parts": [
            {"text": "Part 1 - "},
            {"text": "Part 2"}
        ]}}]}
        self.assertEqual(extract_text(body3), "Part 1 - Part 2")

        # Case 4: completely empty
        body4 = {"candidates": [{"content": {"parts": []}}]}
        self.assertEqual(extract_text(body4), "")

    def test_try_models_falls_back_when_first_model_returns_empty(self):
        logs = []
        coordinator = GeminiCoordinator(
            models=["model-empty", "model-good"],
            log_fn=lambda msg: logs.append(msg)
        )

        def mock_post(url, *args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.headers = {"content-type": "application/json"}
            mock_resp.status_code = 200
            if "model-empty" in url:
                # Returns 200 with empty parts (like a transcribe model)
                mock_resp.json.return_value = {"candidates": [{"content": {"parts": []}}]}
            else:
                # Returns 200 with valid text
                mock_resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "Valid text from fallback"}]}}]}
            return mock_resp

        with patch("gemini_safe.requests.post", side_effect=mock_post):
            res = coordinator._try_models(
                prompt_text="Hello",
                api_key="test-key",
                json_mode=False,
                response_schema=None,
                temperature=0.7,
                max_output_tokens=100,
                timeout=10,
            )
            self.assertEqual(res.get("kind"), ErrorKind.OK)
            self.assertEqual(res.get("model"), "model-good")
            self.assertEqual(res.get("text"), "Valid text from fallback")
            self.assertTrue(any("phản hồi rỗng" in l and "model-empty" in l for l in logs))


if __name__ == "__main__":
    unittest.main()
