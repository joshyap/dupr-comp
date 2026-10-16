from pathlib import Path
import unittest

from analysis import (
    DATA_DIR,
    calculate_percentile,
    get_rating_band,
    load_benchmarks,
    load_distribution,
    rating_gap_to_next_benchmark,
    summarize_distribution,
)


class RatingAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.distribution = load_distribution(DATA_DIR / "doubles_distribution.csv")
        cls.benchmarks = load_benchmarks(DATA_DIR / "percentile_benchmarks.csv")

    def test_published_distribution_shares_sum_to_one_hundred(self) -> None:
        self.assertEqual(self.distribution["share_pct"].sum(), 100)

    def test_exact_published_benchmark(self) -> None:
        estimate = calculate_percentile(4.0, self.benchmarks)
        self.assertEqual(estimate.value, 84)

    def test_rating_between_benchmarks_is_linearly_interpolated(self) -> None:
        estimate = calculate_percentile(3.75, self.benchmarks)
        self.assertEqual(estimate.value, 72)
        self.assertEqual((estimate.lower_bound, estimate.upper_bound), (60, 84))

    def test_out_of_benchmark_range_does_not_extrapolate(self) -> None:
        below = calculate_percentile(2.9, self.benchmarks)
        above = calculate_percentile(5.5, self.benchmarks)
        self.assertIsNone(below.value)
        self.assertIsNone(above.value)

    def test_rating_band_edges_are_unambiguous(self) -> None:
        self.assertEqual(get_rating_band(3.5, self.distribution)["label"], "3.500–3.999")
        self.assertEqual(get_rating_band(5.0, self.distribution)["label"], "5.000+")

    def test_next_benchmark_gap(self) -> None:
        self.assertEqual(rating_gap_to_next_benchmark(3.75, self.benchmarks), (4.0, 0.25))
        self.assertIsNone(rating_gap_to_next_benchmark(5.0, self.benchmarks))

    def test_source_summary_statistics(self) -> None:
        summary = summarize_distribution(self.distribution)
        self.assertEqual(summary["share_3s"], 53)
        self.assertEqual(summary["share_4_plus"], 16)


if __name__ == "__main__":
    unittest.main()
