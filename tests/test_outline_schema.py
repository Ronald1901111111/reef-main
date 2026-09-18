import json
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.semantic.extractor import SemanticExtractor, SemanticOutlineValidationError
from src.core.queue_manager import QueueManager

class TestOutlineSchema(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.extractor = SemanticExtractor(repo_root=self.root)
        self.qm = QueueManager(repo_root=self.root)

    def test_valid_outline_conforms_to_schema(self):
        valid_outline = {
            "job_id": "job_123",
            "source_summary": "Discussão sobre arquitetura limpa e microsserviços.",
            "generated_at": "2026-09-18T10:00:00Z",
            "blocks": [
                {
                    "topico": "Separação de responsabilidades",
                    "afirmacao_ou_tese": "Isolar regras de negócio desacopla o sistema de frameworks.",
                    "evidencias_ou_exemplos": ["Caso da migração bancária de 2024", "Redução de 40% em bugs"],
                    "relacao_causal": "Menor acoplamento permite refatoração contínua com risco reduzido.",
                    "ressalvas_ou_contrapontos": ["Aumenta o número de camadas e código boilerplate."]
                }
            ]
        }
        self.extractor.validate_outline(valid_outline)

    def test_missing_causal_relation_fails_validation(self):
        invalid_outline = {
            "job_id": "job_123",
            "source_summary": "Resumo sem relação causal.",
            "generated_at": "2026-09-18T10:00:00Z",
            "blocks": [
                {
                    "topico": "Tópico sem causa",
                    "afirmacao_ou_tese": "Tese simples.",
                    "evidencias_ou_exemplos": [],
                    # missing relacao_causal
                    "ressalvas_ou_contrapontos": []
                }
            ]
        }
        with self.assertRaises(SemanticOutlineValidationError):
            self.extractor.validate_outline(invalid_outline)

    def test_writing_payload_least_privilege_sanitization(self):
        payload = self.extractor.build_writing_payload(
            job_id="job_abc",
            outline_rel_path="projects/voice-rewriter/outlines/outline_job_abc.json",
            voice_model_bundle_path="projects/voice-rewriter/profiles/ronald_ferrari/versions/v2.0.0/",
            iteration=1
        )
        self.assertEqual(payload["job_id"], "job_abc")
        self.assertIn("outline_path", payload)
        self.assertIn("voice_model_bundle_path", payload)
        self.assertNotIn("source_material", payload)
        self.assertNotIn("raw_source", payload)

        # Enqueue in queue_manager writing queue and verify sanitization
        envelope = self.qm.enqueue_job(
            queue_name="writing",
            job_id="job_abc",
            authorized_inputs=payload,
            iteration=1,
            expected_output_path="candidates/candidate_job_abc_iter1.md"
        )
        self.assertNotIn("source_material", envelope["authorized_inputs"])

if __name__ == "__main__":
    unittest.main()
