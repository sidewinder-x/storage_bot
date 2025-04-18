from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Склад", callback_data="menu_stock"),
            InlineKeyboardButton(text="💸 Финансы", callback_data="menu_finance")
        ],
        [
            InlineKeyboardButton(text="🚚 Курьеры", callback_data="admin_couriers"),
            InlineKeyboardButton(text="🧾 Отчёты", callback_data="menu_reports")
        ],
        [
            InlineKeyboardButton(text="📦 Создать заказ", callback_data="create_order")
        ]
    ])


def get_courier_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Склад", callback_data="courier_stock"),
            InlineKeyboardButton(text="💸 Баланс", callback_data="courier_balance")
        ],
        [InlineKeyboardButton(text="📋 Мои заказы", callback_data="my_orders_menu")]
    ])

def get_my_orders_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Текущий заказ", callback_data="current_orders")],
        [InlineKeyboardButton(text="🧾 История заказов", callback_data="my_orders")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="courier_menu")]
    ])