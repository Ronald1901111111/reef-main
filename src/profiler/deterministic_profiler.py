import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema

def clean_residual_timestamps(text: str) -> str:
    cleaned = re.sub(r"\[?\b\d{1,2}:\d{2}(?::\d{2})?\b\]?", " ", text)
    cleaned = re.sub(r"\[Música\]|\[Aplausos\]|<.*?>", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def split_into_sentences(text: str) -> List[str]:
    # Splits by sentence terminators (. ! ?)
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    valid = []
    for s in raw_sentences:
        s_clean = s.strip()
        if len(s_clean) > 1 and any(c.isalnum() for c in s_clean):
            valid.append(s_clean)
    return valid

def tokenize_words(text: str) -> List[str]:
    # Extract lowercased alphabetic/numeric words including accented Portuguese characters
    return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ\-]+\b", text)]

def compute_mtld(tokens: List[str], ttr_threshold: float = 0.72) -> float:
    if len(tokens) < 10:
        return float(len(set(tokens)))

    def _eval_mtld_factor(token_list: List[str]) -> float:
        factors = 0.0
        types = set()
        token_count = 0
        for token in token_list:
            types.add(token)
            token_count += 1
            ttr = len(types) / token_count
            if ttr <= ttr_threshold:
                factors += 1.0
                types = set()
                token_count = 0
        if token_count > 0:
            excess_ttr = len(types) / token_count
            if excess_ttr < 1.0:
                fractional = (1.0 - excess_ttr) / (1.0 - ttr_threshold)
            else:
                fractional = 0.0
            factors += fractional
        return len(token_list) / max(factors, 0.001)

    forward = _eval_mtld_factor(tokens)
    backward = _eval_mtld_factor(list(reversed(tokens)))
    return round((forward + backward) / 2.0, 2)

class DeterministicProfiler:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self._schema = None

    @property
    def schema(self) -> Dict[str, Any]:
        if self._schema is None:
            schema_path = self.schemas_dir / "raw_metrics.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema

    def validate_metrics(self, metrics: Dict[str, Any]) -> None:
        jsonschema.validate(instance=metrics, schema=self.schema)

    def analyze_directory(self, training_dir: Path) -> Dict[str, Any]:
        txt_files = sorted(training_dir.glob("*.txt"))
        if not txt_files:
            return {
                "total_transcripts": 0,
                "total_words": 0,
                "total_sentences": 0,
                "sentence_length": {"mean": 0.0, "std_dev": 0.0, "min": 0, "max": 0, "median": 0.0},
                "punctuation_density": {
                    "commas_per_100_words": 0.0,
                    "periods_per_100_words": 0.0,
                    "question_marks_per_100_words": 0.0,
                    "exclamation_marks_per_100_words": 0.0,
                    "dashes_per_100_words": 0.0,
                    "colons_per_100_words": 0.0,
                },
                "lexical_metrics": {"type_token_ratio": 0.0, "mtld": 0.0, "unique_words": 0},
                "functional_ngrams": {"top_bigrams": [], "top_trigrams": []},
                "fragmentation_rate": 0.0,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        all_sentences = []
        all_tokens = []
        full_raw_text = []

        for p in txt_files:
            raw = p.read_text(encoding="utf-8")
            cleaned = clean_residual_timestamps(raw)
            full_raw_text.append(cleaned)
            sentences = split_into_sentences(cleaned)
            all_sentences.extend(sentences)
            all_tokens.extend(tokenize_words(cleaned))

        combined_text = " ".join(full_raw_text)
        total_words = len(all_tokens)
        total_sentences = len(all_sentences)

        # Sentence length stats
        sentence_lengths = [len(tokenize_words(s)) for s in all_sentences]
        if sentence_lengths:
            s_mean = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((x - s_mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
            s_std = math.sqrt(variance)
            s_min = min(sentence_lengths)
            s_max = max(sentence_lengths)
            sorted_lens = sorted(sentence_lengths)
            mid = len(sorted_lens) // 2
            s_median = float(sorted_lens[mid]) if len(sorted_lens) % 2 != 0 else (sorted_lens[mid-1] + sorted_lens[mid]) / 2.0
            fragmented = sum(1 for sl in sentence_lengths if sl <= 5)
            fragmentation_rate = round(fragmented / len(sentence_lengths), 4)
        else:
            s_mean = s_std = s_median = 0.0
            s_min = s_max = 0
            fragmentation_rate = 0.0

        # Punctuation density per 100 words
        base_factor = (total_words / 100.0) if total_words > 0 else 1.0
        punct_density = {
            "commas_per_100_words": round(combined_text.count(",") / base_factor, 2),
            "periods_per_100_words": round(combined_text.count(".") / base_factor, 2),
            "question_marks_per_100_words": round(combined_text.count("?") / base_factor, 2),
            "exclamation_marks_per_100_words": round(combined_text.count("!") / base_factor, 2),
            "dashes_per_100_words": round((combined_text.count("-") + combined_text.count("—")) / base_factor, 2),
            "colons_per_100_words": round(combined_text.count(":") / base_factor, 2),
        }

        # Lexical metrics
        unique_words = len(set(all_tokens))
        ttr = round(unique_words / total_words, 4) if total_words > 0 else 0.0
        mtld = compute_mtld(all_tokens)

        # Functional n-grams
        bigrams = [f"{all_tokens[i]} {all_tokens[i+1]}" for i in range(len(all_tokens)-1)]
        trigrams = [f"{all_tokens[i]} {all_tokens[i+1]} {all_tokens[i+2]}" for i in range(len(all_tokens)-2)]
        top_bigrams = [list(item) for item in Counter(bigrams).most_common(15)]
        top_trigrams = [list(item) for item in Counter(trigrams).most_common(10)]

        metrics = {
            "total_transcripts": len(txt_files),
            "total_words": total_words,
            "total_sentences": total_sentences,
            "sentence_length": {
                "mean": round(s_mean, 2),
                "std_dev": round(s_std, 2),
                "min": int(s_min),
                "max": int(s_max),
                "median": round(s_median, 2)
            },
            "punctuation_density": punct_density,
            "lexical_metrics": {
                "type_token_ratio": ttr,
                "mtld": mtld,
                "unique_words": unique_words
            },
            "functional_ngrams": {
                "top_bigrams": top_bigrams,
                "top_trigrams": top_trigrams
            },
            "fragmentation_rate": fragmentation_rate,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        self.validate_metrics(metrics)
        return metrics

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deterministic Stylometric Profiler")
    parser.add_argument("--input-dir", required=True, help="Path to training directory")
    parser.add_argument("--output", required=True, help="Path to output raw_metrics.json")
    args = parser.parse_args()

    profiler = DeterministicProfiler()
    metrics = profiler.analyze_directory(Path(args.input_dir))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"Successfully generated metrics at {out_path}")

if __name__ == "__main__":
    main()
