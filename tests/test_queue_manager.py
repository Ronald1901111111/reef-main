import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.core.exceptions import (
    OptimisticLockError,
    LeaseActiveError,
    SecurityViolationError,
)
from src.core.queue_manager import QueueManager
from src.core.worker_runtime import run_worker_cycle

class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.repo_root = Path(self.tmp_dir.name)
        
        real_schemas = REPO_ROOT / "schemas"
        temp_schemas = self.repo_root / "schemas"
        temp_schemas.mkdir(parents=True, exist_ok=True)
        for s in real_schemas.glob("*.json"):
            (temp_schemas / s.name).write_text(s.read_text(encoding="utf-8"), encoding="utf-8")
            
        self.qm = QueueManager(repo_root=self.repo_root)

    def test_enqueue_and_poll(self):
        envelope = self.qm.enqueue_job(
            queue_name="ingestion",
            job_id="job_001",
            authorized_inputs={"source_type": "text", "raw_text": "Sample text"},
            iteration=1
        )
        self.assertEqual(envelope["job_id"], "job_001")
        self.assertEqual(envelope["claim_status"], "QUEUED")
        self.assertEqual(envelope["queue_name"], "ingestion")
        self.assertIsNotNone(envelope["queue_revision"])

        pending = self.qm.poll_queue("ingestion")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["job_id"], "job_001")

    def test_occ_concurrency_conflict(self):
        env = self.qm.enqueue_job(
            queue_name="semantic_extraction",
            job_id="job_002",
            authorized_inputs={"clean_text": "Clean source"},
            iteration=1
        )
        rev = env["queue_revision"]

        claimed = self.qm.claim_job(
            queue_name="semantic_extraction",
            job_id="job_002",
            worker_id="worker_A",
            expected_revision=rev
        )
        self.assertEqual(claimed["claim_status"], "CLAIMED")
        self.assertEqual(claimed["claim_owner"], "worker_A")
        self.assertNotEqual(claimed["queue_revision"], rev)

        with self.assertRaises(OptimisticLockError):
            self.qm.claim_job(
                queue_name="semantic_extraction",
                job_id="job_002",
                worker_id="worker_B",
                expected_revision=rev
            )

    def test_lease_expiration_and_reclaim(self):
        env = self.qm.enqueue_job(
            queue_name="evaluation",
            job_id="job_003",
            authorized_inputs={"candidate_path": "c1.md"},
            iteration=1
        )
        claimed = self.qm.claim_job(
            queue_name="evaluation",
            job_id="job_003",
            worker_id="worker_stale",
            expected_revision=env["queue_revision"],
            lease_duration_seconds=-60
        )
        self.assertEqual(claimed["claim_owner"], "worker_stale")

        pending = self.qm.poll_queue("evaluation")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["job_id"], "job_003")

        reclaimed = self.qm.claim_job(
            queue_name="evaluation",
            job_id="job_003",
            worker_id="worker_fresh",
            expected_revision=claimed["queue_revision"],
            lease_duration_seconds=300
        )
        self.assertEqual(reclaimed["claim_owner"], "worker_fresh")
        self.assertEqual(reclaimed["claim_status"], "CLAIMED")
        self.assertEqual(reclaimed["attempt"], 2)

    def test_writing_queue_least_privilege_sanitization(self):
        dirty_inputs = {
            "outline_path": "outlines/outline_001.json",
            "voice_model_bundle_path": "profiles/v2.0.0/",
            "source_path": "source_material/raw.txt",
            "raw_source": "This is raw transcript text",
            "url": "https://youtube.com/watch?v=123"
        }
        env = self.qm.enqueue_job(
            queue_name="writing",
            job_id="job_004",
            authorized_inputs=dirty_inputs,
            iteration=1
        )
        inputs = env["authorized_inputs"]
        self.assertNotIn("source_path", inputs)
        self.assertNotIn("raw_source", inputs)
        self.assertNotIn("url", inputs)
        self.assertIn("outline_path", inputs)
        self.assertIn("voice_model_bundle_path", inputs)

    def test_worker_runtime_single_cycle(self):
        self.qm.enqueue_job(
            queue_name="ingestion",
            job_id="job_005",
            authorized_inputs={"raw": "text"},
            iteration=1
        )
        
        executed = []
        def dummy_executor(inputs, context):
            executed.append(inputs)
            return {"status": "SUCCESS", "clean_text": "processed"}

        result = run_worker_cycle(
            worker_id="ingest_worker_1",
            queue_name="ingestion",
            stage_executor=dummy_executor,
            queue_manager=self.qm
        )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(len(executed), 1)

        pending = self.qm.poll_queue("ingestion")
        self.assertEqual(len(pending), 0)

        result_idle = run_worker_cycle(
            worker_id="ingest_worker_1",
            queue_name="ingestion",
            stage_executor=dummy_executor,
            queue_manager=self.qm
        )
        self.assertEqual(result_idle["status"], "IDLE")

    def test_reclaim_active_lease_raises_lease_active_error(self):
        env = self.qm.enqueue_job(
            queue_name="review",
            job_id="job_active_lease",
            authorized_inputs={"candidate": "text"},
            iteration=1
        )
        claimed = self.qm.claim_job(
            queue_name="review",
            job_id="job_active_lease",
            worker_id="worker_active",
            expected_revision=env["queue_revision"],
            lease_duration_seconds=600
        )
        with self.assertRaises(LeaseActiveError):
            self.qm.claim_job(
                queue_name="review",
                job_id="job_active_lease",
                worker_id="worker_intruder",
                expected_revision=claimed["queue_revision"]
            )

    def test_fail_queue_item_records_error_message(self):
        env = self.qm.enqueue_job(
            queue_name="controller",
            job_id="job_fail_test",
            authorized_inputs={"param": "value"},
            iteration=1
        )
        failed = self.qm.fail_queue_item(
            queue_name="controller",
            job_id="job_fail_test",
            worker_id="worker_c",
            expected_revision=env["queue_revision"],
            error_message="Test failure reason"
        )
        self.assertEqual(failed["claim_status"], "FAILED")
        self.assertEqual(failed["error_message"], "Test failure reason")

    def test_worker_runtime_handles_failure(self):
        self.qm.enqueue_job(
            queue_name="semantic_extraction",
            job_id="job_worker_fail",
            authorized_inputs={"raw": "bad data"},
            iteration=1
        )
        def failing_executor(inputs, context):
            raise RuntimeError("Stage failed deliberately")

        res = run_worker_cycle(
            worker_id="worker_fail_runner",
            queue_name="semantic_extraction",
            stage_executor=failing_executor,
            queue_manager=self.qm
        )
        self.assertEqual(res["status"], "FAILED")
        self.assertIn("Stage failed deliberately", res["error"])

if __name__ == "__main__":
    unittest.main()
