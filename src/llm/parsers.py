from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AnalysisOutput:
    technical_view: str
    fundamental_view: str
    recommendation: str
    risk_notes: str


def parse_analysis(raw: str) -> AnalysisOutput:
    try:
        json_str = raw
        if chr(96) * 3 + "json" in raw:
            json_str = raw.split(chr(96) * 3 + "json")[1].split(chr(96) * 3)[0]
        elif chr(96) * 3 in raw:
            json_str = raw.split(chr(96) * 3)[1].split(chr(96) * 3)[0]
        # If direct parse fails, try extracting JSON object from surrounding prose
        try:
            data = json.loads(json_str.strip())
        except json.JSONDecodeError:
            start = json_str.find("{")
            if start == -1:
                raise
            depth = 0
            end = -1
            for i in range(start, len(json_str)):
                if json_str[i] == "{":
                    depth += 1
                elif json_str[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end == -1:
                raise
            data = json.loads(json_str[start : end + 1])
        return AnalysisOutput(
            technical_view=str(data.get("technical_view", "")),
            fundamental_view=str(data.get("fundamental_view", "")),
            recommendation=str(data.get("recommendation", "持有")),
            risk_notes=str(data.get("risk_notes", "")),
        )
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"Failed to parse LLM output as JSON: {e}")
        return AnalysisOutput(
            technical_view=raw[:300] if raw else "解析失败",
            fundamental_view="LLM输出解析失败",
            recommendation="持有",
            risk_notes="建议保守操作",
        )
