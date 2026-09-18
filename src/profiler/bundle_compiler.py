import hashlib
import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from src.core.exceptions import VoiceRewriterError

class BundleVersionExistsError(VoiceRewriterError):
    """Raised when attempting to overwrite an existing immutable bundle version."""
    pass

class CuratedSampleIsolationError(VoiceRewriterError):
    """Raised when a curated sample violates data isolation boundaries."""
    pass

class BundleCompiler:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.profiles_root = self.repo_root / "projects/voice-rewriter/profiles"
        self.corpus_root = self.repo_root / "projects/voice-rewriter/voice_corpus"
        self.schemas_dir = self.repo_root / "schemas"
        self._manifest_schema = None

    @property
    def manifest_schema(self) -> Dict[str, Any]:
        if self._manifest_schema is None:
            schema_path = self.schemas_dir / "bundle_manifest.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._manifest_schema = json.load(f)
        return self._manifest_schema

    def _sha256(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def compile_prompt(
        self,
        voice_profile: Dict[str, Any],
        voice_analysis: Dict[str, Any],
        samples_manifest: Dict[str, Any]
    ) -> str:
        lines = []
        lines.append(f"# Voice Model Prompt Specification: {voice_profile.get('profile_name')}")
        lines.append(f"**Version:** `{voice_profile.get('version')}`\n")
        lines.append("## Voice Character & Summary")
        lines.append(voice_analysis.get("voice_summary", "") + "\n")
        
        lines.append("## Vocabulary Constraints")
        strat = voice_profile.get("vocabulary_stratification", {})
        lines.append(f"* **Characteristic Terms:** {', '.join(strat.get('characteristic_terms', []))}")
        lines.append(f"* **Statistically Unobserved (Use Freely if Relevant):** {', '.join(strat.get('statistically_unobserved_terms', []))}")
        lines.append(f"* **Explicitly Forbidden (Veto Gate):** {', '.join(strat.get('explicitly_forbidden_terms', []))}\n")

        lines.append("## Curated Exemplars")
        for sample in samples_manifest.get("samples", []):
            lines.append(f"### [{sample.get('category').upper()}] {sample.get('rhetorical_intent')}")
            lines.append(f"> \"{sample.get('text')}\"\n")

        return "\n".join(lines)

    def compile_bundle(
        self,
        profile_name: str,
        semver: str,
        raw_metrics: Dict[str, Any],
        voice_analysis: Dict[str, Any],
        voice_profile: Dict[str, Any],
        samples_manifest: Dict[str, Any]
    ) -> Path:
        profile_dir = self.profiles_root / profile_name
        version_dir = profile_dir / "versions" / semver

        # Immutability check: cannot overwrite
        if version_dir.exists():
            raise BundleVersionExistsError(
                f"Bundle version {semver} already exists at {version_dir}. Voice Model Bundles are strictly immutable. Bump SemVer for new versions."
            )

        # Isolation check: verify no sample comes from calibration
        calib_dir = self.corpus_root / "calibration"
        calib_files = {p.name for p in calib_dir.glob("*.txt")} if calib_dir.exists() else set()
        
        for s in samples_manifest.get("samples", []):
            source_file = s.get("source_transcript")
            if source_file in calib_files:
                raise CuratedSampleIsolationError(
                    f"Curated sample {s.get('sample_id')} has provenance in calibration split ({source_file}). Calibration data must NEVER enter training or bundle prompts!"
                )

        version_dir.mkdir(parents=True, exist_ok=True)
        curated_dir = version_dir / "curated_samples"
        curated_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write raw_metrics.json
        raw_metrics_str = json.dumps(raw_metrics, indent=2, ensure_ascii=False)
        (version_dir / "raw_metrics.json").write_text(raw_metrics_str, encoding="utf-8")
        raw_metrics_hash = self._sha256(raw_metrics_str)

        # 2. Write voice_analysis.json
        analysis_str = json.dumps(voice_analysis, indent=2, ensure_ascii=False)
        (version_dir / "voice_analysis.json").write_text(analysis_str, encoding="utf-8")
        analysis_hash = self._sha256(analysis_str)

        # 3. Write voice_profile.yaml
        profile_str = yaml.dump(voice_profile, sort_keys=False, allow_unicode=True)
        (version_dir / "voice_profile.yaml").write_text(profile_str, encoding="utf-8")
        profile_hash = self._sha256(profile_str)

        # 4. Write samples_manifest.json and sample files
        samples_manifest_str = json.dumps(samples_manifest, indent=2, ensure_ascii=False)
        (version_dir / "samples_manifest.json").write_text(samples_manifest_str, encoding="utf-8")
        samples_manifest_hash = self._sha256(samples_manifest_str)

        curated_entries = []
        for s in samples_manifest.get("samples", []):
            s_fn = f"{s['sample_id']}.txt"
            s_text = s.get("text", "")
            (curated_dir / s_fn).write_text(s_text, encoding="utf-8")
            curated_entries.append({
                "sample_id": s["sample_id"],
                "filename": s_fn,
                "sha256": self._sha256(s_text)
            })

        # 5. Compile and write voice_prompt.md
        prompt_str = self.compile_prompt(voice_profile, voice_analysis, samples_manifest)
        (version_dir / "voice_prompt.md").write_text(prompt_str, encoding="utf-8")
        prompt_hash = self._sha256(prompt_str)

        # 6. Build bundle_manifest.json
        now_iso = datetime.now(timezone.utc).isoformat()
        manifest_data = {
            "bundle_version": semver,
            "profile_name": profile_name,
            "created_at": now_iso,
            "hashes": {
                "profile_hash": profile_hash,
                "analysis_hash": analysis_hash,
                "prompt_hash": prompt_hash,
                "samples_manifest_hash": samples_manifest_hash,
                "raw_metrics_hash": raw_metrics_hash
            },
            "curated_samples": curated_entries
        }

        # Validate against schema
        jsonschema.validate(instance=manifest_data, schema=self.manifest_schema)

        (version_dir / "bundle_manifest.json").write_text(
            json.dumps(manifest_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return version_dir
