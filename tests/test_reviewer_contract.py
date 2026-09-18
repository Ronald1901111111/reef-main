import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.reviewer.reviewer import Reviewer, validate_review_report
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestReviewerContract(unittest.TestCase):
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
        self.reviewer = Reviewer(repo_root=self.root)

        # Setup job up to CI_PASSED -> REVIEW_PENDING
        self.sm.create_job(
            job_id="job_rev_01",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        self.sm.transition_job("job_rev_01", "SEMANTIC_EXTRACTION_PENDING", "semantic_extraction")
        self.sm.transition_job("job_rev_01", "SEMANTIC_EXTRACTION_COMPLETED", "semantic_extraction")
        self.sm.transition_job("job_rev_01", "WRITING_PENDING", "writing")
        self.sm.transition_job("job_rev_01", "CANDIDATE_GENERATED", "writing")
        self.sm.transition_job("job_rev_01", "CI_PENDING", "ci_validation")
        self.sm.transition_job("job_rev_01", "CI_PASSED", "review")
        self.sm.transition_job("job_rev_01", "REVIEW_PENDING", "review")

    def test_review_report_validation_and_enqueuing(self):
        inputs = {
            "candidate_version": "v1",
            "candidate_path": "projects/voice-rewriter/candidates/candidate_job_rev_01_v1.md",
            "iteration": 1
        }
        report_path = self.reviewer.review_candidate(
            job_id="job_rev_01",
            review_inputs=inputs,
            state_manager=self.sm,
            queue_manager=self.qm
        )
        self.assertTrue(report_path.exists())
        text = report_path.read_text(encoding="utf-8")
        self.assertTrue(validate_review_report(text))

        # Check job transitioned to REVIEW_COMPLETED
        job = self.sm.get_job("job_rev_01")
        self.assertEqual(job["status"], "REVIEW_COMPLETED")
        self.assertEqual(job["current_stage"], "evaluation")

        # Check enqueued to evaluation
        pending_eval = self.qm.poll_queue("evaluation")
        self.assertEqual(len(pending_eval), 1)
        self.assertEqual(pending_eval[0]["job_id"], "job_rev_01")

if __name__ == "__main__":
    unittest.main()
