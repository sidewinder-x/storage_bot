from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from keyboards.product_kb import get_stock_menu_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states.product_states import AddProductStates
from database import get_db
from keyboards.menu import get_main_menu_kb
from states.product_states import PurchaseProductStates
from states.product_states import SellProductStates
from datetime import datetime
router = Router()

async def save_product_and_finish(message: Message, state: FSMContext):
    data = await state.get_data()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, quantity, buy_price, sell_price, photo) VALUES (?, ?, ?, ?, ?)",
        (data["name"], data["quantity"], data["buy_price"], data["sell_price"], data.get("photo"))
    )
    conn.commit()
    conn.close()

    await message.answer(
        f"✅ Товар <b>{data['name']}</b> добавлен в склад!",
        reply_markup=get_main_menu_kb(),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "menu_stock")
async def stock_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦*Склад*\n\n"
        "Управляй своими товарами в этом разделе:",
        reply_markup=get_stock_menu_kb(),
        parse_mode = "Markdown"
    )

@router.callback_query(F.data == "stock_back")
async def stock_back(callback: CallbackQuery):
    from keyboards.menu import get_main_menu_kb
    await callback.message.edit_text(
        "*🤖 Главное меню*\n\n"
        "📦 **Склад** — управление товарами и остатками\n"
        "💰 **Финансы** — учёт выручки, прибыли и расходов\n"
        "🚚 **Курьеры** — задания и контроль\n"
        "📊 **Отчёты** — аналитика по продажам и закупкам\n\n"
        "👇 *Выберите раздел:*",
        reply_markup=get_main_menu_kb(),
        parse_mode="Markdown"
    )
# Нажатие на "➕ Добавить товар"
@router.callback_query(F.data == "stock_add")
async def start_add_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🏷️ Введите название товара:")
    await state.set_state(AddProductStates.name)

# Получаем название
@router.message(AddProductStates.name)
async def get_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🔢 Введите количество:")
    await state.set_state(AddProductStates.quantity)

# Получаем количество
@router.message(AddProductStates.quantity)
async def get_product_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")
    await state.update_data(quantity=int(message.text))
    await message.answer("💸 Введите закупочную цену:")
    await state.set_state(AddProductStates.buy_price)

# Получаем закупочную цену
@router.message(AddProductStates.buy_price)
async def get_buy_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")
    await state.update_data(buy_price=int(message.text))
    await message.answer("💰 Введите цену продажи:")
    await state.set_state(AddProductStates.sell_price)

# Получаем цену продажи и сохраняем
@router.message(AddProductStates.sell_price)
async def get_sell_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")

    await state.update_data(sell_price=int(message.text))

    # Кнопка "Пропустить фото"
    skip_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить фото", callback_data="skip_product_photo")]
    ])

    # Единое сообщение с кнопкой
    await message.answer(
        "📷 Отправьте фото товара (или нажмите 'Пропустить'):\n\n"
        "Вы можете отправить фото или пропустить этот шаг:",
        reply_markup=skip_button
    )

    await state.set_state(AddProductStates.photo)

@router.message(AddProductStates.photo)
async def get_product_photo(message: Message, state: FSMContext):
    if not message.photo:
        return await message.answer("❗ Отправьте изображение товара.")

    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await save_product_and_finish(message, state)
@router.callback_query(F.data == "skip_product_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await save_product_and_finish(callback.message, state)
@router.callback_query(F.data == "stock_view")
async def view_stock(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, quantity, buy_price, sell_price FROM products")
    products = cur.fetchall()
    conn.close()

    if not products:
        await callback.message.edit_text("📦 На складе пока пусто.", reply_markup=get_stock_menu_kb())
        return

    text = "📋 <b>Остатки на складе:</b>\n\n"
    for name, qty, buy, sell in products:
        profit_per_unit = sell - buy
        total_profit = profit_per_unit * qty
        text += (
            f"📦 <b>{name}</b>\n"
            f"• Кол-во: <b>{qty}</b>\n"
            f"• Закуп: {buy} ₽ | Продажа: {sell} ₽\n"
            f"• Потенц. прибыль: <b>{total_profit} ₽</b>\n\n"
        )

    await callback.message.edit_text(text, reply_markup=get_stock_menu_kb())


# Начало продажи
@router.callback_query(F.data == "stock_sale")
async def start_sale(callback: CallbackQuery, state: FSMContext):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products")
    products = cur.fetchall()
    conn.close()

    if not products:
        await callback.message.edit_text("❗ На складе нет товаров для продажи.", reply_markup=get_stock_menu_kb())
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=name, callback_data=f"sell_{prod_id}")]
                            for prod_id, name in products
                        ] + [[InlineKeyboardButton(text="◀️ Назад", callback_data="menu_stock")]]
    )

    await callback.message.edit_text("🛒 Выберите товар для продажи:", reply_markup=kb)
    await state.set_state(SellProductStates.choosing_product)


# Выбор товара
@router.callback_query(SellProductStates.choosing_product, F.data.startswith("sell_"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=prod_id)
    await callback.message.edit_text("🔢 Введите количество проданных единиц:")
    await state.set_state(SellProductStates.entering_quantity)


# Ввод количества и завершение
@router.message(SellProductStates.entering_quantity)
async def process_sale_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")

    qty = int(message.text)
    data = await state.get_data()
    product_id = data["product_id"]

    conn = get_db()
    cur = conn.cursor()

    # Проверка текущего остатка
    cur.execute("SELECT name, quantity FROM products WHERE id = ?", (product_id,))
    result = cur.fetchone()

    if not result:
        await message.answer("❗ Товар не найден.")
        await state.clear()
        return

    name, current_qty = result

    if qty > current_qty:
        await message.answer(f"❗ На складе только {current_qty} шт. Укажи меньше.")
        return

    # Обновляем склад
    new_qty = current_qty - qty
    cur.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, product_id))

    # Записываем продажу
    cur.execute(
        "INSERT INTO sales (product_id, quantity, date) VALUES (?, ?, ?)",
        (product_id, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()

    from keyboards.menu import get_main_menu_kb
    await message.answer(
        f"✅ Продажа <b>{name}</b> на {qty} шт. зарегистрирована.",
        reply_markup=get_main_menu_kb()
    )
    await state.clear()

from states.product_states import PurchaseProductStates

# Начало закупки
@router.callback_query(F.data == "stock_purchase")
async def start_purchase(callback: CallbackQuery, state: FSMContext):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products")
    products = cur.fetchall()
    conn.close()

    if not products:
        await callback.message.edit_text("❗ Нет товаров для закупки.", reply_markup=get_stock_menu_kb())
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"purchase_{prod_id}")]
            for prod_id, name in products
        ] + [[InlineKeyboardButton(text="◀️ Назад", callback_data="menu_stock")]]
    )

    await callback.message.edit_text("📥 Выберите товар для закупки:", reply_markup=kb)
    await state.set_state(PurchaseProductStates.choosing_product)

# Выбор товара
@router.callback_query(PurchaseProductStates.choosing_product, F.data.startswith("purchase_"))
async def choose_product_for_purchase(callback: CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split("_")[1])
    await state.update_data(product_id=prod_id)
    await callback.message.edit_text("🔢 Введите количество для закупки:")
    await state.set_state(PurchaseProductStates.entering_quantity)

# Ввод количества
@router.message(PurchaseProductStates.entering_quantity)
async def get_purchase_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")
    await state.update_data(quantity=int(message.text))
    await message.answer("💰 Введите цену за единицу:")
    await state.set_state(PurchaseProductStates.entering_price)

# Завершение закупки
@router.message(PurchaseProductStates.entering_price)
async def complete_purchase(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❗ Введите число.")
    data = await state.update_data(price=int(message.text))
    data = await state.get_data()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, quantity FROM products WHERE id = ?", (data["product_id"],))
    product = cur.fetchone()

    if not product:
        await message.answer("❗ Товар не найден.")
        await state.clear()
        return

    name, current_qty = product
    new_qty = current_qty + data["quantity"]

    # Обновляем количество и цену закупки
    cur.execute("UPDATE products SET quantity = ?, buy_price = ? WHERE id = ?",
                (new_qty, data["price"], data["product_id"]))

    # Записываем трату
    total_cost = data["quantity"] * data["price"]
    cur.execute(
        "INSERT INTO expenses (name, amount, date) VALUES (?, ?, ?)",
        (f"{name} (закупка)", total_cost, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()

    from keyboards.menu import get_main_menu_kb
    await message.answer(
        f"📥 Закупка <b>{name}</b> на {data['quantity']} шт. завершена.\n"
        f"💸 Потрачено: <b>{total_cost} ₽</b>",
        reply_markup=get_main_menu_kb()
    )
    await state.clear()

@router.callback_query(F.data == "stock_delete")
async def start_delete(callback: CallbackQuery):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products")
    products = cur.fetchall()
    conn.close()

    if not products:
        await callback.message.edit_text("❗ Нет товаров для удаления.", reply_markup=get_stock_menu_kb())
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🗑 {name}", callback_data=f"delete_{prod_id}")]
            for prod_id, name in products
        ] + [[InlineKeyboardButton(text="◀️ Назад", callback_data="menu_stock")]]
    )

    await callback.message.edit_text("❌ Выберите товар для удаления:", reply_markup=kb)

@router.callback_query(F.data.startswith("delete_product_"))
async def confirm_delete(callback: CallbackQuery):
    prod_id = int(callback.data.split("_")[1])

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM products WHERE id = ?", (prod_id,))
    product = cur.fetchone()

    if not product:
        await callback.message.edit_text("❗ Товар уже удалён или не найден.", reply_markup=get_stock_menu_kb())
        return

    name = product[0]
    cur.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()

    await callback.message.edit_text(
        f"🗑 Товар <b>{name}</b> удалён со склада.",
        reply_markup=get_stock_menu_kb()
    )