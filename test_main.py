import unittest

from main import (
    format_completed_request,
    get_layers,
    get_message,
    get_next_improvement,
)


class TestMain(unittest.TestCase):
    def test_get_message(self):
        self.assertEqual(get_message(), "Conductor is running")

    def test_lifecycle_has_learning_layer(self):
        self.assertEqual(len(get_layers()), 8)
        self.assertEqual(get_layers()[-1], "Delivery and learning feedback")

    def test_next_improvement_prioritizes_failing_tests(self):
        self.assertEqual(
            get_next_improvement(tests_passed=False),
            "Fix failing tests before adding features.",
        )

    def test_next_improvement_uses_review_notes(self):
        self.assertEqual(
            get_next_improvement(review_notes="Simplify this."),
            "Apply review notes in the next refinement.",
        )

    def test_format_completed_request(self):
        self.assertEqual(
            format_completed_request(4, "Code", "Create CLI", "Done"),
            '4. <span style="color: green;">[Code]</span> Create CLI: Done',
        )


if __name__ == "__main__":
    unittest.main()
