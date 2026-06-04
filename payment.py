from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import ADMIN_ID, MINI_APP_URL
import database as db

router = Router()

def after_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌌 Yana xarid qilish", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton(text="📋 Buyurtmalarim", callback_data="my_orders")],
    ])

async def _check(cb, oid):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("❌ Siz admin emassiz!", show_alert=True); return None
    o = db.get_order(oid)
    if not o: await cb.answer("Buyurtma topilmadi!"); return None
    if o["status"] != "pending":
        await cb.answer("Allaqachon ko'rib chiqilgan!", show_alert=True); return None
    return o

async def _edit(cb, suffix):
    try:
        txt = (cb.message.caption or cb.message.text or "") + suffix
        if cb.message.caption is not None: await cb.message.edit_caption(caption=txt)
        else: await cb.message.edit_text(txt)
    except Exception: pass

@router.callback_query(F.data.startswith("confirm_"))
async def confirm(cb: CallbackQuery, bot: Bot):
    oid = int(cb.data.split("_")[1])
    o = await _check(cb, oid)
    if not o: return
    db.update_order(oid, "done")
    try:
        await bot.send_message(o["user_id"],
            f"✅ <b>Buyurtmangiz bajarildi!</b>\n\n"
            f"🆔 #{oid} | {o['product']}\n"
            f"📱 @{o['tg_username']} ga jo'natildi.\n\nXarid uchun rahmat! 🌟",
            reply_markup=after_kb())
    except Exception: pass
    await _edit(cb, "\n\n✅ <b>TASDIQLANDI</b>")
    await cb.answer("✅ Tasdiqlandi!")

@router.callback_query(F.data.startswith("reject_"))
async def reject(cb: CallbackQuery, bot: Bot):
    oid = int(cb.data.split("_")[1])
    o = await _check(cb, oid)
    if not o: return
    db.update_order(oid, "cancelled")
    admin = db.get_setting("admin_username") or "@iammeduz"
    try:
        await bot.send_message(o["user_id"],
            f"❌ <b>Buyurtma #{oid} rad etildi.</b>\n\n"
            f"To'lov tasdiqlanmadi.\nMuammo bo'lsa: {admin}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta urinish", web_app=WebAppInfo(url=MINI_APP_URL))]
            ]))
    except Exception: pass
    await _edit(cb, "\n\n❌ <b>RAD ETILDI</b>")
    await cb.answer("❌ Rad etildi!")
