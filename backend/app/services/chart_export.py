import io

from PIL import Image, ImageDraw, ImageFont

_BG = (255, 255, 255)
_AXIS_TEXT = (30, 30, 30)
_LOW = (235, 244, 255)
_HIGH = (30, 90, 200)
_GRID = (210, 210, 210)


def _lerp_color(low: tuple[int, int, int], high: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(low[i] + (high[i] - low[i]) * t) for i in range(3))


def render_confusion_matrix_png(labels: list[str], matrix: list[list[int]]) -> bytes:
    """Menggambar confusion matrix sebagai PNG sederhana namun jelas terbaca,
    tanpa dependensi tambahan (hanya Pillow, yang sudah dipakai reportlab)."""
    n = len(labels)
    cell = 90
    margin_left = 130
    margin_top = 60
    margin_bottom = 40
    margin_right = 30
    width = margin_left + cell * n + margin_right
    height = margin_top + cell * n + margin_bottom

    img = Image.new("RGB", (width, height), _BG)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.load_default(size=16)
        font_small = ImageFont.load_default(size=13)
    except TypeError:
        font = ImageFont.load_default()
        font_small = font

    max_val = max((v for row in matrix for v in row), default=1) or 1

    draw.text((width // 2 - 60, 15), "Confusion Matrix", fill=_AXIS_TEXT, font=font)

    for row_idx, row in enumerate(matrix):
        for col_idx, value in enumerate(row):
            x0 = margin_left + col_idx * cell
            y0 = margin_top + row_idx * cell
            t = value / max_val
            color = _lerp_color(_LOW, _HIGH, t)
            draw.rectangle([x0, y0, x0 + cell, y0 + cell], fill=color, outline=_GRID)
            text_color = (255, 255, 255) if t > 0.55 else (20, 20, 20)
            text = str(value)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((x0 + cell / 2 - tw / 2, y0 + cell / 2 - th / 2), text, fill=text_color, font=font)

    for col_idx, label in enumerate(labels):
        x0 = margin_left + col_idx * cell
        draw.text((x0 + 10, margin_top - 25), label[:10], fill=_AXIS_TEXT, font=font_small)

    for row_idx, label in enumerate(labels):
        y0 = margin_top + row_idx * cell
        draw.text((10, y0 + cell / 2 - 8), label[:14], fill=_AXIS_TEXT, font=font_small)

    draw.text((margin_left, height - 30), "Prediksi ->", fill=_AXIS_TEXT, font=font_small)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
