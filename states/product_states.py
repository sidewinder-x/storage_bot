from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    name = State()
    quantity = State()
    buy_price = State()
    sell_price = State()
    photo = State()
class SellProductStates(StatesGroup):
    choosing_product = State()
    entering_quantity = State()

class PurchaseProductStates(StatesGroup):
    choosing_product = State()
    entering_quantity = State()
    entering_price = State()

