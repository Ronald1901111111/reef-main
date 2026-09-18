import json
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.profiler.bundle_compiler import (
    BundleCompiler,
    BundleVersionExistsError,
    CuratedSampleIsolationError,
)

class TestBundleCompiler(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        # schemas
        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.compiler = BundleCompiler(repo_root=self.root)
        
        # Setup mock training and calibration dirs
        self.training_dir = self.root / "projects/voice-rewriter/voice_corpus/training"
        self.calibration_dir = self.root / "projects/voice-rewriter/voice_corpus/calibration"
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        
        (self.training_dir / "t1.txt").write_text("Fala pessoal, aqui e o Ronald.", encoding="utf-8")
        (self.calibration_dir / "c1.txt").write_text("Texto de calibração.", encoding="utf-8")

        self.raw_metrics = {
            "total_transcripts": 1,
            "total_words": 6,
            "total_sentences": 1,
            "sentence_length": {"mean": 6.0, "std_dev": 0.0, "min": 6, "max": 6, "median": 6.0},
            "punctuation_density": {"commas_per_100_words": 16.6, "periods_per_100_words": 16.6},
            "lexical_metrics": {"type_token_ratio": 1.0, "mtld": 20.0, "unique_words": 6},
            "functional_ngrams": {"top_bigrams": [], "top_trigrams": []},
            "fragmentation_rate": 0.0,
            "generated_at": "2026-09-17T12:00:00Z"
        }
        self.voice_analysis = {
            "profile_name": "ronald_ferrari",
            "voice_summary": "Direto e técnico.",
            "rhetorical_patterns": {},
            "syntactic_style": {"sentence_cadence": "Curta e assertiva."},
            "generated_at": "2026-09-17T12:00:00Z"
        }
        self.voice_profile = {
            "profile_name": "ronald_ferrari",
            "version": "v1.0.0",
            "vocabulary_stratification": {
                "characteristic_terms": ["arquitetura"],
                "observed_terms": ["arquitetura", "software"],
                "rare_terms": ["software"],
                "statistically_unobserved_terms": [],
                "explicitly_forbidden_terms": ["obsoleto"]
            },
            "stylometric_targets": {"mean_sentence_length": 14.5},
            "generated_at": "2026-09-17T12:00:00Z"
        }
        self.samples_manifest = {
            "version": "v1.0.0",
            "curated_at": "2026-09-17T12:00:00Z",
            "samples": [
                {
                    "sample_id": "hook_01",
                    "category": "hook",
                    "source_transcript": "t1.txt",
                    "text": "Fala pessoal, aqui e o Ronald.",
                    "confidence": 0.99,
                    "rhetorical_intent": "Abertura direta"
                }
            ]
        }

    def test_compile_bundle_success_and_hashes(self):
        bundle_dir = self.compiler.compile_bundle(
            profile_name="ronald_ferrari",
            semver="v2.0.0",
            raw_metrics=self.raw_metrics,
            voice_analysis=self.voice_analysis,
            voice_profile=self.voice_profile,
            samples_manifest=self.samples_manifest
        )
        self.assertTrue(bundle_dir.exists())
        self.assertTrue((bundle_dir / "voice_prompt.md").exists())
        self.assertTrue((bundle_dir / "bundle_manifest.json").exists())

        with open(bundle_dir / "bundle_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["bundle_version"], "v2.0.0")
        self.assertIn("profile_hash", manifest["hashes"])
        self.assertIn("prompt_hash", manifest["hashes"])

    def test_cannot_overwrite_existing_version(self):
        # First compilation
        self.compiler.compile_bundle(
            profile_name="ronald_ferrari",
            semver="v2.0.0",
            raw_metrics=self.raw_metrics,
            voice_analysis=self.voice_analysis,
            voice_profile=self.voice_profile,
            samples_manifest=self.samples_manifest
        )
        # Second compilation with same version must fail
        with self.assertRaises(BundleVersionExistsError):
            self.compiler.compile_bundle(
                profile_name="ronald_ferrari",
                semver="v2.0.0",
                raw_metrics=self.raw_metrics,
                voice_analysis=self.voice_analysis,
                voice_profile=self.voice_profile,
                samples_manifest=self.samples_manifest
            )

    def test_curated_sample_from_calibration_is_rejected(self):
        # Sample pointing to calibration file -> must fail
        bad_manifest = dict(self.samples_manifest)
        bad_manifest["samples"] = [
            {
                "sample_id": "bad_hook",
                "category": "hook",
                "source_transcript": "c1.txt", # from calibration!
                "text": "Texto de calibração.",
                "confidence": 0.99,
                "rhetorical_intent": "Abertura inválida"
            }
        ]
        with self.assertRaises(CuratedSampleIsolationError):
            self.compiler.compile_bundle(
                profile_name="ronald_ferrari",
                semver="v2.0.1",
                raw_metrics=self.raw_metrics,
                voice_analysis=self.voice_analysis,
                voice_profile=self.voice_profile,
                samples_manifest=bad_manifest
            )

if __name__ == "__main__":
    unittest.main()
