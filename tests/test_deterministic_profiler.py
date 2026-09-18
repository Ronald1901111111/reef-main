import json
import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.profiler.deterministic_profiler import (
    DeterministicProfiler,
    clean_residual_timestamps,
    compute_mtld,
    split_into_sentences,
    tokenize_words,
)

class TestDeterministicProfiler(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        s_dir = self.root / "schemas"
        s_dir.mkdir(parents=True, exist_ok=True)
        for sf in (REPO_ROOT / "schemas").glob("*.json"):
            (s_dir / sf.name).write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

        self.profiler = DeterministicProfiler(repo_root=self.root)

    def test_clean_residual_timestamps(self):
        dirty = "00:01 Olá pessoal, 01:23:45 sejam bem-vindos [00:15] ao nosso vídeo."
        cleaned = clean_residual_timestamps(dirty)
        self.assertNotIn("00:01", cleaned)
        self.assertNotIn("01:23:45", cleaned)
        self.assertIn("Olá pessoal", cleaned)
        self.assertIn("ao nosso vídeo", cleaned)

    def test_sentence_and_word_counts(self):
        text = "Esta e a primeira frase. Aqui temos a segunda frase com mais palavras! E a terceira?"
        sentences = split_into_sentences(text)
        self.assertEqual(len(sentences), 3)
        tokens = tokenize_words(text)
        self.assertEqual(len(tokens), 16)

    def test_mtld_calculation(self):
        # Repetitive text -> low MTLD
        rep_text = ["palavra"] * 50
        mtld_low = compute_mtld(rep_text)
        self.assertLess(mtld_low, 15.0)

        # Diverse text -> higher MTLD
        div_text = [f"termo_{i}" for i in range(50)]
        mtld_high = compute_mtld(div_text)
        self.assertGreater(mtld_high, 30.0)

    def test_full_profiling_and_schema_validation(self):
        train_dir = self.root / "training"
        train_dir.mkdir(parents=True, exist_ok=True)

        doc1 = (
            "Fala pessoal, bem-vindos a este canal de tecnologia. "
            "Hoje vamos analisar a arquitetura de software limpa, passo a passo. "
            "O que acontece quando o sistema cresce muito rapidamente? "
            "Ele precisa de barreiras claras de responsabilidade."
        )
        (train_dir / "doc1.txt").write_text(doc1, encoding="utf-8")

        doc2 = (
            "Neste segundo exemplo, exploramos controle de concorrencia e filas. "
            "Voce ja implementou optimistic concurrency control em producao? "
            "E uma tecnica simples e muito poderosa para evitar locks pesados."
        )
        (train_dir / "doc2.txt").write_text(doc2, encoding="utf-8")

        metrics = self.profiler.analyze_directory(train_dir)
        self.assertEqual(metrics["total_transcripts"], 2)
        self.assertGreater(metrics["total_words"], 40)
        self.assertGreater(metrics["total_sentences"], 4)
        self.assertIn("sentence_length", metrics)
        self.assertIn("mean", metrics["sentence_length"])
        self.assertIn("lexical_metrics", metrics)
        self.assertIn("mtld", metrics["lexical_metrics"])

        # Validate against schema
        self.profiler.validate_metrics(metrics)

if __name__ == "__main__":
    unittest.main()
