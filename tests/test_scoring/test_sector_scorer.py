from __future__ import annotations

from unittest.mock import patch

from src.data.models import StockDailyData, StockInfo
from src.scoring.sector_scorer import SectorScorer


def _make_data(n: int = 10, start_price: float = 10.0, step: float = 0.1) -> list[StockDailyData]:
    return [
        StockDailyData(
            date=f"2025-01-{i + 1:02d}",
            open=start_price + i * step,
            high=start_price + i * step + 0.5,
            low=start_price + i * step - 0.5,
            close=start_price + i * step,
            volume=1_000_000,
            amount=10_000_000,
        )
        for i in range(n)
    ]


class TestSectorScorer:
    def test_no_industry_returns_zero(self):
        info = StockInfo(code="000001", name="Test", industry="")
        data = _make_data(10)
        assert SectorScorer().score(info, data) == 0.0

    def test_insufficient_data_returns_zero(self):
        info = StockInfo(code="000001", name="Test", industry="银行")
        data = _make_data(3)
        assert SectorScorer().score(info, data) == 0.0

    @patch("akshare.stock_board_industry_cons_em")
    def test_stock_outperforms_sector(self, mock_ak):
        import pandas as pd

        # Sector median return = 1.0%
        mock_ak.return_value = pd.DataFrame({"涨跌幅": [0.5, 1.0, 1.5, 2.0, 0.8]})

        info = StockInfo(code="000001", name="Test", industry="银行")
        # Stock 5-day return: 11.8/10.8 - 1 ≈ 9.3% → diff = 9.3 - 1 = 8.3% → +50
        data = _make_data(10, start_price=10.0, step=0.2)
        result = SectorScorer().score(info, data)
        assert result == 50.0

    @patch("akshare.stock_board_industry_cons_em")
    def test_stock_underperforms_sector(self, mock_ak):
        import pandas as pd

        # Sector median return = 8.0%
        mock_ak.return_value = pd.DataFrame({"涨跌幅": [7.0, 8.0, 9.0, 8.5, 7.5]})

        info = StockInfo(code="000001", name="Test", industry="银行")
        # Stock near-flat → diff ≈ -8% → -50
        data = _make_data(10, start_price=10.0, step=0.001)
        result = SectorScorer().score(info, data)
        assert result == -50.0

    @patch("akshare.stock_board_industry_cons_em")
    def test_akshare_exception_returns_zero(self, mock_ak):
        mock_ak.side_effect = Exception("network error")
        info = StockInfo(code="000001", name="Test", industry="银行")
        data = _make_data(10)
        assert SectorScorer().score(info, data) == 0.0

    @patch("akshare.stock_board_industry_cons_em")
    def test_empty_dataframe_returns_zero(self, mock_ak):
        import pandas as pd

        mock_ak.return_value = pd.DataFrame()
        info = StockInfo(code="000001", name="Test", industry="银行")
        data = _make_data(10)
        assert SectorScorer().score(info, data) == 0.0
