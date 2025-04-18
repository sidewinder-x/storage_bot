from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from keyboards.menu import get_main_menu_kb

router = Router()



@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "**🤖 Добро пожаловать в Smart-бот!**\n\n"
        "Это ваш помощник для:\n"
        "📦 **Учёта товаров**\n"
        "💸 **Фиксации продаж и расходов**\n"
        "📊 **Анализа прибыли и выручки**\n\n"
        "👇 *Выберите раздел для работы:*",
        reply_markup=get_main_menu_kb(),
        parse_mode="Markdown"
    )