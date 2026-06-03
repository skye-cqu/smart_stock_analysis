from __future__ import annotations

import os

from src.data.models import AnalysisResult, ScoreResult, StrategySignal
from src.report.generator import generate_report


def _make_result(**overrides) -> AnalysisResult:
    defaults = dict(
        stock_code="000001",
        stock_name="平安银行",
        current_price=12.50,
        score=ScoreResult(
            total=65.0,
            technical=70.0,
            capital_flow=60.0,
            fundamental=55.0,
            sector=40.0,
            event=30.0,
        ),
        strategy_signals=[
            StrategySignal(
                strategy_name="ma_cross", stock_code="000001", signal="buy", strength=0.8
            ),
            StrategySignal(
                strategy_name="rsi_oversold", stock_code="000001", signal="hold", strength=0.3
            ),
        ],
        llm_analysis="短期看涨，关注12.5支撑位。",
        recommendation="买入",
    )
    defaults.update(overrides)
    return AnalysisResult(**defaults)


def test_report_file_created(tmp_path):
    result = _make_result()
    path = generate_report(result, output_dir=str(tmp_path))
    assert os.path.isfile(path)
    assert "000001" in path


def test_report_contains_stock_code(tmp_path):
    result = _make_result()
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "000001" in content
    assert "平安银行" in content


def test_report_contains_scoring_section(tmp_path):
    result = _make_result()
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "五维评分" in content
    assert "技术面" in content
    assert "70.0" in content


def test_report_contains_signals(tmp_path):
    result = _make_result()
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "策略信号" in content
    assert "ma_cross" in content


def test_report_contains_llm_analysis(tmp_path):
    result = _make_result()
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "AI分析" in content
    assert "短期看涨" in content


def test_report_contains_recommendation(tmp_path):
    result = _make_result()
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "买入" in content


def test_report_veto_marked(tmp_path):
    result = _make_result(
        score=ScoreResult(
            total=10.0,
            technical=5.0,
            capital_flow=5.0,
            fundamental=5.0,
            sector=5.0,
            event=5.0,
            veto=True,
            veto_reason="基本面异常",
        )
    )
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "一票否决" in content
    assert "基本面异常" in content


def test_report_no_signals(tmp_path):
    result = _make_result(strategy_signals=[])
    path = generate_report(result, output_dir=str(tmp_path))
    with open(path, encoding="utf-8") as f:
        content = f.read()
    assert "无信号" in content
