from __future__ import annotations

from src.data.models import StockInfo
from src.scoring.fundamental_scorer import FundamentalScorer


def _make_info(
    pe_ratio: float | None = None, pb_ratio: float | None = None, roe: float | None = None
) -> StockInfo:
    return StockInfo(
        code="000001",
        name="平安银行",
        industry="银行",
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
        roe=roe,
        market_cap=100.0,
    )


class TestFundamentalScorer:
    def test_good_fundamentals_positive(self):
        info = _make_info(pe_ratio=8.0, pb_ratio=1.0, roe=20.0)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert result > 0

    def test_bad_fundamentals_negative(self):
        info = _make_info(pe_ratio=100.0, pb_ratio=10.0, roe=-5.0)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert result < 0

    def test_none_ratios_returns_zero(self):
        info = _make_info(pe_ratio=None, pb_ratio=None, roe=None)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert result == 0.0

    def test_partial_info(self):
        info = _make_info(pe_ratio=10.0, pb_ratio=None, roe=None)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert result > 0

    def test_score_clamped(self):
        info = _make_info(pe_ratio=5.0, pb_ratio=0.5, roe=30.0)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert -100 <= result <= 100

    def test_negative_pe_penalizes(self):
        info = _make_info(pe_ratio=-10.0, pb_ratio=1.0, roe=5.0)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert result < 0

    def test_extreme_pb_penalizes(self):
        info = _make_info(pe_ratio=15.0, pb_ratio=8.0, roe=12.0)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert result < 30

    def test_zero_data_list(self):
        info = _make_info(pe_ratio=12.0, pb_ratio=2.0, roe=15.0)
        scorer = FundamentalScorer()
        result = scorer.score(info, [])
        assert isinstance(result, float)

    def test_none_info_returns_zero(self):
        scorer = FundamentalScorer()
        result = scorer.score(None, [])
        assert result == 0.0
