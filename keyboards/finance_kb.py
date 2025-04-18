from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_finance_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Выручка и прибыль", callback_data="finance_profit")
        ],
        [InlineKeyboardButton(text="➕ Добавить трату", callback_data="finance_add_expense")],
        [
            InlineKeyboardButton(text="📉 Расходы", callback_data="finance_expenses"),
            InlineKeyboardButton(text="🧮 Баланс", callback_data="finance_balance")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])