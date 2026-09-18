import json
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.corpus.corpus_validator import (
    CorpusValidator,
    CorpusValidationError,
    DataLeakageError,
)

class TestCorpusIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        
        # Schemas
        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.corpus_dir = self.root / "projects/voice-rewriter/voice_corpus"
        self.train_dir = self.corpus_dir / "training"
        self.calib_dir = self.corpus_dir / "calibration"
        self.meta_dir = self.corpus_dir / "metadata"
        self.manifest_dir = self.corpus_dir / "calibration_manifests"

        for d in [self.train_dir, self.calib_dir, self.meta_dir, self.manifest_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.validator = CorpusValidator(repo_root=self.root)

    def _create_sample_transcript(self, name, text, split, contains_guests=False, authorship=True, speaker=True, eligible=True):
        if split == "training":
            fpath = self.train_dir / f"{name}.txt"
        else:
            fpath = self.calib_dir / f"{name}.txt"
        fpath.write_text(text, encoding="utf-8")
        
        meta = {
            "transcript_id": name,
            "title": f"Video {name}",
            "speaker_verified": speaker,
            "authorship_verified": authorship,
            "contains_guests": contains_guests,
            "eligible_for_voice_learning": eligible,
            "split": split,
            "source_type": "youtube",
            "word_count": len(text.split()),
            "created_at": "2026-09-17T12:00:00Z",
            "sha256": self.validator.compute_sha256(text)
        }
        (self.meta_dir / f"{name}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return fpath, meta

    def test_valid_corpus_passes_validation(self):
        self._create_sample_transcript("t1", "Fala pessoal, aqui e o Ronald com mais um video de engenharia.", "training")
        self._create_sample_transcript("t2", "Hoje vamos explorar arquitetura de software limpa e robusta.", "training")
        self._create_sample_transcript("c1", "Bem-vindos a este episodio especial de calibração.", "calibration")
        
        manifest_path = self.validator.generate_calibration_manifest(version="calibration_v1")
        self.assertTrue(manifest_path.exists())

        report = self.validator.validate_corpus()
        self.assertTrue(report["valid"])
        self.assertEqual(report["training_count"], 2)
        self.assertEqual(report["calibration_count"], 1)

    def test_rejection_of_transcripts_with_guests(self):
        self._create_sample_transcript("t_guest", "Entrevista com convidado hoje.", "training", contains_guests=True)
        with self.assertRaises(CorpusValidationError):
            self.validator.validate_corpus()

    def test_rejection_of_unverified_authorship(self):
        self._create_sample_transcript("t_unauth", "Texto de outro criador.", "training", authorship=False)
        with self.assertRaises(CorpusValidationError):
            self.validator.validate_corpus()

    def test_rejection_of_ineligible_for_voice_learning(self):
        self._create_sample_transcript("t_ineligible", "Texto experimental.", "training", eligible=False)
        with self.assertRaises(CorpusValidationError):
            self.validator.validate_corpus()

    def test_detection_and_blocking_of_data_leakage(self):
        # Same content in training and calibration
        shared_text = "Texto duplicado em treino e calibracao."
        self._create_sample_transcript("t_leak", shared_text, "training")
        self._create_sample_transcript("c_leak", shared_text, "calibration")
        
        with self.assertRaises(DataLeakageError):
            self.validator.validate_corpus()

    def test_calibration_manifest_integrity_and_hashes(self):
        self._create_sample_transcript("c1", "Calibracao teste 1.", "calibration")
        self._create_sample_transcript("c2", "Calibracao teste 2.", "calibration")

        manifest_path = self.validator.generate_calibration_manifest(version="calibration_v1")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["manifest_version"], "calibration_v1")
        self.assertEqual(len(manifest["files"]), 2)
        for entry in manifest["files"]:
            self.assertIn("filename", entry)
            self.assertIn("sha256", entry)
            self.assertIn("word_count", entry)

if __name__ == "__main__":
    unittest.main()
