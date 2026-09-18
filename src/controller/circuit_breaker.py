from pathlib import Path
from typing import Dict, Any, Optional
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class PipelineController:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)

    def process_evaluation_decision(
        self,
        job_id: str,
        evaluation_report: Dict[str, Any],
        state_manager: Optional[JobStateManager] = None,
        queue_manager: Optional[QueueManager] = None
    ) -> Dict[str, Any]:
        if state_manager is None:
            state_manager = JobStateManager(repo_root=self.repo_root)
        if queue_manager is None:
            queue_manager = QueueManager(repo_root=self.repo_root)

        job = state_manager.get_job(job_id)
        current_iter = job.get("iteration", 1)
        failure_count = job.get("failure_count", 0)
        recommendation = evaluation_report.get("recommendation")

        frozen_bundle = job["voice_model_bundle_path"]
        frozen_calib = job["calibration_manifest_path"]

        # 1. Circuit Breaker Check: iteration >= 5 or failure_count >= 3
        if current_iter >= 5 or failure_count >= 3:
            state_manager.transition_job(
                job_id=job_id,
                target_status="NEEDS_HUMAN_REVIEW",
                target_stage="human_approval",
                context={
                    "circuit_breaker_tripped": True,
                    "iteration": current_iter,
                    "failure_count": failure_count,
                    "reason": "Max iteration or failure threshold reached"
                }
            )
            return {
                "decision": "NEEDS_HUMAN_REVIEW",
                "circuit_breaker": True,
                "job_id": job_id
            }

        # 2. Recommended for Human Approval
        if recommendation == "PROCEED_TO_HUMAN_APPROVAL":
            state_manager.transition_job(
                job_id=job_id,
                target_status="READY_FOR_HUMAN_APPROVAL",
                target_stage="human_approval",
                context={
                    "composite_score": evaluation_report.get("scores", {}).get("composite_similarity_score"),
                    "recommendation": recommendation
                }
            )
            return {
                "decision": "READY_FOR_HUMAN_APPROVAL",
                "circuit_breaker": False,
                "job_id": job_id
            }

        # 3. Needs Iteration: transition ITERATING -> WRITING_PENDING
        next_iter = current_iter + 1
        state_manager.transition_job(
            job_id=job_id,
            target_status="ITERATING",
            target_stage="writing",
            context={"next_iteration": next_iter},
            iteration_increment=1
        )
        state_manager.transition_job(
            job_id=job_id,
            target_status="WRITING_PENDING",
            target_stage="writing",
            context={"iteration": next_iter}
        )

        # Enqueue in writing queue with evaluator feedback
        envelope = queue_manager.enqueue_job(
            queue_name="writing",
            job_id=job_id,
            authorized_inputs={
                "outline_path": f"projects/voice-rewriter/outlines/outline_{job_id}.json",
                "voice_model_bundle_path": frozen_bundle,
                "iteration": next_iter,
                "feedback_from_evaluation": evaluation_report.get("veto_gates", {})
            },
            iteration=next_iter,
            expected_output_path=f"projects/voice-rewriter/candidates/candidate_{job_id}_v{next_iter}.md"
        )

        # Confirm frozen paths remain intact
        updated_job = state_manager.get_job(job_id)
        assert updated_job["voice_model_bundle_path"] == frozen_bundle
        assert updated_job["calibration_manifest_path"] == frozen_calib

        return {
            "decision": "ITERATING",
            "next_iteration": next_iter,
            "envelope": envelope
        }
