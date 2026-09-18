import json
import tempfile
import unittest
from pathlib import Path
import sys
import yaml

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.profiler.cognitive_profiler import (
    stratify_vocabulary,
    validate_voice_profile,
    validate_voice_analysis,
    validate_curated_samples_manifest,
)

class TestCognitiveProfilerContracts(unittest.TestCase):
    def test_vocabulary_stratification_rules(self):
        corpus_tokens = ["arquitetura", "software", "limpa", "robusta", "software", "software", "sistema"]
        dictionary = {"arquitetura", "software", "limpa", "robusta", "sistema", "inusitado", "top"}
        overrides = ["top"]

        stratified = stratify_vocabulary(corpus_tokens, overrides, dictionary)
        self.assertIn("software", stratified["characteristic_terms"])
        self.assertIn("inusitado", stratified["statistically_unobserved_terms"])
        self.assertNotIn("inusitado", stratified["explicitly_forbidden_terms"])
        self.assertIn("top", stratified["explicitly_forbidden_terms"])

    def test_voice_analysis_schema_compliance(self):
        schema_path = REPO_ROOT / "schemas" / "voice_analysis.schema.json"
        valid_analysis = {
            "analysis_summary": "Estilo direto e técnico.",
            "rhetorical_devices": [
                {
                    "pattern": "Abertura com pergunta reflexiva",
                    "confidence": 0.95,
                    "supporting_transcripts": ["video_01.txt"]
                }
            ],
            "syntactic_tendencies": {},
            "discourse_markers": {}
        }
        validate_voice_analysis(valid_analysis, schema_path)

    def test_curated_samples_manifest_schema_compliance(self):
        schema_path = REPO_ROOT / "schemas" / "curated_samples_manifest.schema.json"
        valid_manifest = {
            "samples": [
                {
                    "sample_id": "sample_001",
                    "category": "hook",
                    "rhetorical_purpose": "Engajamento rápido",
                    "confidence": 0.98,
                    "provenance": {
                        "source_file": "video_01.txt",
                        "split": "training"
                    }
                }
            ]
        }
        validate_curated_samples_manifest(valid_manifest, schema_path)

        # Rejection of non-training provenance
        invalid_manifest = {
            "samples": [
                {
                    "sample_id": "sample_002",
                    "category": "cta",
                    "rhetorical_purpose": "Encerramento",
                    "confidence": 0.90,
                    "provenance": {
                        "source_file": "test_calib.txt",
                        "split": "calibration"
                    }
                }
            ]
        }
        with self.assertRaises(ValueError):
            validate_curated_samples_manifest(invalid_manifest, schema_path)

if __name__ == "__main__":
    unittest.main()
