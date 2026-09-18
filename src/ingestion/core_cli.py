from pathlib import Path
from typing import Dict, Any, Optional
from src.ingestion.parsers import parse_file, parse_plain_text
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

def process_ingestion(
    job_id: str,
    raw_content: Optional[str] = None,
    input_file_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    queue_manager: Optional[QueueManager] = None,
    state_manager: Optional[JobStateManager] = None
) -> Dict[str, Any]:
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent
    repo_root = Path(repo_root)

    if queue_manager is None:
        queue_manager = QueueManager(repo_root=repo_root)
    if state_manager is None:
        state_manager = JobStateManager(repo_root=repo_root)

    # Parse content
    if input_file_path:
        normalized_text = parse_file(Path(input_file_path))
    elif raw_content:
        normalized_text = parse_plain_text(raw_content)
    else:
        raise ValueError("Either raw_content or input_file_path must be provided")

    # Persist normalized source to projects/voice-rewriter/source_material/<job_id>/raw_source.txt
    dest_dir = repo_root / "projects/voice-rewriter/source_material" / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    raw_source_path = dest_dir / "raw_source.txt"
    raw_source_path.write_text(normalized_text, encoding="utf-8")

    # Update global state to SEMANTIC_EXTRACTION_PENDING
    state_manager.transition_job(
        job_id=job_id,
        target_status="SEMANTIC_EXTRACTION_PENDING",
        target_stage="semantic_extraction",
        context={"origin": "ingestion_core"},
        global_artifacts_update={
            "raw_source_path": f"projects/voice-rewriter/source_material/{job_id}/raw_source.txt"
        }
    )

    # Enqueue in semantic_extraction queue
    envelope = queue_manager.enqueue_job(
        queue_name="semantic_extraction",
        job_id=job_id,
        authorized_inputs={
            "source_path": f"projects/voice-rewriter/source_material/{job_id}/raw_source.txt",
            "word_count": len(normalized_text.split())
        },
        iteration=1,
        expected_output_path=f"projects/voice-rewriter/outlines/outline_{job_id}.json"
    )

    return {
        "status": "SUCCESS",
        "job_id": job_id,
        "raw_source_path": raw_source_path,
        "queue_envelope": envelope
    }
