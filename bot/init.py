import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import asyncio

load_dotenv()
print("✅ Файл .env загружен")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMP_DIR = Path(os.getenv("TEMP_DIR", "temp"))
TEMP_DIR.mkdir(exist_ok=True)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024


def convert_pdf_to_epub(pdf_path: str) -> str:
    """Заглушка конвертации PDF -> EPUB"""
    epub_path = pdf_path.replace(".pdf", ".epub")
    with open(epub_path, "w", encoding="utf-8") as f:
        f.write("Заглушка EPUB файла")
    return epub_path


def cleanup_file(path: Path):
    try:
        if path.exists():
            path.unlink()
            logger.info(f"Удалён файл: {path}")
    except Exception as e:
        logger.error(f"Ошибка удаления файла: {e}")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🤖 *Привет! Я бот для конвертации PDF в EPUB*\n\n"
        "📱 *Как использовать:*\n"
        "1. Отправь PDF-файл\n"
        "2. Дождись конвертации\n"
        "3. Получи EPUB-файл\n\n"
        "⚡ *Максимальный размер:* 20MB",
        parse_mode="Markdown"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 *Команды:*\n"
        "/start — начать\n"
        "/help — помощь\n\n"
        "🔧 *Как использовать:*\n"
        "• Отправь PDF-документ\n"
        "• Бот сконвертирует его в EPUB\n"
        "• Получи готовый файл",
        parse_mode="Markdown"
    )


@dp.message(F.document)
async def handle_document(message: Message):
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

    try:
        await message.answer("⬇️ Скачиваю файл...")
        file = await bot.get_file(doc.file_id)
        await bot.download_file(file.file_path, destination=file_path)

        await message.answer("🔄 Конвертирую PDF в EPUB...")
        epub_path = convert_pdf_to_epub(str(file_path))

        await message.answer("📤 Отправляю результат...")

        epub_file = FSInputFile(epub_path)
        await message.answer_document(epub_file, caption="✅ EPUB-файл готов!")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer(f"❌ Ошибка: {e}")

    finally:
        cleanup_file(file_path)
        if 'epub_path' in locals():
            cleanup_file(Path(epub_path))


@dp.message(F.content_type.in_({"text"}))
async def handle_text(message: Message):
    await message.answer(
        "📄 Отправьте PDF-документ для конвертации в EPUB.\n"
        "Напишите /help для справки."
    )


async def main():
    logger.info("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
