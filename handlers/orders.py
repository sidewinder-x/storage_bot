from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_db
from config import config
from keyboards.menu import get_main_menu_kb, get_courier_menu_kb  # добавь импорт
from aiogram.exceptions import TelegramBadRequest

router = Router()


# 📦 Состояния для создания и завершения заказа
class OrderCreation(StatesGroup):
    choosing_product = State()
    entering_quantity = State()
    entering_price = State()


class OrderFinish(StatesGroup):
    waiting_payment_method = State()
    waiting_payout_amount = State()


# 📦 Создание заказа — старт
@router.callback_query(F.data == "create_order")
async def start_order_creation(callback: CallbackQuery, state: FSMContext):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products WHERE quantity > 0")
    products = cur.fetchall()
    conn.close()

    if not products:
        await callback.message.edit_text("❗ Нет товаров для заказа.")
        return

    buttons = [
        [InlineKeyboardButton(text=prod[1], callback_data=f"order_product_{prod[0]}")]
        for prod in products
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])

    await callback.message.edit_text("🛒 Выберите товар для заказа:",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await state.set_state(OrderCreation.choosing_product)


# ➡️ Кол-во товара
@router.callback_query(F.data.startswith("order_product_"))
async def choose_quantity(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)

    await callback.message.edit_text("🔢 Введите количество товара для заказа:")
    await state.set_state(OrderCreation.entering_quantity)


# ➡️ Цена товара
@router.message(OrderCreation.entering_quantity)
async def enter_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите только число.")

    quantity = int(message.text)
    if quantity < 1:
        return await message.answer("❗ Минимум 1 шт.")

    await state.update_data(quantity=quantity)
    await message.answer("💰 Введите цену (если оставить пустым — будет использоваться цена из товара):")
    await state.set_state(OrderCreation.entering_price)


# ✅ Создание заказа и рассылка
@router.message(OrderCreation.entering_price)
async def finish_order(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    price_input = message.text.strip()
    conn = get_db()
    cur = conn.cursor()

    if not price_input:
        cur.execute("SELECT sell_price FROM products WHERE id = ?", (data["product_id"],))
        price = cur.fetchone()[0]
    elif price_input.isdigit():
        price = int(price_input)
    else:
        return await message.answer("❗ Цена должна быть числом или оставьте пустой.")

    # Добавляем заказ
    cur.execute(
        "INSERT INTO orders (product_id, quantity, price, created_at) VALUES (?, ?, ?, datetime('now'))",
        (data["product_id"], data["quantity"], price)
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()

    await state.clear()

    # Рассылаем курьерам
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, photo FROM products WHERE id = ?", (data["product_id"],))
    product = cur.fetchone()
    product_name = product[0]
    product_photo = product[1]  # может быть None
    cur.execute("SELECT id FROM users")
    couriers = cur.fetchall()
    conn.close()

    for courier_id in couriers:
        try:
            text = (
                f"📦 Новый заказ #{order_id}!\n"
                f"🛠 Товар: {product_name}\n"
                f"🔢 Кол-во: {data['quantity']}\n"
                f"💰 Цена: {price} ₽"
            )

            if product_photo:
                await bot.send_photo(
                    courier_id[0],
                    photo=product_photo,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Принять заказ", callback_data=f"accept_order_{order_id}")]
                    ])
                )
            else:
                await bot.send_message(
                    courier_id[0],
                    text=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Принять заказ", callback_data=f"accept_order_{order_id}")]
                    ])
                )

        except Exception as e:
            print(f"❌ Не удалось отправить заказ курьеру {courier_id[0]}: {e}")

    await message.answer("✅ Заказ создан и отправлен всем курьерам.")


# ✅ Курьер принимает заказ
@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[-1])
    courier_id = callback.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()

    if not row or row[0] != 'waiting':
        await callback.answer("❌ Этот заказ уже занят или не существует.", show_alert=True)
        return

    cur.execute("""
        UPDATE orders
        SET status = 'in_progress', assigned_to = ?
        WHERE id = ?
    """, (courier_id, order_id))
    conn.commit()

    cur.execute("SELECT name FROM users WHERE id = ?", (courier_id,))
    name = cur.fetchone()[0]
    conn.close()

    # Удалим старое сообщение, т.к. оно может быть с фото и не редактируемое
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        print(f"⚠️ Не удалось удалить сообщение: {e}")

    # Отправим новое — чистое текстовое сообщение
    await callback.message.answer(
        "✅ Вы приняли заказ.\n\nКогда будете готовы, нажмите кнопку ниже, чтобы начать выполнение.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚚 Начать выполнение", callback_data="start_courier_work")]
        ])
    )

    await callback.message.bot.send_message(
        config.ADMIN_ID,
        f"🚚 Заказ #{order_id} принят курьером <b>{name}</b>."
    )

@router.callback_query(F.data == "start_courier_work")
async def courier_starts_work(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"❌ Не удалось удалить сообщение: {e}")


# 🚚 Курьер завершает заказ — выбирает способ оплаты
@router.callback_query(F.data.startswith("finish_order_"))
async def start_finish_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[-1])
    await state.update_data(order_id=order_id)

    await callback.message.edit_text(
        "💰 Как была получена оплата?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Карта", callback_data="payment_card")],
            [InlineKeyboardButton(text="💵 Наличные", callback_data="payment_cash")]
        ])
    )
    await state.set_state(OrderFinish.waiting_payment_method)


# 🧾 Курьер отправил оплату → сообщение админу
@router.callback_query(OrderFinish.waiting_payment_method, F.data.in_(["payment_card", "payment_cash"]))
async def confirm_finish_order(callback: CallbackQuery, state: FSMContext):
    method = "Карта" if callback.data == "payment_card" else "Наличные"
    data = await state.get_data()
    order_id = data["order_id"]
    courier_id = callback.from_user.id

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET payment_method = ? WHERE id = ?", (method, order_id))
    conn.commit()
    conn.close()

    await state.clear()

    # Добавляем кнопку назад в меню
    await callback.message.edit_text(
        "📝 Запрос отправлен админу.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В меню", callback_data="courier_menu")]
        ])
    )

    await callback.bot.send_message(
        config.ADMIN_ID,
        f"⚠️ Курьер завершил заказ #{order_id}\nСпособ оплаты: <b>{method}</b>\n\n💸 Подтвердите выплату:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Подтвердить выплату", callback_data=f"confirm_finish_{order_id}_{courier_id}")]
        ])
    )
# 💸 Админ вводит сумму выплаты
@router.callback_query(F.data.startswith("confirm_finish_"))
async def ask_payout_amount(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    order_id = int(parts[2])
    courier_id = int(parts[3])

    await state.update_data(order_id=order_id, courier_id=courier_id)
    await callback.message.answer(f"💰 Введите сумму, которую нужно выплатить курьеру за заказ #{order_id}:")
    await state.set_state(OrderFinish.waiting_payout_amount)


# ✅ Завершаем выплату и обновляем всё
@router.message(OrderFinish.waiting_payout_amount)
async def process_payout(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        return await message.answer("❗ Введите сумму числом.")

    payout = int(message.text.strip())
    data = await state.get_data()
    order_id = data["order_id"]
    courier_id = data["courier_id"]

    conn = get_db()
    cur = conn.cursor()

    # 1. Получаем товар и количество из заказа
    cur.execute("SELECT product_id, quantity FROM orders WHERE id = ?", (order_id,))
    product_id, qty_sold = cur.fetchone()

    # 2. Снижаем остаток товара на складе
    cur.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
    current_qty = cur.fetchone()[0]
    new_qty = max(current_qty - qty_sold, 0)
    cur.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, product_id))

    # 3. Завершаем заказ
    cur.execute("""
        UPDATE orders
        SET status = 'completed',
            payout = ?,
            paid_to_courier = 1,
            finished_at = datetime('now')
        WHERE id = ?
    """, (payout, order_id))

    # 4. Пополняем баланс курьеру
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (payout, courier_id))

    # 5. Записываем трату
    cur.execute("""
        INSERT INTO expenses (name, amount, date)
        VALUES (?, ?, datetime('now'))
    """, (f"Выплата курьеру #{courier_id} за заказ #{order_id}", payout))

    conn.commit()
    conn.close()
    await state.clear()

    await message.answer("✅ Выплата курьеру подтверждена.\nБаланс пополнен и заказ завершён.")

    try:
        await message.bot.send_message(
            courier_id,
            f"✅ Выплата за заказ #{order_id} подтверждена.\n💰 Начислено: {payout} ₽",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👍 Отлично", callback_data="dismiss_message")]
            ])
        )
    except Exception as e:
        print(f"❌ Не удалось отправить курьеру: {e}")


@router.callback_query(F.data == "dismiss_message")
async def dismiss_temp_message(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"❌ Не удалось удалить сообщение: {e}")