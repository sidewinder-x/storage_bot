from database import get_db
from keyboards.finance_kb import get_finance_menu_kb
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states.finance_states import AddExpenseStates
from datetime import datetime
router = Router()
@router.callback_query(F.data == "finance_profit")
async def show_profit(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        s.quantity, 
        p.sell_price, 
        p.buy_price
    FROM sales s
    JOIN products p ON s.product_id = p.id
    """)
    rows = cur.fetchall()
    conn.close()

    total_revenue = 0
    total_cost = 0

    for qty, sell_price, buy_price in rows:
        total_revenue += qty * sell_price
        total_cost += qty * buy_price

    profit = total_revenue - total_cost

    text = (
        f"📈 <b>Выручка и прибыль</b>\n\n"
        f"💵 Общая выручка: <b>{total_revenue} ₽</b>\n"
        f"📦 Себестоимость: <b>{total_cost} ₽</b>\n"
        f"💰 Чистая прибыль: <b>{profit} ₽</b>"
    )

    await callback.message.edit_text(text, reply_markup=get_finance_menu_kb())

@router.callback_query(F.data == "menu_finance")
async def open_finance(callback: CallbackQuery):
    await callback.message.edit_text(
        "💸 *Финансы и прибыль:*\n\n Следи за своими доходами и расходами в этом разделе:",
        reply_markup=get_finance_menu_kb(),
        parse_mode = "Markdown"
    )


@router.callback_query(F.data == "finance_add_expense")
async def start_add_expense(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите название траты:")
    await state.set_state(AddExpenseStates.name)


@router.message(AddExpenseStates.name)
async def get_expense_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💰 Введите сумму траты:")
    await state.set_state(AddExpenseStates.amount)


@router.message(AddExpenseStates.amount)
async def get_expense_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")

    data = await state.get_data()
    name = data["name"]
    amount = int(message.text)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (name, amount, date) VALUES (?, ?, ?)",
        (name, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    await message.answer(
        f"✅ Трата <b>{name}</b> на <b>{amount} ₽</b> добавлена!",
        reply_markup=get_finance_menu_kb()
    )
    await state.clear()

@router.callback_query(F.data == "finance_expenses")
async def show_expenses(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, amount, date FROM expenses ORDER BY date DESC")
    expenses = cur.fetchall()
    conn.close()

    if not expenses:
        await callback.message.edit_text(
            "📉 Пока нет зарегистрированных расходов.",
            reply_markup=get_finance_menu_kb()
        )
        return

    text = "<b>📉 Все расходы:</b>\n\n"
    total = 0

    for name, amount, date in expenses:
        total += amount
        text += f"• <b>{name}</b> — {amount} ₽ ({date})\n"

    text += f"\n💸 <b>Всего расходов:</b> {total} ₽"

    await callback.message.edit_text(text, reply_markup=get_finance_menu_kb())

@router.callback_query(F.data == "finance_balance")
async def show_balance(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()

    # Получаем данные по продажам
    cur.execute("""
    SELECT s.quantity, p.sell_price, p.buy_price
    FROM sales s
    JOIN products p ON s.product_id = p.id
    """)
    sales = cur.fetchall()

    total_revenue = 0
    total_cost = 0

    for qty, sell_price, buy_price in sales:
        total_revenue += qty * sell_price
        total_cost += qty * buy_price

    # Получаем сумму всех расходов
    cur.execute("SELECT SUM(amount) FROM expenses")
    expenses_total = cur.fetchone()[0] or 0

    conn.close()

    profit = total_revenue - total_cost
    balance = profit - expenses_total

    text = (
        f"🧮 <b>Баланс:</b>\n\n"
        f"💵 Выручка: {total_revenue} ₽\n"
        f"📦 Себестоимость: {total_cost} ₽\n"
        f"💰 Прибыль: {profit} ₽\n"
        f"📉 Расходы: {expenses_total} ₽\n\n"
        f"💎 <b>Чистый баланс:</b> {balance} ₽"
    )

    await callback.message.edit_text(text, reply_markup=get_finance_menu_kb())