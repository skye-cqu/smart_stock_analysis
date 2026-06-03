from __future__ import annotations

from src.llm.parsers import parse_analysis


class TestParseAnalysis:
    def test_standard_json(self):
        raw = '{"technical_view": "上涨趋势", "recommendation": "买入", "risk_notes": "注意回调"}'
        result = parse_analysis(raw)
        assert result.technical_view == "上涨趋势"
        assert result.recommendation == "买入"
        assert result.risk_notes == "注意回调"

    def test_markdown_json_block(self):
        raw = """这是分析结果：

```json
{"technical_view": "震荡", "recommendation": "持有", "risk_notes": "观望"}
```

以上为分析。"""
        result = parse_analysis(raw)
        assert result.technical_view == "震荡"
        assert result.recommendation == "持有"

    def test_markplain_code_block(self):
        raw = """```
{"technical_view": "下降", "recommendation": "卖出", "risk_notes": "止损"}
```"""
        result = parse_analysis(raw)
        assert result.technical_view == "下降"
        assert result.recommendation == "卖出"

    def test_garbage_text_fallback(self):
        raw = "这是一段完全无法解析的文本，不是JSON格式"
        result = parse_analysis(raw)
        # Fallback: technical_view = raw[:300], recommendation = "持有"
        assert result.recommendation == "持有"
        assert "无法解析" in result.technical_view

    def test_empty_string_fallback(self):
        result = parse_analysis("")
        assert result.recommendation == "持有"

    def test_partial_json_missing_fields(self):
        raw = '{"technical_view": "看涨"}'
        result = parse_analysis(raw)
        assert result.technical_view == "看涨"
        assert result.recommendation == "持有"  # default for missing

    def test_json_with_extra_text_around_extracted(self):
        raw = """根据分析，结果如下：
{"technical_view": "强势", "recommendation": "买入", "risk_notes": "追高风险"}
请注意以上仅供参考。"""
        result = parse_analysis(raw)
        assert result.technical_view == "强势"
        assert result.recommendation == "买入"
        assert result.risk_notes == "追高风险"

    def test_nested_json_with_extra_fields(self):
        raw = '{"technical_view": "test", "recommendation": "持有", "risk_notes": "r", "extra": "ignored"}'
        result = parse_analysis(raw)
        assert result.technical_view == "test"

    def test_long_garbage_truncated(self):
        raw = "x" * 500
        result = parse_analysis(raw)
        assert len(result.technical_view) <= 300

    def test_whitespace_only(self):
        result = parse_analysis("   \n  \t  ")
        assert result.recommendation == "持有"

    def test_json_with_trailing_comma_in_prose_fallback(self):
        raw = "分析如下：{broken json here} 请参考"
        result = parse_analysis(raw)
        assert result.recommendation == "持有"  # invalid JSON still falls back

    def test_multiple_json_objects_extracts_first(self):
        raw = '前文 {"technical_view": "第一个", "recommendation": "买入"} 中间 {"other": "第二个"} 后文'
        result = parse_analysis(raw)
        assert result.technical_view == "第一个"
        assert result.recommendation == "买入"

    def test_json_with_newlines_in_prose(self):
        raw = """以下是分析报告：

{
  "technical_view": "看涨趋势",
  "recommendation": "买入",
  "risk_notes": "注意风险"
}

以上为AI分析结果。"""
        result = parse_analysis(raw)
        assert result.technical_view == "看涨趋势"
        assert result.recommendation == "买入"
