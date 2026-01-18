from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import yaml
import pdfplumber

from app.core.errors import DetectError

@dataclass
class FormatDef:
    id: str
    banco: str
    tipo_producto: str
    text_should_contain: list[str]
    text_must_contain_any: list[str]
    regex_should_match: list[str]

def _load_format_defs(formats_dir: Path) -> list[FormatDef]:
    defs: list[FormatDef] = []
    for p in sorted(formats_dir.glob("*.yml")):
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        defs.append(FormatDef(
            id=str(data.get("id", p.stem)),
            banco=str(data.get("banco", "UNKNOWN")),
            tipo_producto=str(data.get("tipo_producto", "UNKNOWN")),
            text_should_contain=list(data.get("text_should_contain", []) or []),
            text_must_contain_any=list(data.get("text_must_contain_any", []) or []),
            regex_should_match=list(data.get("regex_should_match", []) or []),
        ))
    return defs

def _extract_text_sample(pdf_path: str, max_pages: int = 2) -> str:
    # Solo muestreamos primeras páginas para detectar rápido
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:max_pages]
            chunks = []
            for pg in pages:
                t = pg.extract_text() or ""
                chunks.append(t)
        return "\n".join(chunks)
    except Exception:
        return ""

def _score_format(fmt: FormatDef, text: str) -> int:
    up = (text or "").upper()
    score = 0

    # must contain any (si no cumple, score = 0)
    if fmt.text_must_contain_any:
        if not any(k.upper() in up for k in fmt.text_must_contain_any):
            return 0
        score += 20

    # should contain suma
    for k in fmt.text_should_contain:
        if k.upper() in up:
            score += 5

    # regex hints
    for rx in fmt.regex_should_match:
        try:
            if re.search(rx, text, flags=re.MULTILINE):
                score += 5
        except re.error:
            continue

    return score

def detect_format(pdf_path: str) -> tuple[FormatDef, str]:
    """
    Devuelve (format_def, extracted_text_sample).
    """
    formats_dir = Path(__file__).resolve().parents[1] / "formats"
    defs = _load_format_defs(formats_dir)
    if not defs:
        raise DetectError("No hay definiciones YAML en app/formats/")

    text = _extract_text_sample(pdf_path, max_pages=2)
    # Si no hay texto, más adelante aquí se conectará OCR.
    # Por ahora, si text vacío, seguimos, pero probablemente score será bajo.
    best = None
    best_score = -1

    for d in defs:
        s = _score_format(d, text)
        if s > best_score:
            best_score = s
            best = d

    if not best or best_score <= 0:
        raise DetectError("No se pudo detectar el formato por contenido (score insuficiente).")

    return best, text
