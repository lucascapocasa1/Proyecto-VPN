"""OCR de capturas de rendimiento FIFA Clubes Pro.

Puerto Python de FIFASTATS (imageProcessor.js / ocr.js / parser.js):
recorte de paneles con Pillow, Tesseract vía pytesseract, parseo de pares
"jugador vs equipo" (siempre se toma el primer número de la línea) y matcheo
de apodos contra el plantel del partido por distancia de Levenshtein.

Las imágenes se procesan en memoria y se descartan al terminar (no se
persisten).
"""
from __future__ import annotations

import io
import os
import re
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageFilter, ImageOps

MAX_IMAGES = 30
MAX_IMAGE_BYTES = 20 * 1024 * 1024
CONCURRENCY = 2

TESSERACT_WHITELIST = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,% "
    "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00c1\u00c9\u00cd\u00d3\u00da\u00d1()"
)
DEFAULT_WIN_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

NOISE_WORDS = {
    "res", "cr", "califica", "calificacion", "calificaci\u00f3n", "nombre",
    "po", "pdc", "dfc", "dci", "dd", "di", "mcd", "mci", "mc", "md", "mi",
    "ext", "sd", "si", "dc", "glb", "mor", "l", "mu",
}

RATING_KEYWORDS = [
    "calificaci\u00f3n", "calificacion", "calif", "cr", "rating",
    "valoraci\u00f3n", "valoracion", "cal",
]

INT_FIELDS = (
    "goals", "assists", "shots", "shot_accuracy_pct", "passes",
    "pass_accuracy_pct", "dribbles", "dribble_success_pct", "tackles",
    "tackle_success_pct", "offsides", "fouls", "possession_won",
    "possession_lost", "minutes_played",
)
PCT_FIELDS = {
    "shot_accuracy_pct", "pass_accuracy_pct",
    "dribble_success_pct", "tackle_success_pct",
}

# (campo, keywords, exclude): la línea debe contener alguna keyword y ninguna exclude
FIELD_RULES = [
    ("goals", ["goles", "goal"], []),
    ("assists", ["asist", "assist"], []),
    ("shots", ["tiros", "shots"], ["precisi"]),
    ("shot_accuracy_pct", ["precisi\u00f3n en los tiros", "precision en los tiros", "precisi"], ["pases", "passes"]),
    ("passes", ["pases", "passes"], ["precisi"]),
    ("pass_accuracy_pct", ["precisi\u00f3n en los pases", "precision en los pases", "precisi"], ["tiros", "shots"]),
    ("dribbles", ["regates", "dribbles"], ["tasa", "xito"]),
    ("dribble_success_pct", [
        "tasa de \u00e9xito de los regates", "tasa de exito de los regates",
        "\u00e9xito de los regates", "exito de los regates",
    ], []),
    ("tackles", ["entradas", "tackles"], ["tasa", "xito"]),
    ("tackle_success_pct", [
        "tasa de \u00e9xito en entradas", "tasa de exito en entradas",
        "\u00e9xito en entradas", "exito en entradas",
    ], []),
    ("offsides", ["fueras de lugar", "fuera de juego", "fueras de juego", "offside"], []),
    ("fouls", ["faltas cometidas", "faltas"], []),
    ("possession_won", ["posesi\u00f3n ganada", "posesion ganada"], []),
    ("possession_lost", ["posesi\u00f3n perdida", "posesion perdida"], []),
    ("minutes_played", ["minutos jugados", "minutes"], []),
]

STAT_KEYS = list(INT_FIELDS) + ["rating", "distance_km", "sprint_distance_km"]


class TesseractNotAvailable(Exception):
    """Tesseract no está instalado o no es invocable en este entorno."""


# ── Levenshtein / matcheo de plantel ─────────────────────────────────────

def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[n]


def match_player(detected: str | None, roster: list[dict]) -> dict | None:
    """Matchea el apodo detectado contra el plantel (nickname + aliases).

    roster: [{"player": id, "nickname": str, "aliases": set/list de str}]
    Umbral FIFASTATS: máximo 3 ediciones o 40% de la longitud del nombre.
    """
    if not detected:
        return None
    needle = detected.lower().strip()
    best = None
    best_dist = None
    for entry in roster:
        for alias in entry.get("aliases") or {entry.get("nickname", "")}:
            alias = (alias or "").lower()
            if not alias:
                continue
            if alias == needle:
                return entry
            dist = levenshtein(needle, alias)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = entry
    if best is None:
        return None
    threshold = max(3, int(len(needle) * 0.4))
    if best_dist is not None and best_dist <= threshold:
        return best
    return None


# ── Parser (puerto de parser.js) ─────────────────────────────────────────

def extract_selected_player(name_text: str) -> str | None:
    lines = [l.strip() for l in name_text.splitlines() if l.strip()]
    for line in lines:
        clean = line.lower()
        if clean in NOISE_WORDS:
            continue
        if re.fullmatch(r"[a-z][a-z0-9_\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]{2,25}", clean):
            return clean
    for line in lines:
        for part in line.split():
            lower = part.lower()
            if lower in NOISE_WORDS:
                continue
            if re.fullmatch(r"[a-z][a-z0-9_\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]{3,20}", lower) and not lower.isdigit():
                return lower
    return None


def extract_first_number(raw: str) -> float | None:
    """Primer número de la línea (valor del jugador en el par "jugador vs equipo").

    Previamente normaliza misreads de OCR: 0 → O/o, o), Lo), oO, E.
    """
    s = raw
    s = re.sub(r"[Oo]\)", "0", s)
    s = re.sub(r"Lo\)", "0", s)
    s = re.sub(r"[Oo]O", "0", s)
    s = re.sub(r"\b[Oo]\b", "0", s)
    s = re.sub(r"\b[Ee]\b", "0", s)
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def _find_stat(lines: list[str], keywords: list[str], exclude: list[str]) -> float | None:
    for line in lines:
        lower = line.lower()
        if any(kw.lower() in lower for kw in keywords) and not any(
            ex.lower() in lower for ex in exclude
        ):
            val = extract_first_number(line)
            if val is not None:
                return val
    return None


def _replace_first(s: str, old: str, new: str) -> str:
    return s.replace(old, new, 1)


def _mirror_match(high: float, low: float) -> bool:
    """True si high con 9↔6 (primera ocurrencia, como JS) da low."""
    high_s = f"{high:.1f}"
    low_s = f"{low:.1f}"
    return _replace_first(high_s, "9", "6") == low_s or _replace_first(high_s, "6", "9") == low_s


def extract_valoracion(text: str) -> float | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # 1. Líneas con palabras clave de calificación
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in RATING_KEYWORDS):
            nums = re.findall(r"\b\d\.\d\b", line)
            if nums:
                first = float(nums[0])
                if 1.0 <= first <= 10.0:
                    if first >= 9.0 and len(nums) >= 2:
                        second = float(nums[1])
                        if 1.0 <= second <= 10.0 and _mirror_match(first, second):
                            return second
                    return first

    # 2. Fallback: cualquier decimal del texto
    matches = re.findall(r"\b\d\.\d\b", text)
    if matches:
        ratings = sorted(
            (float(m) for m in matches if 1.0 <= float(m) <= 10.0), reverse=True
        )
        if ratings:
            if ratings[0] >= 9.0 and len(ratings) >= 2:
                for other in ratings[1:]:
                    if _mirror_match(ratings[0], other):
                        return other
            return ratings[0]

    # 3. Fallback: decimales con coma
    for m in re.findall(r"\b\d,\d\b", text):
        val = float(m.replace(",", "."))
        if 1.0 <= val <= 10.0:
            return val
    return None


def extract_valoracion_from_name(name_text: str) -> float | None:
    for raw_line in name_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = re.search(r"(\d\.\d)\s*$", line)
        if m:
            val = float(m.group(1))
            if 1.0 <= val <= 10.0:
                return val
        all_nums = re.findall(r"\b\d\.\d\b", line)
        if len(all_nums) == 1:
            val = float(all_nums[0])
            if 1.0 <= val <= 10.0:
                return val
        paren = re.search(r"\((\d+(?:\.\d+)?)\)", line)
        if paren:
            val = float(paren.group(1))
            if 1.0 <= val <= 10.0:
                return val
        for n in re.findall(r"\b\d+\b", line):
            val = int(n)
            if 1 <= val <= 10:
                return float(val)
    return None


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def parse_stats(stats_text: str, name_text: str | None = None) -> dict:
    lines = [l.strip() for l in stats_text.splitlines() if l.strip()]
    result: dict = {k: None for k in STAT_KEYS}

    val_name = extract_valoracion_from_name(name_text) if name_text else None
    val_stats = extract_valoracion(stats_text)
    rating = val_name if val_name is not None else val_stats
    if val_name is not None and val_stats is not None and val_stats < val_name:
        if _mirror_match(val_name, val_stats):
            rating = val_stats
    if rating is not None:
        rating = _clamp(round(rating, 1), 0.0, 10.0)
    result["rating"] = rating

    for field, keywords, exclude in FIELD_RULES:
        val = _find_stat(lines, keywords, exclude)
        if val is not None:
            result[field] = val

    # Distancias: "Distancia recorrida" / "Distancia en carrera (sprint)"
    for line in lines:
        lower = line.lower()
        is_recorrida = ("dist" in lower and "recorrida" in lower) or ("recorrida vs" in lower)
        is_sprint = ("dist" in lower and "carrera" in lower) or ("sprint" in lower) or ("en carrera vs" in lower)
        nums = re.findall(r"\d+(?:\.\d+)?", line)
        if is_recorrida and nums and result["distance_km"] is None:
            result["distance_km"] = float(nums[0])
        if is_sprint and nums:
            # Si la línea trae ambos pares ("18.1 16.5"), el sprint es el segundo.
            sprint_idx = 1 if (is_recorrida and len(nums) > 1) else 0
            if result["sprint_distance_km"] is None:
                result["sprint_distance_km"] = float(nums[sprint_idx])

    # Tipos y rangos
    for f in INT_FIELDS:
        v = result[f]
        if v is None:
            continue
        iv = int(round(v))
        if f in PCT_FIELDS:
            iv = _clamp(iv, 0, 100)
        elif f == "minutes_played":
            iv = _clamp(iv, 0, 130)
        else:
            iv = max(0, iv)
        result[f] = iv
    for f in ("distance_km", "sprint_distance_km"):
        if result[f] is not None:
            result[f] = float(_clamp(round(result[f], 1), 0.0, 999.9))
    return result


def validate_stats(stats: dict) -> list[str]:
    warnings = []
    if stats.get("rating") is None:
        warnings.append("No se detectó el rating (obligatorio para guardar).")
    basic = [stats.get("goals"), stats.get("assists"), stats.get("passes")]
    if all(v is None for v in basic):
        warnings.append("No se pudieron extraer estadísticas básicas (goles, asistencias, pases).")
    return warnings


# ── Procesamiento de imágenes (puerto de imageProcessor.js) ──────────────

def _load(raw: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(raw))
    return img.convert("RGB")


def crop_stats_panel(raw: bytes) -> Image.Image:
    """Panel derecho de estadísticas: x ≥ 0.62, y ≥ 0.10, 3x + binarización."""
    img = _load(raw)
    w, h = img.size
    left = int(w * 0.62)
    top = int(h * 0.10)
    img = img.crop((left, top, w, h))
    cw, ch = img.size
    img = img.resize((cw * 3, ch * 3), Image.LANCZOS)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.point(lambda p: max(0, min(255, int(p * 1.5 - 30))), mode="L")
    img = img.point(lambda p: 255 if p > 128 else 0, mode="L")
    img = img.filter(ImageFilter.SHARPEN)
    return img


def crop_player_name(raw: bytes) -> Image.Image:
    """Panel superior izquierdo del nombre+rating: x 0.02–0.44, y 0.08–0.30."""
    img = _load(raw)
    w, h = img.size
    left = int(w * 0.02)
    top = int(h * 0.08)
    cw = int(w * 0.42)
    ch = int(h * 0.22)
    img = img.crop((left, top, left + cw, top + ch))
    cw, ch = img.size
    img = img.resize((cw * 3, ch * 3), Image.LANCZOS)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img


# ── Tesseract (puerto de ocr.js) ─────────────────────────────────────────

_lang_cache: str | None = None


def _configure_pytesseract():
    import pytesseract

    if os.name == "nt" and os.path.exists(DEFAULT_WIN_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = DEFAULT_WIN_TESSERACT
    return pytesseract


def tesseract_available() -> bool:
    try:
        pytesseract = _configure_pytesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _lang() -> str:
    global _lang_cache
    if _lang_cache is None:
        pytesseract = _configure_pytesseract()
        try:
            langs = pytesseract.get_languages(config="")
        except Exception:
            langs = []
        _lang_cache = "spa" if "spa" in langs else "eng"
    return _lang_cache


def run_ocr(img: Image.Image) -> str:
    pytesseract = _configure_pytesseract()
    wl = TESSERACT_WHITELIST.replace('"', "")
    config = (
        '--oem 1 --psm 3 '
        f'-c "tessedit_char_whitelist={wl}" '
        '-c "preserve_interword_spaces=1"'
    )
    return pytesseract.image_to_string(img, lang=_lang(), config=config)


# ── Orquestación ─────────────────────────────────────────────────────────

def process_image(raw: bytes, roster: list[dict], filename: str = "") -> dict:
    result = {
        "filename": filename,
        "success": False,
        "detected_name": None,
        "player": None,
        "player_nickname": None,
        "stats": None,
        "warnings": [],
        "errors": [],
        "ocr_debug": {},
    }
    try:
        name_text = run_ocr(crop_player_name(raw))
        stats_text = run_ocr(crop_stats_panel(raw))
        result["ocr_debug"] = {
            "name_text": name_text[:300],
            "stats_text": stats_text[:800],
        }

        detected = extract_selected_player(name_text)
        result["detected_name"] = detected
        matched = match_player(detected, roster)
        if matched is not None:
            result["player"] = matched["player"]
            result["player_nickname"] = matched.get("nickname")

        stats = parse_stats(stats_text, name_text)
        result["stats"] = stats
        result["warnings"] = validate_stats(stats)
        result["success"] = True
    except Exception as exc:  # noqa: BLE001 - se reporta por imagen
        result["errors"].append(f"Error: {exc}")
    return result


def analyze_images(images: list[tuple[str, bytes]], roster: list[dict]) -> list[dict]:
    """Procesa hasta MAX_IMAGES imágenes con CONCURRENCY hilos (Tesseract es subprocess)."""
    if not images:
        raise ValueError("No se enviaron imágenes.")
    if len(images) > MAX_IMAGES:
        raise ValueError(f"Máximo {MAX_IMAGES} imágenes por solicitud.")
    if not tesseract_available():
        raise TesseractNotAvailable("Tesseract no está instalado en el servidor.")
    workers = min(CONCURRENCY, len(images))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(process_image, raw, roster, filename)
            for filename, raw in images
        ]
        return [f.result() for f in futures]
