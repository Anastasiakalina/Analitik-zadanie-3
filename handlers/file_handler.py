import os
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from states import AnalysisStates
from services import agent_service

router = Router()
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_extension(file_name: str) -> str:
    return os.path.splitext(file_name)[1].lower()


@router.message(AnalysisStates.idle, F.document)
async def receive_file(message: Message, state: FSMContext, bot: Bot):
    try:
        logger.info(f"Получен файл от пользователя {message.from_user.id}")
        document = message.document
        file_name = document.file_name or "data.csv"
        ext = _get_extension(file_name)

        if ext not in ALLOWED_EXTENSIONS:
            await message.answer(
                f"❌ Неподдерживаемый формат: <code>{ext}</code>\n"
                f"Пришли CSV или Excel (.xlsx/.xls)."
            )
            return

        #Проверка размера
        if document.file_size and document.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            await message.answer(f"❌ Файл слишком большой (лимит {MAX_FILE_SIZE_MB} МБ).")
            return

        await message.answer("⏳ Загружаю файл...")

        #Скачивание
        file = await bot.get_file(document.file_id)
        local_path = os.path.join(DOWNLOAD_DIR, f"{message.from_user.id}_{file_name}")
        await bot.download_file(file.file_path, destination=local_path)

        if os.path.getsize(local_path) == 0:
            await message.answer("❌ Файл оказался пустым. Попробуйте ещё раз.")
            return

        #Проверка текста к файлу
        caption = message.caption.strip() if message.caption else None

        if caption:
            logger.info(f"Файл с caption: {caption[:50]}...")
            await state.update_data(file_path=local_path, file_name=file_name)
            await state.set_state(AnalysisStates.analyzing)

            await message.answer(
                f"✅ Файл <b>{file_name}</b> получен!\n"
                "⏳ Начинаю анализ..."
            )

            try:
                result = await asyncio.to_thread(
                    agent_service.analyze_data,
                    local_path,
                    caption
                )

                if result["text"]:
                    for chunk in [result["text"][i:i + 4096] for i in range(0, len(result["text"]), 4096)]:
                        await message.answer(chunk)

                logger.info(f"📊 Отправка графиков: {result['files']}")
                for img_path in result["files"]:
                    try:
                        if os.path.exists(img_path):
                            await message.answer_photo(FSInputFile(img_path), caption="📊 График")
                            logger.info(f"✅ Отправлен график: {img_path}")
                        else:
                            logger.warning(f"❌ Файл не существует: {img_path}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка отправки {img_path}: {e}")

            except Exception as e:
                logger.error(f"Ошибка анализа caption: {e}", exc_info=True)
                await message.answer(f"⚠️ Ошибка анализа: {str(e)}")

            await state.set_state(AnalysisStates.idle)

            await message.answer(
                "✅ Анализ завершён!\n\n"
            )
        else:
            await state.update_data(file_path=local_path, file_name=file_name)
            await state.set_state(AnalysisStates.waiting_for_context)

            await message.answer(
                f"✅ Файл <b>{file_name}</b> загружен!\n\n"
                "📝 Напиши, что нужно проанализировать:\n"
            )

    except Exception as e:
        logger.error(f"Ошибка file_handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка загрузки: {str(e)}")
        await state.clear()
        await state.set_state(AnalysisStates.idle)


@router.message(AnalysisStates.idle, ~F.document & ~F.text)
async def wrong_input_idle(message: Message):
    pass