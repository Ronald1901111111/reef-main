import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.validator.ci_router import CIRouter
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestCIRouter(unittest.TestCase):
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
        self.router = CIRouter(repo_root=self.root)

    def _create_job_in_ci_pending(self, job_id):
        self.sm.create_job(
            job_id=job_id,
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        self.sm.transition_job(job_id, "SEMANTIC_EXTRACTION_PENDING", "semantic_extraction")
        self.sm.transition_job(job_id, "SEMANTIC_EXTRACTION_COMPLETED", "semantic_extraction")
        self.sm.transition_job(job_id, "WRITING_PENDING", "writing")
        self.sm.transition_job(job_id, "CANDIDATE_GENERATED", "writing")
        self.sm.transition_job(job_id, "CI_PENDING", "ci_validation")

    def test_routing_passed_ci_to_review(self):
        self._create_job_in_ci_pending("job_pass")
        report = {
            "job_id": "job_pass",
            "candidate_version": "v1",
            "voice_model_version": "v2.0.0",
            "status": "PASSED",
            "violations": [],
            "warnings": [],
            "metrics": {"max_sentence_length": 15, "long_sentences_count": 0},
            "generated_at": "2026-09-18T10:00:00Z"
        }
        res = self.router.route_lint_result("job_pass", report, self.sm, self.qm)
        self.assertEqual(res["routed_to"], "review")

        job = self.sm.get_job("job_pass")
        self.assertEqual(job["status"], "CI_PASSED")
        self.assertEqual(job["current_stage"], "review")

        pending_rev = self.qm.poll_queue("review")
        self.assertEqual(len(pending_rev), 1)
        self.assertEqual(pending_rev[0]["job_id"], "job_pass")

    def test_routing_failed_ci_to_controller(self):
        self._create_job_in_ci_pending("job_fail")
        report = {
            "job_id": "job_fail",
            "candidate_version": "v1",
            "voice_model_version": "v2.0.0",
            "status": "FAILED",
            "violations": ["Sentence exceeds 24 words"],
            "warnings": [],
            "metrics": {"max_sentence_length": 30, "long_sentences_count": 1},
            "generated_at": "2026-09-18T10:00:00Z"
        }
        res = self.router.route_lint_result("job_fail", report, self.sm, self.qm)
        self.assertEqual(res["routed_to"], "controller")

        job = self.sm.get_job("job_fail")
        self.assertEqual(job["status"], "CI_FAILED")
        self.assertEqual(job["current_stage"], "controller")

        pending_ctrl = self.qm.poll_queue("controller")
        self.assertEqual(len(pending_ctrl), 1)
        self.assertEqual(pending_ctrl[0]["job_id"], "job_fail")

if __name__ == "__main__":
    unittest.main()
