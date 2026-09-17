import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.core.exceptions import IllegalStateTransitionError
from src.core.state_machine import (
    JobState,
    QueueState,
    can_transition_job,
    assert_transition_job,
    can_transition_queue,
    assert_transition_queue,
    get_valid_next_job_states,
    get_valid_next_queue_states,
)

class TestStateMachine(unittest.TestCase):
    def test_job_and_queue_states_are_disjoint_except_failed(self):
        job_state_values = set(s.value for s in JobState)
        queue_state_values = set(s.value for s in QueueState)
        self.assertEqual(len(job_state_values), 18)
        self.assertEqual(len(queue_state_values), 5)
        # Only FAILED is shared as a terminal failure concept, other states are strictly disjoint
        intersection = job_state_values.intersection(queue_state_values)
        self.assertEqual(intersection, {"FAILED"})
        self.assertNotIn("QUEUED", job_state_values)
        self.assertNotIn("CLAIMED", job_state_values)
        self.assertNotIn("RUNNING", job_state_values)
        self.assertNotIn("COMPLETED", job_state_values)

    def test_valid_job_lifecycle_transitions(self):
        valid_pairs = [
            ("WAITING_FOR_TRANSCRIPT", "SEMANTIC_EXTRACTION_PENDING"),
            ("SEMANTIC_EXTRACTION_PENDING", "SEMANTIC_EXTRACTION_COMPLETED"),
            ("SEMANTIC_EXTRACTION_COMPLETED", "WRITING_PENDING"),
            ("WRITING_PENDING", "CANDIDATE_GENERATED"),
            ("CANDIDATE_GENERATED", "CI_PENDING"),
            ("CI_PENDING", "CI_PASSED"),
            ("CI_PENDING", "CI_FAILED"),
            ("CI_PASSED", "REVIEW_PENDING"),
            ("CI_FAILED", "ITERATING"),
            ("CI_FAILED", "NEEDS_HUMAN_REVIEW"),
            ("REVIEW_PENDING", "REVIEW_COMPLETED"),
            ("REVIEW_COMPLETED", "EVALUATION_PENDING"),
            ("EVALUATION_PENDING", "EVALUATED"),
            ("EVALUATED", "ITERATING"),
            ("EVALUATED", "READY_FOR_HUMAN_APPROVAL"),
            ("EVALUATED", "NEEDS_HUMAN_REVIEW"),
            ("ITERATING", "WRITING_PENDING"),
            ("READY_FOR_HUMAN_APPROVAL", "APPROVED_BY_HUMAN"),
            ("APPROVED_BY_HUMAN", "PROMOTED"),
        ]
        for src, dst in valid_pairs:
            self.assertTrue(
                can_transition_job(src, dst),
                f"Transition {src} -> {dst} should be valid"
            )
            assert_transition_job(src, dst, context={"job_id": "test_01"})

    def test_invalid_job_lifecycle_transitions_fail(self):
        invalid_pairs = [
            ("CI_PENDING", "PROMOTED"),
            ("WAITING_FOR_TRANSCRIPT", "PROMOTED"),
            ("WRITING_PENDING", "APPROVED_BY_HUMAN"),
            ("PROMOTED", "WRITING_PENDING"), # Terminal state
            ("FAILED", "WRITING_PENDING"), # Terminal state
            ("QUEUED", "RUNNING"), # Mixing queue state into job state
        ]
        for src, dst in invalid_pairs:
            self.assertFalse(
                can_transition_job(src, dst),
                f"Transition {src} -> {dst} should be invalid"
            )
            with self.assertRaises(IllegalStateTransitionError):
                assert_transition_job(src, dst, context={"job_id": "test_01"})

    def test_valid_queue_lifecycle_transitions(self):
        valid_pairs = [
            ("QUEUED", "CLAIMED"),
            ("CLAIMED", "RUNNING"),
            ("RUNNING", "COMPLETED"),
            ("RUNNING", "FAILED"),
            ("CLAIMED", "QUEUED"), # Reclaim / lease expire
            ("FAILED", "QUEUED"),  # Retry
        ]
        for src, dst in valid_pairs:
            self.assertTrue(can_transition_queue(src, dst))
            assert_transition_queue(src, dst)

    def test_invalid_queue_lifecycle_transitions_fail(self):
        invalid_pairs = [
            ("QUEUED", "COMPLETED"), # Skipping claimed and running
            ("COMPLETED", "RUNNING"), # Terminal
            ("QUEUED", "WRITING_PENDING"), # Mixing job state into queue state
        ]
        for src, dst in invalid_pairs:
            self.assertFalse(can_transition_queue(src, dst))
            with self.assertRaises(IllegalStateTransitionError):
                assert_transition_queue(src, dst)

    def test_promoted_is_terminal_success_state(self):
        self.assertEqual(len(get_valid_next_job_states("PROMOTED")), 0)

    def test_job_state_manager_persistence_and_transition(self):
        import tempfile
        from src.core.state_machine import JobStateManager

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        t_root = Path(tmp.name)
        
        s_dir = t_root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        mgr = JobStateManager(repo_root=t_root)
        job = mgr.create_job(
            job_id="job_sm_01",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json",
            initial_status="WAITING_FOR_TRANSCRIPT",
            initial_stage="ingestion"
        )
        self.assertEqual(job["status"], "WAITING_FOR_TRANSCRIPT")

        updated = mgr.transition_job(
            job_id="job_sm_01",
            target_status="SEMANTIC_EXTRACTION_PENDING",
            target_stage="semantic_extraction"
        )
        self.assertEqual(updated["status"], "SEMANTIC_EXTRACTION_PENDING")
        self.assertEqual(updated["current_stage"], "semantic_extraction")

        with self.assertRaises(IllegalStateTransitionError):
            mgr.transition_job(job_id="job_sm_01", target_status="PROMOTED")

if __name__ == "__main__":
    unittest.main()
