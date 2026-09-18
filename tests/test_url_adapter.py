import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.ingestion.url_adapter import (
    URLAcquisitionAdapter,
    SubtitleAcquisitionError,
    extract_video_id,
)
from src.ingestion.worker import process_ingestion_queue_item
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class TestURLAdapter(unittest.TestCase):
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

    def test_extract_video_id(self):
        url1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        url2 = "https://youtu.be/dQw4w9WgXcQ?t=10"
        bad_url = "https://example.com/video"
        self.assertEqual(extract_video_id(url1), "dQw4w9WgXcQ")
        self.assertEqual(extract_video_id(url2), "dQw4w9WgXcQ")
        self.assertIsNone(extract_video_id(bad_url))

    def test_successful_acquisition_and_ingestion(self):
        mock_fetcher = lambda url: "Transcrição capturada com sucesso sobre microsserviços."
        adapter = URLAcquisitionAdapter(fetcher_callable=mock_fetcher)

        self.sm.create_job(
            job_id="job_yt_01",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        item = self.qm.enqueue_job(
            queue_name="ingestion",
            job_id="job_yt_01",
            authorized_inputs={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            iteration=1,
            expected_output_path="source_material/job_yt_01/raw_source.txt"
        )

        res = process_ingestion_queue_item(
            item=item,
            repo_root=self.root,
            queue_manager=self.qm,
            state_manager=self.sm,
            url_adapter=adapter
        )
        self.assertEqual(res["status"], "SUCCESS")
        job = self.sm.get_job("job_yt_01")
        self.assertEqual(job["status"], "SEMANTIC_EXTRACTION_PENDING")

        pending_se = self.qm.poll_queue("semantic_extraction")
        self.assertEqual(len(pending_se), 1)

    def test_failed_acquisition_fallback_to_waiting_for_transcript(self):
        def failing_fetcher(url):
            raise ConnectionError("Network blocked or no captions available")

        adapter = URLAcquisitionAdapter(fetcher_callable=failing_fetcher)

        self.sm.create_job(
            job_id="job_yt_fail",
            voice_model_bundle_path="profiles/ronald_ferrari/versions/v2.0.0/",
            calibration_manifest_path="calibration_manifests/calibration_v1.json"
        )
        item = self.qm.enqueue_job(
            queue_name="ingestion",
            job_id="job_yt_fail",
            authorized_inputs={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            iteration=1,
            expected_output_path="source_material/job_yt_fail/raw_source.txt"
        )

        res = process_ingestion_queue_item(
            item=item,
            repo_root=self.root,
            queue_manager=self.qm,
            state_manager=self.sm,
            url_adapter=adapter
        )
        self.assertEqual(res["status"], "WAITING_FOR_TRANSCRIPT")
        job = self.sm.get_job("job_yt_fail")
        self.assertEqual(job["status"], "WAITING_FOR_TRANSCRIPT")

        # Now simulate manual transcript arrival to resume workflow
        manual_item = self.qm.enqueue_job(
            queue_name="ingestion",
            job_id="job_yt_fail",
            authorized_inputs={"raw_content": "Transcrição manual enviada pelo usuário."},
            iteration=2,
            expected_output_path="source_material/job_yt_fail/raw_source.txt"
        )
        res_resume = process_ingestion_queue_item(
            item=manual_item,
            repo_root=self.root,
            queue_manager=self.qm,
            state_manager=self.sm,
            url_adapter=adapter
        )
        self.assertEqual(res_resume["status"], "SUCCESS")
        job_resumed = self.sm.get_job("job_yt_fail")
        self.assertEqual(job_resumed["status"], "SEMANTIC_EXTRACTION_PENDING")

if __name__ == "__main__":
    unittest.main()
