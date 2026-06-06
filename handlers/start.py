from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from config import MINI_APP_URL
import database as db

router = Router()

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 Do'konni ochish", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="📋 Buyurtmalarim", callback_data="my_orders"),
         InlineKeyboardButton(text="📞 Aloqa",         callback_data="contact")],
    ])

@router.message(CommandStart())
async def start(msg: Message):
    db.upsert_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.full_name or "")
    await msg.answer(".", reply_markup=ReplyKeyboardRemove())
    await msg.answer(
        f"👋 Salom, <b>{msg.from_user.first_name}</b>!\n\n"
        f"⭐ <b>Stars & Premium Shop</b>\n\n"
        f"{db.get_setting('welcome_text') or 'Stars va Premium arzon narxlarda!'}\n\n"
        "👇 Do'konni ochish uchun tugmani bosing:",
        reply_markup=main_kb()
    )

@router.callback_query(F.data == "contact")
async def contact(cb: CallbackQuery):
    s = db.get_all_settings()
    await cb.message.edit_text(
        f"📞 <b>Aloqa</b>\n\n"
        f"👤 Admin: {s.get('admin_username','@iammeduz')}\n"
        f"📱 Tel: {s.get('phone','+998507121607')}\n"
        f"⏰ Ish vaqti: {s.get('work_hours','09:00 — 00:00')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")]
        ])
    )

@router.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery):
    await cb.message.edit_text(
        f"⭐ <b>Stars & Premium Shop</b>\n\n"
        f"{db.get_setting('welcome_text') or 'Stars va Premium arzon narxlarda!'}\n\n"
        "👇 Do'konni ochish uchun tugmani bosing:",
        reply_markup=main_kb()
    )

@router.callback_query(F.data == "my_orders")
async def my_orders(cb: CallbackQuery):
    orders = db.get_user_orders(cb.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 Do'konni ochish", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")]
    ])
    if not orders:
        return await cb.message.edit_text(
            "📋 <b>Buyurtmalarim</b>\n\nHali hech narsa xarid qilmagansiz.",
            reply_markup=kb
        )
    sm = {"pending":"⏳","done":"✅","cancelled":"❌"}
    text = "📋 <b>Oxirgi buyurtmalar:</b>\n\n"
    for o in orders[:8]:
        text += f"{sm.get(o['status'],'⏳')} #{o['id']} | {o['product']}\n💰 {o['price']:,} so'm | {str(o['created_at'])[:10]}\n\n"
    await cb.message.edit_text(text, reply_markup=kb)
