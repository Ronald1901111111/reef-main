from pathlib import Path
from typing import Optional, Dict, Any
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager
from src.ingestion.url_adapter import URLAcquisitionAdapter, SubtitleAcquisitionError
from src.ingestion.core_cli import process_ingestion

def process_ingestion_queue_item(
    item: Dict[str, Any],
    repo_root: Path,
    queue_manager: QueueManager,
    state_manager: JobStateManager,
    url_adapter: Optional[URLAcquisitionAdapter] = None,
    worker_id: str = "ingestion_worker"
) -> Dict[str, Any]:
    if url_adapter is None:
        url_adapter = URLAcquisitionAdapter()

    job_id = item["job_id"]
    inputs = item.get("authorized_inputs", {})
    youtube_url = inputs.get("youtube_url")
    raw_content = inputs.get("raw_content")
    input_file = inputs.get("input_file_path")

    # Claim and mark running to have updated revision
    claimed = queue_manager.claim_job(
        queue_name="ingestion",
        job_id=job_id,
        worker_id=worker_id,
        expected_revision=item["queue_revision"]
    )
    running = queue_manager.mark_running(
        queue_name="ingestion",
        job_id=job_id,
        worker_id=worker_id,
        expected_revision=claimed["queue_revision"]
    )
    current_rev = running["queue_revision"]

    # If YouTube URL provided, attempt extraction with fallback
    if youtube_url and not raw_content and not input_file:
        try:
            subtitles = url_adapter.fetch_subtitles(youtube_url)
            if not subtitles:
                raise SubtitleAcquisitionError("Empty subtitle returned")
            raw_content = subtitles
        except SubtitleAcquisitionError as e:
            # Safe fallback: transition global job to WAITING_FOR_TRANSCRIPT if not already
            current_job = state_manager.get_job(job_id)
            if current_job.get("status") != "WAITING_FOR_TRANSCRIPT":
                state_manager.transition_job(
                    job_id=job_id,
                    target_status="WAITING_FOR_TRANSCRIPT",
                    target_stage="ingestion",
                    context={"reason": "youtube_subtitles_unavailable", "error": str(e), "url": youtube_url}
                )
            queue_manager.complete_queue_item(
                queue_name="ingestion",
                job_id=job_id,
                worker_id=worker_id,
                expected_revision=current_rev
            )
            return {
                "job_id": job_id,
                "status": "WAITING_FOR_TRANSCRIPT",
                "message": f"Subtitles unavailable for {youtube_url}. Suspended pending manual transcript."
            }

    # If raw content or file is available, process ingestion core
    result = process_ingestion(
        job_id=job_id,
        raw_content=raw_content,
        input_file_path=Path(input_file) if input_file else None,
        repo_root=repo_root,
        queue_manager=queue_manager,
        state_manager=state_manager
    )
    queue_manager.complete_queue_item(
        queue_name="ingestion",
        job_id=job_id,
        worker_id=worker_id,
        expected_revision=current_rev
    )
    return result

def run_ingestion_cycle(repo_root: Optional[Path] = None, url_adapter: Optional[URLAcquisitionAdapter] = None) -> int:
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent
    repo_root = Path(repo_root)

    qm = QueueManager(repo_root=repo_root)
    sm = JobStateManager(repo_root=repo_root)
    pending = qm.poll_queue("ingestion")
    processed = 0

    for item in pending:
        process_ingestion_queue_item(
            item=item,
            repo_root=repo_root,
            queue_manager=qm,
            state_manager=sm,
            url_adapter=url_adapter
        )
        processed += 1

    return processed
