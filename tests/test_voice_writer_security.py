import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.writer.writer import VoiceWriter, validate_production_candidate
from src.core.exceptions import SecurityViolationError
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestVoiceWriterSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.qm = QueueManager(repo_root=self.root)
        self.sm = JobStateManager(repo_root=self.root)
        self.writer = VoiceWriter(repo_root=self.root)

        # Create base job
        self.sm.create_job(
            job_id="job_writer_test",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        # Advance state to WRITING_PENDING
        self.sm.transition_job("job_writer_test", "SEMANTIC_EXTRACTION_PENDING", "semantic_extraction")
        self.sm.transition_job("job_writer_test", "SEMANTIC_EXTRACTION_COMPLETED", "semantic_extraction")
        self.sm.transition_job("job_writer_test", "WRITING_PENDING", "writing")

    def test_security_violation_when_source_material_leaks(self):
        toxic_inputs = {
            "job_id": "job_writer_test",
            "outline_path": "outlines/outline_01.json",
            "source_material_path": "projects/voice-rewriter/source_material/job_01/raw_source.txt"
        }
        with self.assertRaises(SecurityViolationError):
            self.writer.write_candidate(
                job_id="job_writer_test",
                writing_inputs=toxic_inputs,
                state_manager=self.sm,
                queue_manager=self.qm
            )

    def test_successful_writing_produces_production_blocks_and_transitions(self):
        valid_inputs = {
            "job_id": "job_writer_test",
            "outline_path": "projects/voice-rewriter/outlines/outline_01.json",
            "voice_model_bundle_path": "projects/voice-rewriter/profiles/ronald_ferrari/versions/v2.0.0/",
            "iteration": 1
        }
        cand_path = self.writer.write_candidate(
            job_id="job_writer_test",
            writing_inputs=valid_inputs,
            state_manager=self.sm,
            queue_manager=self.qm
        )
        self.assertTrue(cand_path.exists())
        content = cand_path.read_text(encoding="utf-8")
        self.assertTrue(validate_production_candidate(content))

        # Check job transitioned to CI_PENDING
        job = self.sm.get_job("job_writer_test")
        self.assertEqual(job["status"], "CI_PENDING")

        # Frozen paths must remain intact
        self.assertEqual(job["voice_model_bundle_path"], "profiles/ronald_ferrari/versions/v2.0.0/")
        self.assertEqual(job["calibration_manifest_path"], "calibration_manifests/calibration_v1.json")

if __name__ == "__main__":
    unittest.main()
