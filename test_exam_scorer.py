import unittest
from unittest.mock import patch
import json
import exam_scorer
from exam_scorer import score_urgency, calculate_fallback_urgency, URGENCY_SYSTEM_PROMPT


class TestExamScorer(unittest.TestCase):

    def setUp(self):
        self.sample_exams = [
            {"subject": "DSA", "days_left": 6, "confidence": 2},
            {"subject": "Linear Algebra", "days_left": 1, "confidence": 1},
            {"subject": "Computer Networks", "days_left": 20, "confidence": 5},
        ]

    def test_prompt_content(self):
        self.assertIn("academic risk analyst", URGENCY_SYSTEM_PROMPT)
        self.assertIn("Fewer days left + lower confidence = higher urgency", URGENCY_SYSTEM_PROMPT)
        self.assertIn("urgency_score", URGENCY_SYSTEM_PROMPT)

    def test_empty_exams(self):
        res = score_urgency([])
        self.assertEqual(res, {"results": []})

    @patch("exam_scorer.ai")
    def test_successful_clean_json(self, mock_ai):
        mock_response = {
            "results": [
                {"subject": "DSA", "urgency_score": 75, "reason": "6 days left and 2/5 confidence means high risk."},
                {"subject": "Linear Algebra", "urgency_score": 98, "reason": "1 day left and 1/5 confidence is critical."},
                {"subject": "Computer Networks", "urgency_score": 10, "reason": "20 days left with 5/5 confidence is safe."}
            ]
        }
        mock_ai.return_value = json.dumps(mock_response)
        
        result = score_urgency(self.sample_exams)
        self.assertEqual(result, mock_response)
        mock_ai.assert_called_once()

    @patch("exam_scorer.ai")
    def test_markdown_wrapped_json(self, mock_ai):
        raw_llm_text = """```json
{
  "results": [
    {"subject": "DSA", "urgency_score": 70, "reason": "6 days left with low confidence 2 requires urgent study."}
  ]
}
```"""
        mock_ai.return_value = raw_llm_text

        result = score_urgency([{"subject": "DSA", "days_left": 6, "confidence": 2}])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["urgency_score"], 70)
        self.assertEqual(result["results"][0]["subject"], "DSA")

    @patch("exam_scorer.ai")
    def test_ai_returns_dict_directly(self, mock_ai):
        mock_dict = {
            "results": [
                {"subject": "DSA", "urgency_score": 72, "reason": "6 days and confidence 2."}
            ]
        }
        mock_ai.return_value = mock_dict
        result = score_urgency([{"subject": "DSA", "days_left": 6, "confidence": 2}])
        self.assertEqual(result, mock_dict)

    @patch("exam_scorer.ai")
    def test_ai_failure_with_fallback(self, mock_ai):
        mock_ai.return_value = "AI temporarily unavailable. All API keys failed."
        result = score_urgency(self.sample_exams, fallback_on_error=True)
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 3)
        
        # Verify schema
        for item in result["results"]:
            self.assertIn("subject", item)
            self.assertIn("urgency_score", item)
            self.assertIn("reason", item)
            self.assertGreaterEqual(item["urgency_score"], 0)
            self.assertLessEqual(item["urgency_score"], 100)

        # Verify ordering of urgency: Linear Algebra (1d, conf 1) > DSA (6d, conf 2) > Networks (20d, conf 5)
        la_score = [i["urgency_score"] for i in result["results"] if i["subject"] == "Linear Algebra"][0]
        dsa_score = [i["urgency_score"] for i in result["results"] if i["subject"] == "DSA"][0]
        cn_score = [i["urgency_score"] for i in result["results"] if i["subject"] == "Computer Networks"][0]
        
        self.assertGreater(la_score, dsa_score)
        self.assertGreater(dsa_score, cn_score)

    @patch("exam_scorer.ai")
    def test_ai_failure_without_fallback_raises(self, mock_ai):
        mock_ai.return_value = "AI temporarily unavailable. All API keys failed."
        with self.assertRaises(ValueError):
            score_urgency(self.sample_exams, fallback_on_error=False)

    def test_fallback_extremes(self):
        # Most urgent: 0 days left, confidence 1
        most_urgent = calculate_fallback_urgency([{"subject": "Finals", "days_left": 0, "confidence": 1}])
        self.assertEqual(most_urgent["results"][0]["urgency_score"], 100)
        self.assertIn("today", most_urgent["results"][0]["reason"])
        self.assertIn("1/5", most_urgent["results"][0]["reason"])

        # Least urgent: 30 days left, confidence 5
        least_urgent = calculate_fallback_urgency([{"subject": "Elective", "days_left": 30, "confidence": 5}])
        self.assertLessEqual(least_urgent["results"][0]["urgency_score"], 10)
        self.assertIn("30 days", least_urgent["results"][0]["reason"])
        self.assertIn("5/5", least_urgent["results"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
