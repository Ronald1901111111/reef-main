import json
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.controller.promoter import (
    ScriptPromoter,
    ApprovalMissingError,
    ApprovalMismatchError,
)
from src.core.state_machine import JobStateManager

class TestPromoter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.sm = JobStateManager(repo_root=self.root)
        self.promoter = ScriptPromoter(repo_root=self.root)

        # Setup job in READY_FOR_HUMAN_APPROVAL
        self.sm.create_job(
            job_id="job_promo_01",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        self.sm.transition_job("job_promo_01", "SEMANTIC_EXTRACTION_PENDING", "semantic_extraction")
        self.sm.transition_job("job_promo_01", "SEMANTIC_EXTRACTION_COMPLETED", "semantic_extraction")
        self.sm.transition_job("job_promo_01", "WRITING_PENDING", "writing")
        self.sm.transition_job("job_promo_01", "CANDIDATE_GENERATED", "writing")
        self.sm.transition_job("job_promo_01", "CI_PENDING", "ci_validation")
        self.sm.transition_job("job_promo_01", "CI_PASSED", "review")
        self.sm.transition_job("job_promo_01", "REVIEW_PENDING", "review")
        self.sm.transition_job("job_promo_01", "REVIEW_COMPLETED", "evaluation")
        self.sm.transition_job("job_promo_01", "EVALUATION_PENDING", "evaluation")
        self.sm.transition_job("job_promo_01", "EVALUATED", "controller")
        self.sm.transition_job("job_promo_01", "READY_FOR_HUMAN_APPROVAL", "human_approval")

        # Create candidate file
        cand_dir = self.root / "projects/voice-rewriter/candidates"
        cand_dir.mkdir(parents=True, exist_ok=True)
        self.cand_path = cand_dir / "candidate_job_promo_01_v1.md"
        self.cand_path.write_text("# Roteiro Final Aprovado", encoding="utf-8")

    def test_promotion_blocked_when_approval_file_missing(self):
        non_existent = self.root / "missing_approval.json"
        with self.assertRaises(ApprovalMissingError):
            self.promoter.promote_candidate(
                job_id="job_promo_01",
                candidate_version="v1",
                candidate_file_path=self.cand_path,
                approval_file_path=non_existent,
                state_manager=self.sm
            )

    def test_promotion_blocked_on_mismatch(self):
        mismatch_approval = {
            "job_id": "job_other", # Mismatch!
            "candidate_version": "v1",
            "approved_by": "Ronald Ferrari",
            "approval_timestamp": "2026-09-18T12:00:00Z",
            "decision": "APPROVED",
            "slug": "arquitetura-software-2026"
        }
        app_path = self.root / "approval_bad.json"
        app_path.write_text(json.dumps(mismatch_approval), encoding="utf-8")

        with self.assertRaises(ApprovalMismatchError):
            self.promoter.promote_candidate(
                job_id="job_promo_01",
                candidate_version="v1",
                candidate_file_path=self.cand_path,
                approval_file_path=app_path,
                state_manager=self.sm
            )

    def test_successful_promotion_transitions_to_promoted(self):
        valid_approval = {
            "job_id": "job_promo_01",
            "candidate_version": "v1",
            "approved_by": "Ronald Ferrari",
            "approval_timestamp": "2026-09-18T12:00:00Z",
            "decision": "APPROVED",
            "slug": "arquitetura-software-2026",
            "notes": "Excelente roteiro, pronto para gravação."
        }
        app_path = self.root / "approval_good.json"
        app_path.write_text(json.dumps(valid_approval), encoding="utf-8")

        dest = self.promoter.promote_candidate(
            job_id="job_promo_01",
            candidate_version="v1",
            candidate_file_path=self.cand_path,
            approval_file_path=app_path,
            state_manager=self.sm
        )
        self.assertTrue(dest.exists())
        self.assertEqual(dest.name, "arquitetura-software-2026.md")

        job = self.sm.get_job("job_promo_01")
        self.assertEqual(job["status"], "PROMOTED")
        self.assertEqual(job["current_stage"], "completed")

if __name__ == "__main__":
    unittest.main()
