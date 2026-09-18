import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from src.core.exceptions import VoiceRewriterError

class CorpusValidationError(VoiceRewriterError):
    """Raised when corpus metadata or content fails validation."""
    pass

class DataLeakageError(VoiceRewriterError):
    """Raised when contamination is detected between training and calibration splits."""
    pass

class CorpusValidator:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.corpus_dir = self.repo_root / "projects/voice-rewriter/voice_corpus"
        self.schemas_dir = self.repo_root / "schemas"
        self._meta_schema = None

    @property
    def meta_schema(self) -> Dict[str, Any]:
        if self._meta_schema is None:
            schema_path = self.schemas_dir / "transcript_metadata.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._meta_schema = json.load(f)
        return self._meta_schema

    def compute_sha256(self, content_or_bytes) -> str:
        if isinstance(content_or_bytes, str):
            data = content_or_bytes.encode("utf-8")
        else:
            data = content_or_bytes
        return hashlib.sha256(data).hexdigest()

    def validate_metadata(self, meta: Dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=meta, schema=self.meta_schema)
        except jsonschema.ValidationError as e:
            raise CorpusValidationError(f"Invalid transcript metadata for {meta.get('transcript_id')}: {e.message}") from e

    def generate_calibration_manifest(
        self,
        version: str = "calibration_v1",
        output_dir: Optional[Path] = None
    ) -> Path:
        calib_dir = self.corpus_dir / "calibration"
        manifest_dir = output_dir or (self.corpus_dir / "calibration_manifests")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"{version}.json"

        files_info = []
        for txt_path in sorted(calib_dir.glob("*.txt")):
            text = txt_path.read_text(encoding="utf-8")
            sha = self.compute_sha256(text)
            words = len(text.split())
            files_info.append({
                "filename": txt_path.name,
                "relative_path": f"projects/voice-rewriter/voice_corpus/calibration/{txt_path.name}",
                "sha256": sha,
                "word_count": words
            })

        now_iso = datetime.now(timezone.utc).isoformat()
        manifest_data = {
            "manifest_version": version,
            "created_at": now_iso,
            "total_files": len(files_info),
            "files": files_info
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        return manifest_path

    def validate_corpus(self) -> Dict[str, Any]:
        train_dir = self.corpus_dir / "training"
        calib_dir = self.corpus_dir / "calibration"
        meta_dir = self.corpus_dir / "metadata"

        train_files = {p.name: p for p in train_dir.glob("*.txt")}
        calib_files = {p.name: p for p in calib_dir.glob("*.txt")}

        # 1. Check filename collision / leakage
        overlap_names = set(train_files.keys()).intersection(set(calib_files.keys()))
        if overlap_names:
            raise DataLeakageError(f"Data leakage detected! Filename overlap between training and calibration: {overlap_names}")

        # 2. Check content hash collision / leakage
        train_hashes = {}
        for name, p in train_files.items():
            h = self.compute_sha256(p.read_text(encoding="utf-8"))
            train_hashes[h] = name

        calib_hashes = {}
        for name, p in calib_files.items():
            h = self.compute_sha256(p.read_text(encoding="utf-8"))
            if h in train_hashes:
                raise DataLeakageError(
                    f"Data leakage detected! Hash {h} present in both training ({train_hashes[h]}) and calibration ({name})"
                )
            calib_hashes[h] = name

        # 3. Check metadata and eligibility
        for name, p in train_files.items():
            transcript_id = p.stem
            meta_path = meta_dir / f"{transcript_id}.json"
            if not meta_path.exists():
                raise CorpusValidationError(f"Missing metadata for training file: {name}")
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.validate_metadata(meta)

            if meta.get("contains_guests") is True:
                raise CorpusValidationError(f"Training transcript {name} contains guests (prohibited for pure voice training)")
            if meta.get("authorship_verified") is not True:
                raise CorpusValidationError(f"Training transcript {name} authorship is not verified")
            if meta.get("speaker_verified") is not True:
                raise CorpusValidationError(f"Training transcript {name} speaker is not verified")
            if meta.get("eligible_for_voice_learning") is not True:
                raise CorpusValidationError(f"Training transcript {name} is marked not eligible for voice learning")
            if meta.get("split") != "training":
                raise CorpusValidationError(f"Training transcript {name} has mismatched split in metadata: {meta.get('split')}")

        for name, p in calib_files.items():
            transcript_id = p.stem
            meta_path = meta_dir / f"{transcript_id}.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                self.validate_metadata(meta)
                if meta.get("split") != "calibration":
                    raise CorpusValidationError(f"Calibration transcript {name} has mismatched split: {meta.get('split')}")

        return {
            "valid": True,
            "training_count": len(train_files),
            "calibration_count": len(calib_files),
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
