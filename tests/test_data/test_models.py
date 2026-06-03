from __future__ import annotations

from src.data.models import (
    AnalysisResult,
    ScoreResult,
    StockDailyData,
    StockInfo,
    StrategySignal,
)


class TestStockDailyDataFromAkshare:
    def test_chinese_keys(self):
        row = {
            "日期": "2026-01-15",
            "开盘": 10.5,
            "最高": 11.0,
            "最低": 10.2,
            "收盘": 10.8,
            "成交量": 1000000,
            "成交额": 10800000.0,
            "换手率": 1.5,
        }
        d = StockDailyData.from_akshare(row)
        assert d.date == "2026-01-15"
        assert d.open == 10.5
        assert d.close == 10.8
        assert d.volume == 1000000
        assert d.turnover == 1.5

    def test_english_keys(self):
        row = {
            "date": "2026-01-16",
            "open": 11.0,
            "high": 11.5,
            "low": 10.8,
            "close": 11.2,
            "volume": 2000000,
            "amount": 22400000.0,
            "turnover": 2.0,
        }
        d = StockDailyData.from_akshare(row)
        assert d.date == "2026-01-16"
        assert d.open == 11.0
        assert d.close == 11.2

    def test_mixed_keys_chinese_takes_priority(self):
        row = {
            "日期": "2026-01-17",
            "date": "WRONG",
            "开盘": 12.0,
            "open": 999.0,
            "最高": 12.5,
            "最低": 11.8,
            "收盘": 12.3,
            "成交量": 500000,
            "成交额": 6150000.0,
        }
        d = StockDailyData.from_akshare(row)
        assert d.date == "2026-01-17"
        assert d.open == 12.0

    def test_missing_fields_defaults_to_zero(self):
        row = {}
        d = StockDailyData.from_akshare(row)
        assert d.date == ""
        assert d.open == 0.0
        assert d.close == 0.0
        assert d.volume == 0.0
        assert d.turnover == 0.0

    def test_string_numeric_values(self):
        row = {"日期": "2026-01-01", "收盘": "15.5", "成交量": "3000000"}
        d = StockDailyData.from_akshare(row)
        assert d.close == 15.5
        assert d.volume == 3000000.0


class TestStockInfo:
    def test_basic_construction(self):
        info = StockInfo(code="000001", name="平安银行")
        assert info.code == "000001"
        assert info.name == "平安银行"
        assert info.industry == ""
        assert info.pe_ratio is None
        assert info.pb_ratio is None
        assert info.roe is None

    def test_full_construction(self):
        info = StockInfo(
            code="600519",
            name="贵州茅台",
            industry="白酒",
            market_cap=20000.0,
            pe_ratio=30.0,
            pb_ratio=10.0,
            roe=25.0,
        )
        assert info.pe_ratio == 30.0
        assert info.pb_ratio == 10.0
        assert info.roe == 25.0


class TestScoreResult:
    def test_defaults(self):
        sr = ScoreResult()
        assert sr.total == 0.0
        assert sr.veto is False
        assert sr.veto_reason == ""

    def test_all_dimensions(self):
        sr = ScoreResult(
            total=80.0,
            technical=70.0,
            capital_flow=60.0,
            fundamental=50.0,
            sector=40.0,
            event=30.0,
        )
        assert sr.technical == 70.0
        assert sr.event == 30.0

    def test_veto_state(self):
        sr = ScoreResult(total=-100, veto=True, veto_reason="technical critically low")
        assert sr.veto is True
        assert "technical" in sr.veto_reason


class TestStrategySignal:
    def test_basic_construction(self):
        sig = StrategySignal(strategy_name="ma_cross", stock_code="000001", signal="buy")
        assert sig.signal == "buy"
        assert sig.strength == 0.0
        assert sig.indicators == {}

    def test_with_indicators(self):
        sig = StrategySignal(
            strategy_name="rsi",
            stock_code="000001",
            signal="sell",
            strength=0.9,
            indicators={"rsi": 75.0},
        )
        assert sig.strength == 0.9
        assert sig.indicators["rsi"] == 75.0


class TestAnalysisResult:
    def test_basic_construction(self, sample_score_result):
        ar = AnalysisResult(
            stock_code="000001",
            stock_name="Test",
            current_price=10.0,
            score=sample_score_result,
        )
        assert ar.stock_code == "000001"
        assert ar.strategy_signals == []
        assert ar.analysis_date  # auto-populated

    def test_with_strategy_signals(self, sample_score_result):
        signals = [
            StrategySignal("ma_cross", "000001", "buy", 0.8),
            StrategySignal("rsi", "000001", "hold", 0.0),
        ]
        ar = AnalysisResult(
            stock_code="000001",
            stock_name="Test",
            current_price=10.0,
            score=sample_score_result,
            strategy_signals=signals,
        )
        assert len(ar.strategy_signals) == 2
