import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.ingestion.cleaner import clean_subtitles_noise, normalize_whitespace
from src.ingestion.parsers import parse_srt, parse_file
from src.ingestion.core_cli import process_ingestion
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestIngestionCore(unittest.TestCase):
    def test_clean_subtitles_noise_preserves_facts_and_names(self):
        raw = "<i>[Música]</i> Olá, eu sou o Dr. Carlos e temos 42.5% de ganho em 2026. [Aplausos]"
        cleaned = clean_subtitles_noise(raw)
        self.assertNotIn("[Música]", cleaned)
        self.assertNotIn("[Aplausos]", cleaned)
        self.assertNotIn("<i>", cleaned)
        self.assertIn("Dr. Carlos", cleaned)
        self.assertIn("42.5%", cleaned)
        self.assertIn("2026", cleaned)

    def test_parse_srt_format(self):
        srt_content = """1
00:00:01,000 --> 00:00:03,500
[Música]
Bem-vindos ao canal.

2
00:00:04,000 --> 00:00:07,000
Hoje falaremos sobre 3 pilares
fundamentais da computação.
"""
        parsed = parse_srt(srt_content)
        self.assertNotIn("-->", parsed)
        self.assertNotIn("00:00:01", parsed)
        self.assertNotIn("[Música]", parsed)
        self.assertIn("Bem-vindos ao canal.", parsed)
        self.assertIn("3 pilares fundamentais da computação.", parsed)

    def test_process_ingestion_workflow(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        
        # Schemas
        s_dir = root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        # Create job
        sm = JobStateManager(repo_root=root)
        job = sm.create_job(
            job_id="job_ingest_01",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        self.assertEqual(job["status"], "WAITING_FOR_TRANSCRIPT")

        qm = QueueManager(repo_root=root)

        raw_text = "[Música] Transcrição do vídeo sobre inteligência artificial com 98% de precisão."
        result = process_ingestion(
            job_id="job_ingest_01",
            raw_content=raw_text,
            repo_root=root,
            queue_manager=qm,
            state_manager=sm
        )
        self.assertTrue(result["raw_source_path"].exists())
        self.assertIn("98% de precisão", result["raw_source_path"].read_text(encoding="utf-8"))

        # Global job state should now be SEMANTIC_EXTRACTION_PENDING
        updated_job = sm.get_job("job_ingest_01")
        self.assertEqual(updated_job["status"], "SEMANTIC_EXTRACTION_PENDING")
        self.assertEqual(updated_job["current_stage"], "semantic_extraction")

        # Check queue
        pending = qm.poll_queue("semantic_extraction")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["job_id"], "job_ingest_01")

if __name__ == "__main__":
    unittest.main()
