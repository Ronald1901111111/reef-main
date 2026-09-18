import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validator.voice_linter import VoiceLinter

class TestVoiceLinter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.linter = VoiceLinter(repo_root=self.root)
        self.voice_profile = {
            "version": "v2.0.0",
            "vocabulary_stratification": {
                "explicitly_forbidden_terms": ["sinergia", "top"],
                "statistically_unobserved_terms": ["quântico", "metaverso"],
                "characteristic_terms": ["arquitetura"]
            }
        }

    def test_forbidden_term_fails_lint(self):
        bad_text = "Esta arquitetura vai gerar uma grande sinergia na equipe."
        report = self.linter.lint(
            job_id="job_linter_1",
            candidate_text=bad_text,
            candidate_version="v1",
            voice_profile=self.voice_profile
        )
        self.assertEqual(report["status"], "FAILED")
        self.assertTrue(any("sinergia" in v for v in report["violations"]))

    def test_long_sentence_fails_lint(self):
        long_sentence = " ".join(["palavra"] * 26) + "."
        report = self.linter.lint(
            job_id="job_linter_2",
            candidate_text=long_sentence,
            candidate_version="v1",
            voice_profile=self.voice_profile
        )
        self.assertEqual(report["status"], "FAILED")
        self.assertTrue(any("exceeds 24 words" in v for v in report["violations"]))

    def test_statistically_unobserved_term_only_warns_and_passes(self):
        warning_text = "Estamos desenvolvendo um algoritmo quântico simples e direto."
        report = self.linter.lint(
            job_id="job_linter_3",
            candidate_text=warning_text,
            candidate_version="v1",
            voice_profile=self.voice_profile
        )
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(len(report["violations"]), 0)
        self.assertTrue(any("quântico" in w for w in report["warnings"]))

if __name__ == "__main__":
    unittest.main()
