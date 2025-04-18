from aiogram.fsm.state import StatesGroup, State

class AddExpenseStates(StatesGroup):
    name = State()
    amount = State()