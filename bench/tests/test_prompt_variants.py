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

    def test_default_prompt_hides_the_explicit_int_division_section(self) -> None:
        for variant in ([], [("effect_examples", "mock")]):
            text = self.prompt(variant)
            self.assertNotIn("int.div_floor", text)
            self.assertNotIn("### Explicit Int division", text)
            self.assertIn("## 9. Diagnostics format", text)  # the cut stops at the next section

    def test_int_ops_variant_documents_the_functions(self) -> None:
        text = self.prompt([("int_ops", "explicit")])
        self.assertIn("int.div_floor", text)  # from the variant file
        self.assertIn("int.rem_euclid", text)
        self.assertIn("E0312", text)


if __name__ == "__main__":
    unittest.main()
