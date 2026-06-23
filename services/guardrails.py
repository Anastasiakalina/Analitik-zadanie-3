import re
import logging

logger = logging.getLogger(__name__)

SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"show\s+(me\s+)?your\s+instructions",
    r"what\s+(are|were)\s+your\s+(original\s+)?instructions",
    r"repeat\s+(your\s+)?system\s+prompt",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+if",
    r"pretend\s+you\s+are",
    r"new\s+instructions?:",
    r"override\s+previous",

    r"игнорируй\s+(все\s+)?предыдущие\s+инструкции",
    r"забудь\s+(все\s+)?предыдущие\s+инструкции",
    r"покажи\s+(свой\s+)?системный\s+промпт",
    r"раскрой\s+(свой\s+)?системный\s+промпт",
    r"какие\s+у\s+тебя\s+инструкции",
    r"новые\s+инструкции?:",
    r"ты\s+теперь",
    r"представь\s+что\s+ты",
    r"переопределить\s+предыдущие",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


def check_text_safety(text: str) -> dict:
    if not text:
        return {"is_safe": True, "reason": None}

    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            logger.warning(f"🛡️ Обнаружена попытка prompt injection: {text[:100]}...")
            return {
                "is_safe": False,
                "reason": "Обнаружена подозрительная инструкция. Пожалуйста, сформулируйте запрос иначе."
            }

    return {"is_safe": True, "reason": None}


def check_csv_safety(csv_content: str) -> dict:
    if not csv_content:
        return {"is_safe": True, "reason": None, "suspicious_cells": []}

    suspicious_cells = []

    lines = csv_content.split('\n')
    for line_num, line in enumerate(lines, 1):
        cells = line.split(',')
        for cell_num, cell in enumerate(cells, 1):
            cell_clean = cell.strip().strip('"').strip("'")

            for pattern in COMPILED_PATTERNS:
                if pattern.search(cell_clean):
                    suspicious_cells.append({
                        "line": line_num,
                        "cell": cell_num,
                        "content": cell_clean[:50] + "..." if len(cell_clean) > 50 else cell_clean
                    })
                    break

    if suspicious_cells:
        logger.warning(f"🛡️ Обнаружены подозрительные ячейки в CSV: {len(suspicious_cells)}")
        return {
            "is_safe": False,
            "reason": f"В файле обнаружены подозрительные данные ({len(suspicious_cells)} ячеек). Возможно, это попытка инъекции.",
            "suspicious_cells": suspicious_cells
        }

    return {"is_safe": True, "reason": None, "suspicious_cells": []}