
import asyncio
import sqlite3
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)

import asyncio
import sqlite3
import json
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 584192076  # Keyin o'z Telegram ID raqamingizni yozamiz

bot = Bot(token=TOKEN)
dp = Dispatcher()

pending_orders = {}
pending_price_updates = {}
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Mahsulot qo‘shish")],
        [KeyboardButton(text="📦 Mahsulotlar ro‘yxati")],
        [KeyboardButton(text="🗑 Mahsulot o‘chirish")],
        [KeyboardButton(text="💰 Narxni o‘zgartirish")]
    ],
    resize_keyboard=True
)

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz.")
        return

    await message.answer(
        "⚙️ DMART MARKET ADMIN PANEL",
        reply_markup=admin_menu
    )

@dp.message(F.text == "📦 Mahsulotlar ro‘yxati")
async def product_list(message: Message):
    print("ADMIN LIST BOSILDI")

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz.")
        return

    try:
        con = database()
        products = con.execute(
            "SELECT id, name, price FROM products"
        ).fetchall()
        con.close()

        if not products:
            await message.answer("Hozircha mahsulotlar yo‘q.")
            return

        text = "📦 MAHSULOTLAR RO‘YXATI\n\n"

        for p in products:
            text += f"🆔 {p[0]} | {p[1]}\n💰 {p[2]:,} so‘m\n\n"

        await message.answer(text)

    except Exception as e:
        await message.answer(f"Xatolik: {e}")
    
def database():
    con = sqlite3.connect("dmart.db")
    con.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            description TEXT,
            photo TEXT
        )
    """)

    try:
        con.execute("ALTER TABLE products ADD COLUMN photo TEXT")
    except sqlite3.OperationalError:
        pass

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT, phone TEXT, product TEXT
        )
    """)
    con.commit()
    return con


menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Katalog")],
        [KeyboardButton(text="🛒 Onlayn do‘kon",
                        web_app=WebAppInfo(url="https://dmart-market.onrender.com"))],
        [KeyboardButton(text="📦 Buyurtma berish")],
        [KeyboardButton(text="☎️ Aloqa")]
    ],
    resize_keyboard=True
)



@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Assalomu alaykum!\n"
        "🛍 DMART MARKET ga xush kelibsiz!\n"
        "Namangan bo'ylab onlayn bozor.",
        reply_markup=menu
    )


@dp.message(F.text == "🛍 Katalog")
async def catalog(message: Message):
    con = database()
    products = con.execute(
        "SELECT id,name,price,description,photo FROM products"
    ).fetchall()
    con.close()

    if not products:
        await message.answer("Hozircha mahsulotlar mavjud emas.")
        return

    for p in products:
        caption = (
            f"🛍 {p[1]}\n"
            f"💰 Narxi: {p[2]:,} so'm\n"
            f"📝 {p[3]}\n"
            f"Buyurtma uchun: /order {p[0]}"
        )

        if p[4]:
            await message.answer_photo(
                photo=p[4],
                caption=caption
            )
        else:
            await message.answer(caption)


@dp.message(Command("add"))
async def add_product(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        data = message.text.split("|")
        name = data[1].strip()
        price = int(data[2].strip())
        description = data[3].strip()

        con = database()
        con.execute(
            "INSERT INTO products(name,price,description,photo) VALUES(?,?,?,?)",
            (name, price, description, None)
        )
        con.commit()
        con.close()

        await message.answer("✅ Mahsulot qo'shildi! Endi rasmini yuboring.")
    except Exception:
        await message.answer(
            "Format:\n/add | Mahsulot | Narx | Tavsif"
        )

@dp.message(F.photo)
async def save_product_photo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    photo_id = message.photo[-1].file_id

    con = database()
    product = con.execute(
        "SELECT id FROM products ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if product:
        con.execute(
            "UPDATE products SET photo=? WHERE id=?",
            (photo_id, product[0])
        )
        con.commit()
        await message.answer("✅ Mahsulot rasmi saqlandi!")
    else:
        await message.answer("Avval mahsulot qo‘shing.")

    con.close()

@dp.message(Command("order"))
async def order(message: Message):
    try:
        pid = int(message.text.split()[1])
        con = database()
        product = con.execute(
            "SELECT name FROM products WHERE id=?", (pid,)
        ).fetchone()
        con.close()

        if not product:
            await message.answer("Mahsulot topilmadi.")
            return

        await message.answer(
            f"📦 {product[0]}\n"
            "Buyurtma uchun administratorga yozing: @DmartNamanganBot"
        )
    except:
        await message.answer("Mahsulot raqamini kiriting: /order 1")
@dp.message(F.web_app_data)
async def web_app_order(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        items = data.get("items", [])
        total = int(data.get("total", 0))

        if not items:
            await message.answer("Savatchangiz bo‘sh!")
            return

        text = "🛒 YANGI BUYURTMA!\n\n"

        for item in items:
            name = item.get("name", "Mahsulot")
            price = int(item.get("price", 0))
            quantity = int(item.get("quantity", 1))
            text += f"📦 {name}\n🔢 Soni: {quantity}\n💰 Narxi: {price * quantity:,} so'm\n\n"

        text += f"💵 Jami: {total:,} so'm"

        pending_orders[message.from_user.id] = {
            "order": text,
            "stage": "phone"
        }

        await message.answer(
            "📞 Telefon raqamingizni yuboring.\n"
            "Masalan: +998901234567"
        )

    except Exception:
        await message.answer("❌ Buyurtmada xatolik yuz berdi.")
    
@dp.message(F.text == "☎️ Aloqa")
async def contact(message: Message):
    await message.answer("☎️ DMART MARKET\nTelegram: @DmartNamanganBot")

@dp.message(
    F.text,
    lambda message: message.from_user.id in pending_orders
)
async def collect_order_details(message: Message):
    user_id = message.from_user.id

    if user_id not in pending_orders:
        return

    stage = pending_orders[user_id]["stage"]

    if stage == "phone":
        phone = message.text.strip()
        digits = "".join(ch for ch in phone if ch.isdigit())

        if len(digits) < 9:
            await message.answer("Telefon raqam noto‘g‘ri. Masalan: +998901234567")
            return

        pending_orders[user_id]["phone"] = phone
        pending_orders[user_id]["stage"] = "address"

        await message.answer("📍 Yetkazib berish manzilingizni yuboring.")
        return

    if stage == "address":
        address = message.text.strip()

        if len(address) < 5:
            await message.answer("Manzilni to‘liqroq yozing.")
            return

        order = pending_orders.pop(user_id)

        final_text = (
            f"{order['order']}\n\n"
            f"👤 Xaridor: {message.from_user.full_name}\n"
            f"📞 Telefon: {order['phone']}\n"
            f"📍 Manzil: {address}\n"
            f"🆔 Telegram ID: {user_id}"
        )

        await bot.send_message(ADMIN_ID, final_text)
        await message.answer("✅ Buyurtmangiz yuborildi! Rahmat.")

@dp.message(F.text == "💰 Narxni o‘zgartirish")
async def change_price(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "Mahsulot ID va yangi narxni yuboring.\n"
        "Masalan: 2 | 250000"
    )


@dp.message(
    F.text.regexp(r"^\d+\s*\|\s*\d+$"),
    lambda message: message.from_user.id == ADMIN_ID
)
async def save_new_price(message: Message):
    try:
        product_id, new_price = map(
            int, message.text.split("|")
        )

        con = database()
        product = con.execute(
            "SELECT name FROM products WHERE id=?",
            (product_id,)
        ).fetchone()

        if not product:
            con.close()
            await message.answer("❌ Mahsulot topilmadi.")
            return

        con.execute(
            "UPDATE products SET price=? WHERE id=?",
            (new_price, product_id)
        )
        con.commit()
        con.close()

        await message.answer(
            f"✅ {product[0]} narxi yangilandi!\n"
            f"💰 Yangi narx: {new_price:,} so‘m"
        )

    except Exception:
        await message.answer("❌ Xatolik yuz berdi.")
        
async def main():
    database()
    await dp.start_polling(bot)

@dp.message(F.text == "🗑 Mahsulot o‘chirish")
async def delete_product(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "O‘chirmoqchi bo‘lgan mahsulot ID raqamini yuboring.\n"
        "Masalan: 2"
    )

@dp.message(
    F.text.regexp(r"^\d+$"),
    lambda message: message.from_user.id == ADMIN_ID
)
async def confirm_delete_product(message: Message):
    product_id = int(message.text)

    con = database()
    product = con.execute(
        "SELECT name FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if not product:
        con.close()
        await message.answer("❌ Bunday mahsulot topilmadi.")
        return

    con.execute("DELETE FROM products WHERE id=?", (product_id,))
    con.commit()
    con.close()

    await message.answer(f"✅ {product[0]} o‘chirildi!")
    
if __name__ == "__main__":
    asyncio.run(main())
