from typing import Callable, Dict, Any, Optional
from src.core.queue_manager import QueueManager

def run_worker_cycle(
    worker_id: str,
    queue_name: str,
    stage_executor: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    queue_manager: QueueManager,
    state_manager: Optional[Any] = None,
    lease_duration_seconds: int = 300
) -> Dict[str, Any]:
    eligible_items = queue_manager.poll_queue(queue_name)
    if not eligible_items:
        return {"status": "IDLE", "message": f"No work in queue {queue_name}"}

    item = eligible_items[0]
    job_id = item["job_id"]
    rev = item["queue_revision"]

    claimed = queue_manager.claim_job(
        queue_name=queue_name,
        job_id=job_id,
        worker_id=worker_id,
        expected_revision=rev,
        lease_duration_seconds=lease_duration_seconds
    )
    rev = claimed["queue_revision"]

    running = queue_manager.mark_running(
        queue_name=queue_name,
        job_id=job_id,
        worker_id=worker_id,
        expected_revision=rev
    )
    rev = running["queue_revision"]
    inputs = running["authorized_inputs"]

    context = {
        "job_id": job_id,
        "run_id": running["run_id"],
        "iteration": running.get("iteration", 1),
        "queue_name": queue_name,
        "worker_id": worker_id,
    }
    
    try:
        execution_output = stage_executor(inputs, context)
        
        if state_manager and "next_state" in execution_output:
            state_manager.transition_job(
                job_id=job_id,
                target_state=execution_output["next_state"],
                context=context
            )
            
        if "next_queue" in execution_output and "next_inputs" in execution_output:
            queue_manager.enqueue_job(
                queue_name=execution_output["next_queue"],
                job_id=job_id,
                authorized_inputs=execution_output["next_inputs"],
                iteration=running.get("iteration", 1),
                expected_output_path=execution_output.get("expected_output_path")
            )

        queue_manager.complete_queue_item(
            queue_name=queue_name,
            job_id=job_id,
            worker_id=worker_id,
            expected_revision=rev
        )
        return {
            "status": "COMPLETED",
            "job_id": job_id,
            "output": execution_output
        }
    except Exception as exc:
        queue_manager.fail_queue_item(
            queue_name=queue_name,
            job_id=job_id,
            worker_id=worker_id,
            expected_revision=rev,
            error_message=str(exc)
        )
        return {
            "status": "FAILED",
            "job_id": job_id,
            "error": str(exc)
        }
