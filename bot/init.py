"""Telegram bot for converting PDF files to EPUB.

This bot uses aiogram and supports:
- /start and /help commands with usage instructions
- Receiving PDF documents, validating file type and size
- Converting PDF files to EPUB
- Sending the converted file back to the user
- Temporary file management and cleanup
"""

# --- standard library ---
import asyncio
import os
import logging
from pathlib import Path
from typing import Optional

# --- third-party ---
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info(".env file loaded")

TEMP_DIR = Path(os.getenv("TEMP_DIR", "temp"))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN was not found in .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


def convert_pdf_to_epub(pdf_path: str) -> str:
    """Stub for PDF → EPUB conversion."""
    epub_path = str(Path(pdf_path).with_suffix(".epub"))
    with open(epub_path, "w", encoding="utf-8") as f:
        f.write("EPUB file stub")
    return epub_path


def cleanup_file(path: Path):
    """Delete a file if it exists, logging success or error."""
    try:
        if path.exists():
            path.unlink()
            logger.info("File deleted: %s", path)
    except OSError as e:
        logger.error("File deletion failed: %s", e)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Send initial bot message."""
    await message.answer(
        "🤖 *Привет! Я бот для конвертации PDF в EPUB*\n\n"
        "📱 *Как использовать:*\n"
        "1. Отправь PDF-файл\n"
        "2. Дождись конвертации\n"
        "3. Получи EPUB-файл\n\n"
        f"⚡ *Максимальный размер:* {MAX_FILE_SIZE_MB}MB",
        parse_mode="Markdown",
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Send list of supported commands."""
    await message.answer(
        "📋 *Команды:*\n"
        "/start — начать\n"
        "/help — помощь\n\n"
        "🔧 *Как использовать:*\n"
        "• Отправь PDF-документ\n"
        "• Бот сконвертирует его в EPUB\n"
        "• Получи готовый файл",
        parse_mode="Markdown",
    )


@dp.message(F.document)
async def handle_document(message: Message):
    """Process an incoming document: validate, download, convert, send, and clean up."""
    doc = message.document

    if doc.mime_type != "application/pdf":
        await message.answer("❌ Поддерживаются только PDF-файлы.")
        return

    if doc.file_size > MAX_FILE_SIZE:
        await message.answer(
            f"❌ Файл слишком большой ({doc.file_size / 1024 / 1024:.1f}MB). "
            f"Максимум: {MAX_FILE_SIZE_MB}MB"
        )
        return

    file_name = f"user_{message.from_user.id}_{doc.file_name}"
    file_path = TEMP_DIR / file_name
    epub_path: Optional[str] = None

    try:
        await message.answer("⬇️ Скачиваю файл...")
        tg_file = await bot.get_file(doc.file_id)
        await bot.download_file(tg_file.file_path, destination=file_path)

        await message.answer("🔄 Конвертирую PDF в EPUB...")
        epub_path = convert_pdf_to_epub(str(file_path))

        await message.answer("📤 Отправляю результат...")
        epub_file = FSInputFile(epub_path)
        await message.answer_document(epub_file, caption="✅ EPUB-файл готов!")

    except (OSError, TelegramAPIError) as e:
        logger.error("File processing failed: %s", e)
        await message.answer(f"❌ Ошибка: {e}")

    finally:
        cleanup_file(file_path)
        if epub_path:
            cleanup_file(Path(epub_path))


@dp.message(F.content_type.in_({"text"}))
async def handle_text(message: Message):
    """Respond to plain text with usage hint."""
    await message.answer(
        "📄 Отправьте PDF-документ для конвертации в EPUB.\n"
        "Напишите /help для справки."
    )


async def main():
    """Start the dispatcher and begin bot polling."""
    logger.info("🤖 PDFtoEpub Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
