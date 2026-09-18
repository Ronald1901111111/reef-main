import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.evaluator.evaluator import Evaluator
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestEvaluatorSchema(unittest.TestCase):
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
        self.evaluator = Evaluator(repo_root=self.root)

        # Job setup up to REVIEW_COMPLETED
        self.sm.create_job(
            job_id="job_eval_01",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        self.sm.transition_job("job_eval_01", "SEMANTIC_EXTRACTION_PENDING", "semantic_extraction")
        self.sm.transition_job("job_eval_01", "SEMANTIC_EXTRACTION_COMPLETED", "semantic_extraction")
        self.sm.transition_job("job_eval_01", "WRITING_PENDING", "writing")
        self.sm.transition_job("job_eval_01", "CANDIDATE_GENERATED", "writing")
        self.sm.transition_job("job_eval_01", "CI_PENDING", "ci_validation")
        self.sm.transition_job("job_eval_01", "CI_PASSED", "review")
        self.sm.transition_job("job_eval_01", "REVIEW_PENDING", "review")
        self.sm.transition_job("job_eval_01", "REVIEW_COMPLETED", "evaluation")

    def test_weighted_score_and_schema_validation(self):
        scores = {
            "functional_vocabulary_score": 9.5,
            "syntactic_cadence_score": 9.0,
            "rhetorical_alignment_score": 9.0,
            "factual_fidelity": 10.0,
            "source_style_contamination": 0.5
        }
        report = self.evaluator.evaluate_candidate(
            job_id="job_eval_01",
            candidate_version="v1",
            scores_input=scores,
            state_manager=self.sm,
            queue_manager=self.qm
        )
        self.assertEqual(report["recommendation"], "PROCEED_TO_HUMAN_APPROVAL")
        self.assertTrue(report["veto_gates"]["factual_fidelity_passed"])
        self.assertTrue(report["veto_gates"]["contamination_passed"])
        self.assertGreaterEqual(report["scores"]["composite_similarity_score"], 8.5)

        # Check job transition and enqueue
        job = self.sm.get_job("job_eval_01")
        self.assertEqual(job["status"], "EVALUATED")
        self.assertEqual(job["current_stage"], "controller")

        pending_ctrl = self.qm.poll_queue("controller")
        self.assertEqual(len(pending_ctrl), 1)
        self.assertEqual(pending_ctrl[0]["job_id"], "job_eval_01")

    def test_factual_fidelity_veto_gate_triggers(self):
        scores = {
            "functional_vocabulary_score": 9.5,
            "syntactic_cadence_score": 9.0,
            "rhetorical_alignment_score": 9.0,
            "factual_fidelity": 9.0, # Below 9.5 threshold -> veto!
            "source_style_contamination": 0.5
        }
        report = self.evaluator.evaluate_candidate(
            job_id="job_eval_01",
            candidate_version="v1",
            scores_input=scores,
            state_manager=self.sm,
            queue_manager=self.qm
        )
        self.assertFalse(report["veto_gates"]["factual_fidelity_passed"])
        self.assertEqual(report["recommendation"], "NEEDS_ITERATION")

    def test_contamination_veto_gate_triggers(self):
        scores = {
            "functional_vocabulary_score": 9.5,
            "syntactic_cadence_score": 9.0,
            "rhetorical_alignment_score": 9.0,
            "factual_fidelity": 10.0,
            "source_style_contamination": 3.0 # Above 2.0 threshold -> veto!
        }
        report = self.evaluator.evaluate_candidate(
            job_id="job_eval_01",
            candidate_version="v1",
            scores_input=scores,
            state_manager=self.sm,
            queue_manager=self.qm
        )
        self.assertFalse(report["veto_gates"]["contamination_passed"])
        self.assertEqual(report["recommendation"], "NEEDS_ITERATION")

if __name__ == "__main__":
    unittest.main()
