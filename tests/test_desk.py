import json
from pathlib import Path
import tempfile
import unittest

from desk import load_notes, recommend, render


START = Path(__file__).resolve().parents[1] / "data/starting.json"


class DeskTest(unittest.TestCase):
    def test_opening_handoff(self):
        notes = load_notes(START)
        result = recommend(notes)
        pick = result["recommendation"]
        self.assertEqual((pick["person"], pick["location"]), ("Sam", "Novelty"))
        self.assertEqual(pick["evidence"]["skills"]["note"], 4)
        self.assertEqual(pick["evidence"]["availability"]["note"], 7)
        self.assertEqual(result["excluded"][0]["person"], "Kai")
        self.assertIn(notes[6]["text"], render(result, notes))

    def test_assignment_alone_does_not_confirm_availability(self):
        notes = load_notes(START)
        self.assertIsNone(recommend(notes, "13:45")["recommendation"])

    def test_minute_40_changes_the_recommendation_at_the_same_desk_time(self):
        notes = load_notes(START, [START.with_name("minute-40.json")])
        result = recommend(notes)
        pick = result["recommendation"]
        self.assertEqual(result["as_of"], "13:55")
        self.assertEqual((pick["person"], pick["location"]), ("Kai", "Connection"))
        self.assertEqual(pick["evidence"]["skills"]["note"], 4)
        self.assertEqual(pick["evidence"]["availability"]["note"], 9)
        self.assertEqual(pick["evidence"]["location"]["note"], 9)
        self.assertEqual(result["excluded"][0]["person"], "Sam")
        self.assertIn("ask them to help in Novelty now", render(result, notes))

    def test_later_note_overrides_only_fields_it_mentions(self):
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "example.json"
            handoff.write_text(json.dumps({
                "id": 90,
                "at": "13:56",
                "title": "Synthetic test",
                "text": "Kai is free in the test room. Sam is busy.",
                "facts": [
                    {"person": "Kai", "location": "Test room", "availability": "free"},
                    {"person": "Sam", "availability": "busy"},
                ],
            }), encoding="utf-8")
            notes = load_notes(START, [handoff])
        self.assertEqual(recommend(notes)["recommendation"]["person"], "Sam")
        result = recommend(notes, "13:56")
        pick = result["recommendation"]
        self.assertEqual((pick["person"], pick["location"]), ("Kai", "Test room"))
        self.assertEqual(pick["evidence"]["skills"]["note"], 4)
        self.assertEqual(pick["evidence"]["availability"]["note"], 90)
        self.assertEqual(result["excluded"][0]["person"], "Sam")


if __name__ == "__main__":
    unittest.main()
