"""The default arm's Zehn prompt must not document syntax that only a dialect accepts."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchlib.adapters.zehn import ZehnAdapter  # noqa: E402


class PromptVariantTests(unittest.TestCase):
    def prompt(self, variant):
        a = ZehnAdapter()
        a.set_variant(variant)
        return a.system_prompt({})

    def test_default_prompt_hides_the_mock_syntax(self) -> None:
        text = self.prompt([])
        self.assertNotIn("with console = mock", text)
        self.assertNotIn("### Mocked examples", text)
        self.assertIn("## 8. Standard Library", text)  # the cut stops at the next section

    def test_other_variants_do_not_get_the_mock_syntax(self) -> None:
        self.assertNotIn("with console = mock", self.prompt([("int_ops", "explicit")]))

    def test_mock_variant_documents_it(self) -> None:
        text = self.prompt([("effect_examples", "mock")])
        self.assertIn("### Mocked examples of effectful functions", text)
        self.assertIn("with console = mock", text)


if __name__ == "__main__":
    unittest.main()
