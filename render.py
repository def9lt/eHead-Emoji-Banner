"""
Telegram Emoji Pack Banner Renderer
===================================================
Author:  Lux
Telegram: @photoshopgame
GitHub:  https://github.com/photoshopgame
License: MIT
===================================================
Модуль рендера TGS / Lottie / WebM / WebP и верстки баннера-превью эмодзи-пака.
"""

__author__ = "Lux (@photoshopgame)"

import gzip
import io
import math
import os
import subprocess
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Определение доступных движков рендера Lottie / TGS
RENDER_ENGINE: Optional[str] = None

# 1. Проверяем lottie + pycairo (наиболее надежный чистый Python парсер с быстрым рендером cairo)
try:
    import lottie
    from lottie.parsers.tgs import parse_tgs
    from lottie.exporters.cairo import export_png
    RENDER_ENGINE = "lottie_cairo"
except ImportError:
    # 2. Проверяем rlottie-python (обертка Samsung C++ rlottie)
    try:
        from rlottie_python import LottieAnimation
        RENDER_ENGINE = "rlottie_python"
    except ImportError:
        # 3. Проверяем lottie + cairosvg (экспорт через SVG)
        try:
            import lottie
            from lottie.parsers.tgs import parse_tgs
            from lottie.exporters.svg import export_svg
            import cairosvg
            RENDER_ENGINE = "lottie_svg"
        except ImportError:
            # 4. Проверяем pyrlottie
            try:
                from pyrlottie import LottieFile, convMultLottie
                RENDER_ENGINE = "pyrlottie"
            except ImportError:
                RENDER_ENGINE = None


def detect_file_format(data: bytes) -> str:
    """
    Определяет реальный формат файла по сигнатуре (magic bytes):
    - 'tgs': gzip-сжатый JSON Lottie
    - 'json': несжатый JSON Lottie
    - 'webp': статический WebP
    - 'webm': видео-стикер WebM (VP9 + альфа-канал)
    - 'unknown': неизвестный формат
    """
    if len(data) >= 2 and data[:2] == b"\x1f\x8b":
        return "tgs"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if len(data) >= 4 and data[:4] == b"\x1aE\xdf\xa3":
        return "webm"
    # Проверка на JSON
    stripped = data.strip()
    if len(stripped) > 0 and stripped[:1] in (b"{", b"["):
        return "json"
    return "unknown"


def render_webm_frame(data: bytes, target_size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """Извлекает первый кадр из видео-стикера WebM через ffmpeg."""
    try:
        proc = subprocess.run(
            [
                "ffmpeg",
                "-v", "error",
                "-i", "pipe:0",
                "-vframes", "1",
                "-f", "image2pipe",
                "-vcodec", "png",
                "pipe:1"
            ],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        img = Image.open(io.BytesIO(proc.stdout)).convert("RGBA")
        if img.size != target_size:
            img = img.resize(target_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        raise RuntimeError(f"Ошибка рендера WebM через ffmpeg: {e}") from e


def render_webp_frame(data: bytes, target_size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """Загружает статичный WebP кадр."""
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        if img.size != target_size:
            img = img.resize(target_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        raise RuntimeError(f"Ошибка открытия WebP: {e}") from e


def render_lottie_frame(data: bytes, is_gzipped: bool = True, target_size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """
    Рендерит первый кадр Lottie (TGS / JSON) в PNG.
    """
    if RENDER_ENGINE is None:
        raise RuntimeError(
            "В окружении бота НЕ УСТАНОВЛЕН движок рендера Lottie/TGS!\n"
            "Ваши эмодзи действительно в формате TGS, но на сервере не установлена библиотека для их отрисовки.\n"
            "Выполните команду в терминале:\n"
            "👉 pip install lottie\n"
            "(или: pip install rlottie-python)"
        )

    # 1. Вариант через lottie + cairo
    if RENDER_ENGINE == "lottie_cairo":
        try:
            if is_gzipped:
                bio_in = io.BytesIO(data)
                anim = parse_tgs(bio_in)
            else:
                import json
                from lottie.parsers.tgs import parse_lottie
                anim = parse_lottie(json.loads(data.decode("utf-8")))

            bio_out = io.BytesIO()
            export_png(anim, bio_out, frame=0)
            bio_out.seek(0)
            img = Image.open(bio_out).convert("RGBA")
            if img.size != target_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            raise RuntimeError(f"Ошибка рендера через lottie+cairo: {e}") from e

    # 2. Вариант через rlottie-python
    elif RENDER_ENGINE == "rlottie_python":
        try:
            if is_gzipped:
                json_data = gzip.decompress(data).decode("utf-8", errors="ignore")
            else:
                json_data = data.decode("utf-8", errors="ignore")

            anim = LottieAnimation.from_data(json_data)
            frame = anim.render_frame(0)
            if not isinstance(frame, Image.Image):
                frame = Image.fromarray(frame)
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            if frame.size != target_size:
                frame = frame.resize(target_size, Image.Resampling.LANCZOS)
            return frame
        except Exception as e:
            raise RuntimeError(f"Ошибка рендера через rlottie-python: {e}") from e

    # 3. Вариант через lottie + cairosvg
    elif RENDER_ENGINE == "lottie_svg":
        try:
            bio_in = io.BytesIO(data)
            anim = parse_tgs(bio_in)
            bio_svg = io.StringIO()
            export_svg(anim, bio_svg)
            svg_data = bio_svg.getvalue().encode("utf-8")
            png_bytes = cairosvg.svg2png(bytestring=svg_data)
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            if img.size != target_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            raise RuntimeError(f"Ошибка рендера через lottie+svg: {e}") from e

    # 4. Вариант через pyrlottie
    elif RENDER_ENGINE == "pyrlottie":
        import tempfile
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                in_path = os.path.join(tmpdir, "in.tgs")
                out_path = os.path.join(tmpdir, "out.png")
                with open(in_path, "wb") as f:
                    f.write(data)
                convMultLottie([LottieFile(in_path, out_path)])
                if os.path.exists(out_path):
                    img = Image.open(out_path).convert("RGBA")
                    if img.size != target_size:
                        img = img.resize(target_size, Image.Resampling.LANCZOS)
                    return img
                raise RuntimeError("pyrlottie не создал выходной PNG файл")
        except Exception as e:
            raise RuntimeError(f"Ошибка рендера через pyrlottie: {e}") from e

    raise RuntimeError(f"Неизвестный движок рендера: {RENDER_ENGINE}")


def render_emoji_to_image(data: bytes, target_size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """
    Универсальная функция рендеринга эмодзи/стикера любого формата:
    - Автоматически распознает TGS, JSON, WebM, WebP
    - Возвращает чистый Image (RGBA)
    """
    fmt = detect_file_format(data)

    if fmt == "tgs":
        return render_lottie_frame(data, is_gzipped=True, target_size=target_size)
    elif fmt == "json":
        return render_lottie_frame(data, is_gzipped=False, target_size=target_size)
    elif fmt == "webm":
        return render_webm_frame(data, target_size=target_size)
    elif fmt == "webp":
        return render_webp_frame(data, target_size=target_size)
    else:
        # Попытка распаковки gzip наугад
        try:
            decompressed = gzip.decompress(data)
            return render_lottie_frame(decompressed, is_gzipped=False, target_size=target_size)
        except Exception:
            raise ValueError(f"Неизвестный формат файла эмодзи (первые 8 байт: {data[:8]!r})")


def _load_font_fit(
    font_path: str,
    text: str,
    max_width: int,
    initial_size: int = 110,
    min_size: int = 38,
) -> Tuple[ImageFont.FreeTypeFont, int, int]:
    """Динамический подбор максимального размера шрифта под заданную ширину."""
    font_size = initial_size
    temp_img = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(temp_img)

    while font_size >= min_size:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        if text_w <= max_width:
            return font, text_w, text_h
        font_size -= 2

    font = ImageFont.truetype(font_path, min_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    return font, bbox[2] - bbox[0], bbox[3] - bbox[1]


def create_banner(
    title: str,
    emoji_images: List[Image.Image],
    background_path: str = "background.png",
    font_path: str = "BebasNeue-Regular.ttf",
    target_canvas_size: Tuple[int, int] = (1920, 1200),
    title_color: str = "#9BA5B7",
) -> io.BytesIO:
    """Отрисовывает финальный баннер 1920x1200."""
    canvas_w, canvas_h = target_canvas_size

    # 1. Загрузка фона
    bg_candidates = [background_path, "background.png", "Background.png"]
    bg_image: Optional[Image.Image] = None
    for path in bg_candidates:
        if os.path.exists(path):
            try:
                bg_image = Image.open(path).convert("RGBA")
                break
            except Exception:
                pass

    if bg_image is None:
        bg_image = Image.new("RGBA", (canvas_w, canvas_h), (20, 24, 33, 255))
    elif bg_image.size != (canvas_w, canvas_h):
        bg_image = bg_image.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(bg_image)

    # 2. Отрисовка названия пака
    clean_title = (title or "EMOJI PACK").strip().upper()
    title_top_y = 90
    max_title_w = canvas_w - 240

    if not os.path.exists(font_path):
        font_path = "BebasNeue-Regular.ttf"

    font, text_w, text_h = _load_font_fit(
        font_path=font_path,
        text=clean_title,
        max_width=max_title_w,
        initial_size=110,
        min_size=40,
    )

    title_x = (canvas_w - text_w) // 2
    draw.text((title_x, title_top_y), clean_title, font=font, fill=title_color)

    # 3. Расчет области для сетки эмодзи
    grid_top_y = title_top_y + text_h + 80
    grid_bottom_y = canvas_h - 90
    available_height = grid_bottom_y - grid_top_y

    total_emojis = len(emoji_images)
    if total_emojis > 0:
        if total_emojis <= 8:
            rows = 1
            cols = total_emojis
            emoji_dim = min(260, int(available_height * 0.75))
        elif total_emojis <= 14:
            rows = 2
            cols = math.ceil(total_emojis / 2)
            emoji_dim = 230
        else:
            rows = 3
            cols = math.ceil(total_emojis / 3)
            emoji_dim = 200

        max_emoji_w = int((canvas_w - 200) / cols)
        emoji_dim = min(emoji_dim, max_emoji_w)

        total_items_height = rows * emoji_dim
        remaining_h = available_height - total_items_height
        gap_y = max(30, remaining_h // (rows + 1))
        content_total_h = rows * emoji_dim + (rows - 1) * gap_y
        start_y = grid_top_y + (available_height - content_total_h) // 2
        gap_x = 45

        for r in range(rows):
            row_items = emoji_images[r * cols : (r + 1) * cols]
            if not row_items:
                continue

            num_in_row = len(row_items)
            row_width = num_in_row * emoji_dim + (num_in_row - 1) * gap_x
            row_start_x = (canvas_w - row_width) // 2
            curr_y = start_y + r * (emoji_dim + gap_y)

            for c, img in enumerate(row_items):
                curr_x = row_start_x + c * (emoji_dim + gap_x)
                if img.size != (emoji_dim, emoji_dim):
                    scaled_img = img.resize((emoji_dim, emoji_dim), Image.Resampling.LANCZOS)
                else:
                    scaled_img = img

                if scaled_img.mode == "RGBA":
                    bg_image.paste(scaled_img, (curr_x, curr_y), mask=scaled_img.split()[3])
                else:
                    bg_image.paste(scaled_img, (curr_x, curr_y))

    output = io.BytesIO()
    bg_image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
