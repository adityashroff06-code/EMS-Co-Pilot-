import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ems_copilot.assistant import answer_question, create_client


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.client.embeddings.create.return_value.data = [SimpleNamespace(embedding=[0.1, 0.2])]
        self.client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="Review the load schedule [guide.pdf, page 2]."))],
            model="test-model",
        )
        self.collection = Mock()
        self.collection.metadata = {"embedding_model": "test-embedding-model"}
        self.collection.count.return_value = 1
        self.collection.query.return_value = {
            "documents": [["Source evidence"]],
            "metadatas": [[{"source": "guide.pdf", "page": 2, "chunk": 0}]],
        }
        self.snapshot = {key: {} for key in ("period", "kpis", "data_quality", "top_peaks", "load_types", "previous_period", "carbon_basis")}

    def test_grounded_answer_preserves_source_and_caps_retrieval(self):
        result = answer_question("What should we investigate?", self.snapshot, self.collection, client=self.client)
        self.assertTrue(result["review_required"])
        self.assertEqual(result["sources"][0]["page"], 2)
        self.assertEqual(self.collection.query.call_args.kwargs["n_results"], 1)
        self.assertEqual(self.client.embeddings.create.call_args.kwargs["model"], "test-embedding-model")
        kwargs = self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["max_completion_tokens"], 1800)
        self.assertIn("Source evidence", kwargs["messages"][1]["content"])

    def test_incomplete_or_empty_provider_answer_is_rejected(self):
        cases = [[], [SimpleNamespace(finish_reason="length", message=SimpleNamespace(content="partial"))],
                 [SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=None))]]
        for choices in cases:
            self.client.chat.completions.create.return_value.choices = choices
            with self.subTest(choices=choices), self.assertRaises(ValueError):
                answer_question("Question", self.snapshot, self.collection, client=self.client)

    def test_blank_question_and_empty_index_do_not_call_provider(self):
        with self.assertRaises(ValueError):
            answer_question(" ", self.snapshot, self.collection, client=self.client)
        self.collection.count.return_value = 0
        with self.assertRaises(ValueError):
            answer_question("Question", self.snapshot, self.collection, client=self.client)
        self.client.embeddings.create.assert_not_called()

    def test_missing_key_fails_before_sdk_import(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}), self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            create_client()


if __name__ == "__main__":
    unittest.main()
