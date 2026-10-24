"""
Telegram Emoji Pack Banner Generator Bot
===================================================
Author:  Lux
Telegram: @photoshopgame
GitHub:  https://github.com/photoshopgame
License: MIT
===================================================
Асинхронный бот на aiogram 3.x для генерации баннеров-превью
эмодзи-паков Telegram (1920x1200) с рендером .TGS / Lottie.
"""

import asyncio
import html
import io
import logging
import os
import re
from typing import List, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

from render import (
    RENDER_ENGINE,
    create_banner,
    detect_file_format,
    render_emoji_to_image,
)

# Метаданные автора и проекта
__author__ = "Lux"
__telegram__ = "@photoshopgame"
__version__ = "1.0.0"

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.warning("Переменная окружения BOT_TOKEN не установлена! Укажите её в .env или экспортируйте.")

dp = Dispatcher()


def extract_pack_name(text: str) -> Optional[str]:
    """Извлекает имя пака из различных ссылок и строк."""
    text = text.strip()
    patterns = [
        r"(?:https?:\/\/)?t\.me\/addemoji\/([a-zA-Z0-9_]+)",
        r"(?:https?:\/\/)?t\.me\/addstickers\/([a-zA-Z0-9_]+)",
        r"tg:\/\/addemoji\?set=([a-zA-Z0-9_]+)",
        r"tg:\/\/addstickers\?set=([a-zA-Z0-9_]+)",
        r"^([a-zA-Z0-9_]{3,})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def sync_render_pipeline(title: str, raw_files: List[bytes]) -> io.BytesIO:
    """
    Синхронный пайплайн рендеринга для выполнения в потоке (asyncio.to_thread).
    """
    emoji_images = []
    errors = []

    for idx, data in enumerate(raw_files):
        try:
            img = render_emoji_to_image(data, target_size=(256, 256))
            emoji_images.append(img)
        except Exception as e:
            fmt = detect_file_format(data)
            error_str = f"Эмодзи #{idx + 1} (формат: {fmt}): {e}"
            errors.append(error_str)
            logger.warning(error_str)

    if not emoji_images:
        first_err = errors[0] if errors else "Неизвестная ошибка"
        first_fmt = detect_file_format(raw_files[0]) if raw_files else "none"

        if RENDER_ENGINE is None and first_fmt in ("tgs", "json"):
            raise ValueError(
                "❌ <b>Движок рендера TGS не установлен в окружении Python!</b>\n\n"
                f"Формат ваших эмодзи: <code>{first_fmt.upper()}</code> (валидный векторный Lottie).\n"
                "Но в среде, где запущен бот, не установлена библиотека рендеринга.\n\n"
                "👉 <b>Решение:</b> выполните в терминале:\n"
                "<code>pip install lottie cairosvg</code>\n"
                "(или <code>pip install rlottie-python</code>)\n\n"
                "Затем перезапустите бота <code>python main.py</code>."
            )

        raise ValueError(
            f"Не удалось сконвертировать эмодзи.\n"
            f"Активный движок: {RENDER_ENGINE}\n"
            f"Формат первого файла: {first_fmt}\n"
            f"Ошибка: {first_err}"
        )

    return create_banner(title=title, emoji_images=emoji_images)


# ==========================================
# 🐣 Секретная пасхалка от создателя (Lux)
# ==========================================
@dp.message(Command("lux", "photoshopgame", "creator", "easteregg"))
@dp.message(F.text.lower().in_({"lux", "люкс", "photoshopgame", "@photoshopgame"}))
async def cmd_easter_egg(message: Message):
    """Секретная пасхалка от Lux (@photoshopgame)."""
    easter_egg_card = (
        "✨ <b>Easter Egg Activated!</b>\n\n"
        "<code>┌──────────────────────────────────────┐\n"
        "│  ⚡️  Crafted with passion by Lux     │\n"
        "│  🎨  Telegram: @photoshopgame         │\n"
        "│  🚀  Emoji Pack Banner Generator     │\n"
        "└──────────────────────────────────────┘</code>\n\n"
        "<i>«Pixel-perfect design is not an accident — it's an obsession.»</i>\n\n"
        "Спасибо, что пользуетесь ботом! Если есть идеи или предложения — пишите лично."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать Lux (@photoshopgame)",
                    url="https://t.me/photoshopgame",
                )
            ]
        ]
    )
    await message.answer(easter_egg_card, parse_mode=ParseMode.HTML, reply_markup=keyboard)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Приветственное сообщение."""
    if RENDER_ENGINE:
        engine_status = f"✅ <b>Движок рендера Lottie/TGS:</b> <code>{RENDER_ENGINE}</code>"
    else:
        engine_status = (
            "⚠️ <b>Внимание:</b> движок рендера Lottie/TGS не обнаружен в Python!\n"
            "Для поддержки векторных TGS установите: <code>pip install lottie cairosvg</code>"
        )

    text = (
        "👋 <b>Привет! Я бот для создания превью-баннеров эмодзи-паков.</b>\n\n"
        "Отправь мне ссылку на пак или его короткое имя, например:\n"
        "• <code>https://t.me/addemoji/Duck</code>\n"
        "• <code>https://t.me/addstickers/Duck</code>\n"
        "• Или просто имя: <code>Duck</code>\n\n"
        f"{engine_status}\n\n"
        "Я скачаю первые 12–18 эмодзи, отренделю их и соберу красивый баннер 1920x1200!\n\n"
        "───────────────\n"
        "⚡️ <i>Created by Lux (Telegram: @photoshopgame)</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Справка по использованию."""
    text = (
        "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
        "1. Скопируйте ссылку на эмодзи-пак в Telegram.\n"
        "2. Отправьте ссылку сюда сообщением.\n"
        "3. Бот вернет готовый полноразмерный баннер (1920x1200) без сжатия и кнопку для быстрой установки пака.\n\n"
        f"<b>Статус движка TGS:</b> <code>{RENDER_ENGINE or 'Не установлен'}</code>\n\n"
        "───────────────\n"
        "👨‍💻 <b>Разработчик:</b> Lux (@photoshopgame)"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(F.text)
async def handle_pack_request(message: Message, bot: Bot):
    """Обработчик входящих ссылок и названий эмодзи-паков."""
    pack_name = extract_pack_name(message.text)
    if not pack_name:
        await message.answer(
            "❌ Не удалось распознать ссылку или имя пака.\n"
            "Пришлите ссылку формата <code>https://t.me/addemoji/...</code> или имя набора.",
            parse_mode=ParseMode.HTML,
        )
        return

    status_msg = await message.answer(
        f"⏳ Получаю информацию о паке <code>{html.escape(pack_name)}</code>...",
        parse_mode=ParseMode.HTML,
    )

    try:
        try:
            sticker_set = await bot.get_sticker_set(name=pack_name)
        except TelegramBadRequest:
            await status_msg.edit_text(
                f"❌ Набор <code>{html.escape(pack_name)}</code> не найден в Telegram.\n"
                "Проверьте правильность ссылки или имени пака.",
                parse_mode=ParseMode.HTML,
            )
            return

        if not sticker_set.stickers:
            await status_msg.edit_text("❌ В этом наборе нет стикеров/эмодзи.")
            return

        selected_stickers = sticker_set.stickers[:18]
        total_selected = len(selected_stickers)

        await status_msg.edit_text(
            f"📥 Скачиваю {total_selected} эмодзи из пака «<b>{html.escape(sticker_set.title)}</b>»...",
            parse_mode=ParseMode.HTML,
        )

        raw_files: List[bytes] = []
        for sticker in selected_stickers:
            try:
                buf = io.BytesIO()
                await bot.download(sticker, destination=buf)
                buf.seek(0)
                raw_files.append(buf.read())
            except Exception as e:
                logger.error(f"Не удалось скачать стикер {sticker.file_id}: {e}")

        if not raw_files:
            await status_msg.edit_text("❌ Не удалось скачать файлы эмодзи.")
            return

        await status_msg.edit_text("🎨 Рендерю эмодзи и собираю баннер 1920x1200...")

        # Рендеринг в отдельном пуле потоков (CPU-bound)
        banner_bio = await asyncio.to_thread(
            sync_render_pipeline,
            title=sticker_set.title,
            raw_files=raw_files,
        )

        add_url = (
            f"https://t.me/addemoji/{pack_name}"
            if getattr(sticker_set, "is_custom_emoji", False)
            else f"https://t.me/addstickers/{pack_name}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Установить пак", url=add_url)]
            ]
        )

        banner_file = BufferedInputFile(
            file=banner_bio.getvalue(),
            filename=f"{pack_name}_preview.png",
        )

        await message.answer_document(
            document=banner_file,
            caption=(
                f"✨ <b>Превью-баннер готов!</b>\n\n"
                f"🏷 <b>Название:</b> {html.escape(sticker_set.title)}\n"
                f"📦 <b>Стихий/эмодзи на баннере:</b> {len(raw_files)}\n\n"
                f"⚡️ <i>by Lux (@photoshopgame)</i>"
            ),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception("Ошибка при обработке пака")
        await status_msg.edit_text(
            f"{str(e)}",
            parse_mode=ParseMode.HTML,
        )


async def main():
    if not BOT_TOKEN:
        raise ValueError("Токен бота не найден. Задайте BOT_TOKEN в файле .env или переменных окружения.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logger.info(
        f"Запуск бота... Автор: {__author__} ({__telegram__}) | "
        f"Активный движок рендера Lottie: {RENDER_ENGINE or 'ОТСУТСТВУЕТ'}"
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
