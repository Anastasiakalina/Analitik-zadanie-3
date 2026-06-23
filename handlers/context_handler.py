import os
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from states import AnalysisStates
from services import agent_service

router = Router()
logger = logging.getLogger(__name__)


@router.message(AnalysisStates.waiting_for_context, F.text)
async def receive_context(message: Message, state: FSMContext):
    user_instruction = message.text.strip()

    if len(user_instruction) < 3:
        await message.answer("🤔 Слишком короткая инструкция. Напиши подробнее.")
        return

    await state.update_data(user_instruction=user_instruction)
    await state.set_state(AnalysisStates.analyzing)

    status_msg = await message.answer("🧠 Запускаю AI-агента... ⏳")
    data = await state.get_data()
    file_path = data.get("file_path")
    file_name = data.get("file_name", "файл")

    try:
        result = await asyncio.to_thread(
            agent_service.analyze_data,
            file_path,
            user_instruction
        )
        await status_msg.delete()

        if result["text"]:
            for chunk in [result["text"][i:i + 4096] for i in range(0, len(result["text"]), 4096)]:
                await message.answer(chunk)

        for img_path in result["files"]:
            if os.path.exists(img_path):
                await message.answer_photo(FSInputFile(img_path), caption="📊 График")

    except Exception as e:
        logger.error(f"Ошибка анализа: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка при анализе: {str(e)}")

    # Возвращаемся в idle, файл остаётся в данных
    await state.set_state(AnalysisStates.idle)

    await message.answer(
        f"✅ Анализ файла <b>{file_name}</b> завершён!\n\n"
        "💡 Ты можешь:\n"
        "• Задать <b>дополнительный вопрос</b> к этому файлу (просто напиши)\n"
        "• Загрузить <b>новый файл</b> (просто отправь его)"
    )


@router.message(AnalysisStates.idle, F.text)
async def handle_followup(message: Message, state: FSMContext):
    user_question = message.text.strip()

    if user_question.startswith('/'):
        return

    logger.info(f"Получен доп. вопрос: {user_question}")
    data = await state.get_data()
    file_path = data.get("file_path")

    if not file_path:
        await message.answer("📤 Сначала отправь файл (CSV или Excel).")
        return

    if len(user_question) < 3:
        await message.answer("🤔 Слишком короткий вопрос. Напиши подробнее.")
        return

    await state.set_state(AnalysisStates.analyzing)
    status_msg = await message.answer("🔍 Анализирую... ⏳")

    try:
        result = await asyncio.to_thread(
            agent_service.analyze_data,
            file_path,
            user_question
        )
        await status_msg.delete()

        if result["text"]:
            for chunk in [result["text"][i:i + 4096] for i in range(0, len(result["text"]), 4096)]:
                await message.answer(chunk)

        for img_path in result["files"]:
            if os.path.exists(img_path):
                await message.answer_photo(FSInputFile(img_path), caption="📊 График")

    except Exception as e:
        logger.error(f"Ошибка доп. вопроса: {e}", exc_info=True)
        await message.answer(f"⚠️ Ошибка: {str(e)}")

    # Возвращаемся в idle, файл остаётся в данных
    await state.set_state(AnalysisStates.idle)

    await message.answer(
        "💡 Можешь задать ещё вопрос или загрузить новый файл"
    )