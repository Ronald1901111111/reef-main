import json
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.controller.circuit_breaker import PipelineController
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestControllerCircuitBreaker(unittest.TestCase):
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
        self.ctrl = PipelineController(repo_root=self.root)

    def _setup_job_to_evaluated(self, job_id, iteration=1, failure_count=0):
        self.sm.create_job(
            job_id=job_id,
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        job_path = self.sm.get_job_path(job_id)
        with open(job_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["iteration"] = iteration
        data["failure_count"] = failure_count
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.sm.transition_job(job_id, "SEMANTIC_EXTRACTION_PENDING", "semantic_extraction")
        self.sm.transition_job(job_id, "SEMANTIC_EXTRACTION_COMPLETED", "semantic_extraction")
        self.sm.transition_job(job_id, "WRITING_PENDING", "writing")
        self.sm.transition_job(job_id, "CANDIDATE_GENERATED", "writing")
        self.sm.transition_job(job_id, "CI_PENDING", "ci_validation")
        self.sm.transition_job(job_id, "CI_PASSED", "review")
        self.sm.transition_job(job_id, "REVIEW_PENDING", "review")
        self.sm.transition_job(job_id, "REVIEW_COMPLETED", "evaluation")
        self.sm.transition_job(job_id, "EVALUATION_PENDING", "evaluation")
        self.sm.transition_job(job_id, "EVALUATED", "controller")

    def test_circuit_breaker_trips_at_max_iterations(self):
        self._setup_job_to_evaluated("job_cb_iter", iteration=5)
        eval_report = {"recommendation": "NEEDS_ITERATION"}
        res = self.ctrl.process_evaluation_decision("job_cb_iter", eval_report, self.sm, self.qm)

        self.assertTrue(res["circuit_breaker"])
        self.assertEqual(res["decision"], "NEEDS_HUMAN_REVIEW")

        job = self.sm.get_job("job_cb_iter")
        self.assertEqual(job["status"], "NEEDS_HUMAN_REVIEW")
        self.assertEqual(job["current_stage"], "human_approval")

    def test_circuit_breaker_trips_at_max_failures(self):
        self._setup_job_to_evaluated("job_cb_fail", iteration=2, failure_count=3)
        eval_report = {"recommendation": "NEEDS_ITERATION"}
        res = self.ctrl.process_evaluation_decision("job_cb_fail", eval_report, self.sm, self.qm)

        self.assertTrue(res["circuit_breaker"])
        self.assertEqual(res["decision"], "NEEDS_HUMAN_REVIEW")

        job = self.sm.get_job("job_cb_fail")
        self.assertEqual(job["status"], "NEEDS_HUMAN_REVIEW")

    def test_advance_to_ready_for_human_approval_on_success(self):
        self._setup_job_to_evaluated("job_pass", iteration=1)
        eval_report = {
            "recommendation": "PROCEED_TO_HUMAN_APPROVAL",
            "scores": {"composite_similarity_score": 9.2}
        }
        res = self.ctrl.process_evaluation_decision("job_pass", eval_report, self.sm, self.qm)

        self.assertFalse(res["circuit_breaker"])
        self.assertEqual(res["decision"], "READY_FOR_HUMAN_APPROVAL")

        job = self.sm.get_job("job_pass")
        self.assertEqual(job["status"], "READY_FOR_HUMAN_APPROVAL")
        self.assertEqual(job["current_stage"], "human_approval")

    def test_iteration_cycle_increments_and_reenqueues(self):
        self._setup_job_to_evaluated("job_iter", iteration=1)
        eval_report = {
            "recommendation": "NEEDS_ITERATION",
            "veto_gates": {"factual_fidelity_passed": True, "contamination_passed": False}
        }
        res = self.ctrl.process_evaluation_decision("job_iter", eval_report, self.sm, self.qm)

        self.assertEqual(res["decision"], "ITERATING")
        self.assertEqual(res["next_iteration"], 2)

        job = self.sm.get_job("job_iter")
        self.assertEqual(job["status"], "WRITING_PENDING")
        self.assertEqual(job["current_stage"], "writing")
        self.assertEqual(job["iteration"], 2)

        # Check enqueued to writing
        pending = self.qm.poll_queue("writing")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["job_id"], "job_iter")
        self.assertEqual(pending[0]["iteration"], 2)

if __name__ == "__main__":
    unittest.main()
