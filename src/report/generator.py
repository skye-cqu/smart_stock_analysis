from __future__ import annotations

import logging
import os

from src.data.models import AnalysisResult

logger = logging.getLogger(__name__)


def generate_report(result: AnalysisResult, output_dir: str = "reports") -> str:
    """Generate a Markdown analysis report and return the file path."""
    s = result.score
    lines = [
        f"# {result.stock_name} ({result.stock_code}) 分析报告",
        f"日期: {result.analysis_date}  价格: {result.current_price:.2f}",
        "",
        "## 五维评分",
        "",
        "| 维度 | 分数 |",
        "|------|------|",
        f"| 技术面 | {s.technical:.1f} |",
        f"| 资金面 | {s.capital_flow:.1f} |",
        f"| 基本面 | {s.fundamental:.1f} |",
        f"| 板块面 | {s.sector:.1f} |",
        f"| 事件面 | {s.event:.1f} |",
        f"| **综合** | **{s.total:.1f}** |",
        "",
    ]

    if s.veto:
        lines.append(f"> **一票否决**: {s.veto_reason}")
        lines.append("")

    lines.extend(
        [
            "## 策略信号",
            "",
        ]
    )
    for sig in result.strategy_signals:
        lines.append(f"- {sig.strategy_name}: {sig.signal} (strength={sig.strength:.2f})")
    if not result.strategy_signals:
        lines.append("- 无信号")
    lines.append("")

    if result.llm_analysis:
        lines.extend(
            [
                "## AI分析",
                "",
                result.llm_analysis,
                "",
            ]
        )

    lines.extend(
        [
            f"## 建议: {result.recommendation}",
            "",
        ]
    )

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{result.stock_code}_{result.analysis_date}.md")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return file_path
