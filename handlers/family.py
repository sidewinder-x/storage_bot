from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import get_db
from config import config
from keyboards.menu import get_main_menu_kb, get_courier_menu_kb  # добавь импорт
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from keyboards.menu import get_my_orders_kb
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from database import get_db
router = Router()


# 📦 Состояния FSM для регистрации курьера
class RegisterCourier(StatesGroup):
    waiting_for_name = State()


@router.callback_query(F.data.startswith("delete_courier_"))
async def delete_courier(callback: CallbackQuery, bot: Bot):
    courier_id = int(callback.data.split("_")[-1])
    print(f"🚮 Курьер на удаление: {courier_id}")

    conn = get_db()
    cur = conn.cursor()

    # Проверим, существует ли курьер
    cur.execute("SELECT name FROM users WHERE id = ?", (courier_id,))
    user = cur.fetchone()

    if not user:
        await callback.answer("❗ Курьер не найден", show_alert=True)
        return

    name = user[0]

    # Удаляем
    cur.execute("DELETE FROM users WHERE id = ?", (courier_id,))
    conn.commit()
    print(f"✅ Курьер {name} удалён")

    # Пробуем уведомить курьера
    try:
        await bot.send_message(courier_id, "❌ Вы были удалены как курьер.")
    except TelegramBadRequest as e:
        print(f"⚠️ Не удалось отправить сообщение курьеру {courier_id}: {e}")

    # Обновляем список
    cur.execute("SELECT id, name, balance FROM users")
    users = cur.fetchall()
    conn.close()

    if not users:
        await callback.message.edit_text("🚚 Курьеры удалены. Список пуст.")
        return

    text = "<b>🚚 Список курьеров:</b>\n\n"
    buttons = []

    for user_id, name, balance in users:
        text += f"👤 <b>{name}</b> | Баланс: {balance} ₽\n"
        buttons.append([InlineKeyboardButton(
            text=f"🗑 Удалить {name}",
            callback_data=f"delete_courier_{user_id}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
# 🧠 /start — проверка на админа или курьера
@router.message(F.text == "/start")
async def check_user_start(message: Message):

    user_id = message.from_user.id

    print(f"🛠️ Запущен /start от user_id = {user_id}, admin = {config.ADMIN_ID}")  # DEBUG

    if user_id == config.ADMIN_ID:
        await message.answer(
            "*🤖 Главное меню*\n\n"
            "Добро пожаловать в систему управления!\n\n"
            "📦 **Управляйте складом**\n"
            "💰 **Следите за финансами**\n"
            "🚚 **Назначайте задания курьерам**\n"
            "📊 **Анализируйте выручку и прибыль**\n\n"
            "👇 *Выберите раздел для продолжения:*",
            reply_markup=get_main_menu_kb(),
            parse_mode="Markdown"
        )
        return

    # Курьер
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()

    if user:
        await message.answer(
            f"👋 Привет, <b>{user[0]}</b>!\n\nДобро пожаловать в курьерский интерфейс.",
            reply_markup=get_courier_menu_kb()
        )
    else:
        await message.answer(
            "👋 Добро пожаловать!\nТы не зарегистрирован как курьер.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Зарегистрироваться", callback_data="register_courier")]
            ])
        )


# 🔹 Курьер нажал "Зарегистрироваться"
@router.callback_query(F.data == "register_courier")
async def ask_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👤 Введите ваше имя для регистрации:")
    await state.set_state(RegisterCourier.waiting_for_name)


# 🔹 Курьер вводит имя → сохраняем

@router.message(RegisterCourier.waiting_for_name)
async def save_courier_name(message: Message, state: FSMContext):
    name = message.text.strip()
    user_id = message.from_user.id

    if len(name) < 2:
        return await message.answer("❗ Имя должно быть минимум из 2 символов. Попробуй ещё раз.")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (id, name, balance) VALUES (?, ?, ?)", (user_id, name, 0))
    conn.commit()
    conn.close()

    await message.answer(
        f"✅ Вы зарегистрированы как <b>{name}</b>!",
        reply_markup=get_courier_menu_kb()  # 🎯 Показываем сразу ПОЛНОЕ меню
    )
    await state.clear()


@router.callback_query(F.data == "my_orders")
async def show_courier_orders(callback: CallbackQuery):
    courier_id = callback.from_user.id
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, product_id, quantity, status FROM orders WHERE assigned_to = ?", (courier_id,))
    orders = cur.fetchall()
    conn.close()

    if not orders:
        await callback.message.edit_text(
            "📦 У вас нет заказов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="my_orders_menu")]
            ])
        )
        return

    text = "<b>🧾 История ваших заказов:</b>\n\n"
    buttons = []

    for order in orders:
        oid, pid, qty, status = order
        text += f"📦 Заказ #{oid} | Товар ID: {pid} | Кол-во: {qty} | Статус: {status}\n"

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_orders_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
@router.callback_query(F.data == "admin_couriers")
async def show_couriers(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, balance FROM users")
    users = cur.fetchall()
    conn.close()

    if not users:
        await callback.message.edit_text("❗ Курьеры не найдены.")
        return

    text = "<b>🚚 Список курьеров:</b>\n\n"
    buttons = []

    for user_id, name, balance in users:
        text += f"👤 <b>{name}</b> | Баланс: {balance} ₽\n"
        buttons.append([InlineKeyboardButton(text=f"🗑 Удалить {name}", callback_data=f"delete_courier_{user_id}")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "my_orders_menu")
async def show_my_orders_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>📋 Мои заказы:</b>\n\nВыберите, что хотите посмотреть:",
        reply_markup=get_my_orders_kb()
    )

@router.callback_query(F.data == "courier_menu")
async def back_to_courier_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()

    if user:
        await callback.message.edit_text(
            f"👋 Привет, <b>{user[0]}</b>!\n\nДобро пожаловать в курьерский интерфейс.",
            reply_markup=get_courier_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "👋 Добро пожаловать!\nТы не зарегистрирован как курьер.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Зарегистрироваться", callback_data="register_courier")]
            ])
        )
@router.callback_query(F.data == "current_orders")
async def show_current_orders(callback: CallbackQuery):
    courier_id = callback.from_user.id
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT o.id, p.name, o.quantity, o.price
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.assigned_to = ? AND o.status = 'in_progress'
    """, (courier_id,))
    orders = cur.fetchall()
    conn.close()

    if not orders:
        await callback.message.edit_text(
            "📬 У вас нет текущих заказов.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="my_orders_menu")]
            ])
        )
        return

    text = "<b>📬 Ваш текущий заказ:</b>\n\n"
    buttons = []

    for order_id, product_name, qty, price in orders:
        text += f"📦 Заказ #{order_id}\n🛠 Товар: {product_name}\n🔢 Кол-во: {qty}\n💰 Цена: {price} ₽\n\n"
        buttons.append([
            InlineKeyboardButton(text=f"✅ Завершить заказ #{order_id}", callback_data=f"finish_order_{order_id}")
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_orders_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "courier_balance")
async def show_courier_balance(callback: CallbackQuery):
    courier_id = callback.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance, name FROM users WHERE id = ?", (courier_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await callback.message.edit_text("❗ Курьер не найден.")
        return

    balance, name = row

    text = f"<b>💸 Баланс курьера {name}:</b>\n\n"
    text += f"📊 Текущий баланс: <b>{balance} ₽</b>\n\n"
    text += "👇 Нажмите, чтобы посмотреть историю выплат:"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧾 История выплат", callback_data="courier_payouts_history")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="courier_menu")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "courier_payouts_history")
async def show_payout_history(callback: CallbackQuery):
    courier_id = callback.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT amount, date FROM expenses
        WHERE name LIKE ?
        ORDER BY date DESC
        LIMIT 10
    """, (f"%курьеру #{courier_id}%",))
    payouts = cur.fetchall()
    conn.close()

    text = "<b>🧾 История выплат:</b>\n\n"

    if payouts:
        for amount, date in payouts:
            text += f"✅ +{amount} ₽ — {date}\n"
    else:
        text += "— пока нет выплат.\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="courier_balance")]
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "courier_stock")
async def show_courier_stock(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, quantity FROM products WHERE quantity > 0")
    products = cur.fetchall()
    conn.close()

    if not products:
        text = "📦 Склад пуст."
    else:
        text = "<b>📦 Склад — в наличии:</b>\n\n"
        for name, qty in products:
            text += f"🔹 {name} — <b>{qty} шт.</b>\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="courier_menu")]
        ]),
        parse_mode="HTML"
    )