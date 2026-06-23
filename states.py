from aiogram.fsm.state import State, StatesGroup


class AnalysisStates(StatesGroup):
    idle = State()
    waiting_for_context = State()
    analyzing = State()