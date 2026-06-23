from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states import AnalysisStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AnalysisStates.idle)
    await message.answer(
        "👋 Привет! Я — AI-аналитик данных.\n\n"
        "📤 Отправь мне CSV или Excel-файл, "
        "и напиши, что нужно проанализировать.\n\n"
        "Команды:\n"
        "/help — справка\n"
        "/cancel — отменить текущий анализ"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📊 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Отправь файл (CSV/XLSX, до 20 МБ)\n"
        "2️⃣ Напиши текстом, что нужно найти: "
        "3️⃣ Получи ответ\n\n"
        "💻🧑‍💻Этот бот был создан Калинниковой А.И., студенткой группы Б9123-09.03.03цтэ"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять 🙂")
        return
    await state.clear()
    await state.set_state(AnalysisStates.idle)
    await message.answer("❌ Анализ отменён. Отправь новый файл, когда будешь готов.")