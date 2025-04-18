from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_stock_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить товар", callback_data="stock_add"),
            InlineKeyboardButton(text="📦 Остатки", callback_data="stock_view")
        ],
        [
            InlineKeyboardButton(text="✅ Продажа", callback_data="stock_sale"),
            InlineKeyboardButton(text="📥 Закупка", callback_data="stock_purchase")
        ],
        [
            InlineKeyboardButton(text="❌ Удалить товар", callback_data="stock_delete")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="stock_back")
        ]
    ])