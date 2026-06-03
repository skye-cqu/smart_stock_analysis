from __future__ import annotations

from unittest.mock import MagicMock

from src.data.models import ScoreResult, StockDailyData, StockInfo
from src.scoring.engine import FiveDimensionScorer


def _make_daily(closes: list[float]) -> list[StockDailyData]:
    return [
        StockDailyData(
            date=f"2026-01-{i + 1:02d}",
            open=c - 0.1,
            high=c + 0.2,
            low=c - 0.2,
            close=c,
            volume=1000,
            amount=c * 1000,
            turnover=1.0,
        )
        for i, c in enumerate(closes)
    ]


def _make_info(pe: float = 15.0, pb: float = 2.0, roe: float = 12.0) -> StockInfo:
    return StockInfo(
        code="000001",
        name="平安银行",
        industry="银行",
        pe_ratio=pe,
        pb_ratio=pb,
        roe=roe,
        market_cap=100.0,
    )


class TestFiveDimensionScorer:
    def test_weighted_total_matches(self):
        scorer = FiveDimensionScorer()
        mock_scores = {
            "technical": 80.0,
            "capital_flow": 60.0,
            "fundamental": 40.0,
            "sector": 20.0,
            "event": 0.0,
        }
        for name, mock_score in mock_scores.items():
            mock = MagicMock()
            mock.score.return_value = mock_score
            scorer.scorers[name] = mock

        result = scorer.score(_make_info(), _make_daily([10.0] * 30))
        expected = 80.0 * 0.30 + 60.0 * 0.30 + 40.0 * 0.15 + 20.0 * 0.15 + 0.0 * 0.10
        assert result.total == expected

    def test_veto_forces_negative_100(self):
        scorer = FiveDimensionScorer()
        for name in scorer.scorers:
            mock = MagicMock()
            mock.score.return_value = 50.0
            scorer.scorers[name] = mock
        scorer.scorers["technical"].score.return_value = -60.0

        result = scorer.score(_make_info(), _make_daily([10.0] * 30))
        assert result.total == -100.0

    def test_exception_in_scorer_defaults_to_zero(self):
        scorer = FiveDimensionScorer()
        for name in scorer.scorers:
            mock = MagicMock()
            mock.score.return_value = 50.0
            scorer.scorers[name] = mock
        scorer.scorers["capital_flow"].score.side_effect = ValueError("boom")

        result = scorer.score(_make_info(), _make_daily([10.0] * 30))
        expected = 50.0 * 0.30 + 0.0 * 0.30 + 50.0 * 0.15 + 50.0 * 0.15 + 50.0 * 0.10
        assert result.total == expected

    def test_all_scorers_zero(self):
        scorer = FiveDimensionScorer()
        for name in scorer.scorers:
            mock = MagicMock()
            mock.score.return_value = 0.0
            scorer.scorers[name] = mock

        result = scorer.score(_make_info(), _make_daily([10.0] * 30))
        assert result.total == 0.0

    def test_score_returns_score_result(self):
        scorer = FiveDimensionScorer()
        result = scorer.score(_make_info(), _make_daily([10.0] * 30))
        assert isinstance(result, ScoreResult)

    def test_dimensions_populated(self):
        scorer = FiveDimensionScorer()
        for name in scorer.scorers:
            mock = MagicMock()
            mock.score.return_value = 10.0
            scorer.scorers[name] = mock

        result = scorer.score(_make_info(), _make_daily([10.0] * 30))
        assert result.technical == 10.0
        assert result.capital_flow == 10.0
        assert result.fundamental == 10.0
        assert result.sector == 10.0
        assert result.event == 10.0

    def test_no_info_passes_none_for_fundamental(self):
        scorer = FiveDimensionScorer()
        for name in scorer.scorers:
            mock = MagicMock()
            mock.score.return_value = 0.0
            scorer.scorers[name] = mock

        result = scorer.score(None, _make_daily([10.0] * 30))
        assert isinstance(result, ScoreResult)
