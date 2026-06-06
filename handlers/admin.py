import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID, MINI_APP_URL
import database as db

router = Router()

class S(StatesGroup):
    broadcast=State(); edit_price=State()
    edit_card=State(); edit_name=State()
    edit_welcome=State(); edit_phone=State(); edit_hours=State()

def iam(uid): return uid == ADMIN_ID

def adm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika",    callback_data="adm_stats"),
         InlineKeyboardButton(text="⏳ Kutayotganlar", callback_data="adm_pending")],
        [InlineKeyboardButton(text="💰 Narxlar",       callback_data="adm_prices"),
         InlineKeyboardButton(text="⚙️ Sozlamalar",   callback_data="adm_settings")],
        [InlineKeyboardButton(text="📢 Xabar yuborish",callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar",callback_data="adm_users")],
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin menyu", callback_data="adm_back")]
    ])

async def panel(t, s=None):
    s = s or db.get_stats()
    txt = (f"🔐 <b>Admin Panel</b>\n\n✅ Bajarilgan: <b>{s['done']}</b> ta\n"
           f"⏳ Kutayotgan: <b>{s['pending']}</b> ta\n💰 Daromad: <b>{s['income']:,} so'm</b>\n"
           f"👥 Foydalanuvchi: <b>{s['users']}</b> ta")
    if isinstance(t, Message): await t.answer(txt, reply_markup=adm_kb())
    else: await t.message.edit_text(txt, reply_markup=adm_kb())

@router.message(Command("admin"))
async def admin_cmd(msg: Message):
    if not iam(msg.from_user.id): return
    await panel(msg)

@router.callback_query(F.data == "adm_back")
async def adm_back(cb: CallbackQuery, state: FSMContext):
    if not iam(cb.from_user.id): return
    await state.clear(); await panel(cb)

@router.callback_query(F.data == "adm_stats")
async def adm_stats(cb: CallbackQuery):
    if not iam(cb.from_user.id): return
    s = db.get_stats()
    await cb.message.edit_text(
        f"📊 <b>Statistika</b>\n\n👥 Foydalanuvchi: <b>{s['users']}</b>\n"
        f"📦 Jami buyurtma: <b>{s['total']}</b>\n✅ Bajarilgan: <b>{s['done']}</b>\n"
        f"⏳ Kutayotgan: <b>{s['pending']}</b>\n\n💰 Jami daromad: <b>{s['income']:,} so'm</b>",
        reply_markup=back_kb())

@router.callback_query(F.data == "adm_pending")
async def adm_pending(cb: CallbackQuery):
    if not iam(cb.from_user.id): return
    ords = db.get_orders(status="pending")
    if not ords:
        return await cb.message.edit_text("⏳ Kutayotgan buyurtma yo'q!", reply_markup=back_kb())
    txt = f"⏳ <b>Kutayotganlar ({len(ords)} ta):</b>\n\n"
    for o in ords[:20]:
        txt += f"#{o['id']} | {o['product']}\n👤 @{o['username']} → @{o['tg_username']}\n💰 {o['price']:,} so'm\n\n"
    await cb.message.edit_text(txt, reply_markup=back_kb())

@router.callback_query(F.data == "adm_prices")
async def adm_prices(cb: CallbackQuery):
    if not iam(cb.from_user.id): return
    rows = [[InlineKeyboardButton(
        text=f"{'✅' if p['active'] else '❌'} {p['name']} — {p['price']:,}",
        callback_data=f"adm_p_{p['id']}")] for p in db.get_all_products()]
    rows.append([InlineKeyboardButton(text="🔙 Admin menyu", callback_data="adm_back")])
    await cb.message.edit_text("💰 <b>Narxlar</b>\n\n✅ Faol | ❌ O'chiq\nBosing — o'zgartiring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(F.data.startswith("adm_p_"))
async def adm_price_detail(cb: CallbackQuery, state: FSMContext):
    if not iam(cb.from_user.id): return
    pid = cb.data[6:]; p = db.get_product(pid)
    await state.update_data(pid=pid); await state.set_state(S.edit_price)
    await cb.message.edit_text(
        f"📦 <b>{p['name']}</b>\n💰 Joriy: <b>{p['price']:,} so'm</b>\n"
        f"Holat: {'✅ Faol' if p['active'] else '❌ O\'chiq'}\n\nYangi narxni yozing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Faol/O'chiq", callback_data=f"adm_tog_{pid}")],
            [InlineKeyboardButton(text="🔙 Narxlar",    callback_data="adm_prices")],
        ]))

@router.message(S.edit_price)
async def save_price(msg: Message, state: FSMContext):
    if not iam(msg.from_user.id): return
    try:
        price = int(msg.text.strip().replace(" ","").replace(",",""))
        data = await state.get_data(); db.update_price(data["pid"], price)
        await state.clear(); await msg.answer(f"✅ Narx yangilandi: <b>{price:,} so'm</b>", reply_markup=adm_kb())
    except: await msg.answer("❌ Faqat raqam kiriting!")

@router.callback_query(F.data.startswith("adm_tog_"))
async def toggle_prod(cb: CallbackQuery, state: FSMContext):
    if not iam(cb.from_user.id): return
    pid = cb.data[8:]; db.toggle_product(pid)
    await state.clear(); p = db.get_product(pid)
    await cb.answer(f"{'✅ Faol' if p['active'] else '❌ O\'chiq'}", show_alert=True)
    await adm_prices(cb)

@router.callback_query(F.data == "adm_settings")
async def adm_settings(cb: CallbackQuery):
    if not iam(cb.from_user.id): return
    s = db.get_all_settings()
    await cb.message.edit_text(
        f"⚙️ <b>Sozlamalar</b>\n\n💳 Karta: <code>{s.get('payment_card','-')}</code>\n"
        f"👤 Ism: {s.get('payment_name','-')}\n📱 Tel: {s.get('phone','-')}\n"
        f"⏰ Ish vaqti: {s.get('work_hours','-')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Karta",         callback_data="adm_s_card"),
             InlineKeyboardButton(text="👤 Karta egasi",   callback_data="adm_s_name")],
            [InlineKeyboardButton(text="📝 Xush kelibsiz", callback_data="adm_s_welcome")],
            [InlineKeyboardButton(text="📱 Telefon",       callback_data="adm_s_phone"),
             InlineKeyboardButton(text="⏰ Ish vaqti",     callback_data="adm_s_hours")],
            [InlineKeyboardButton(text="🔙 Admin menyu",   callback_data="adm_back")],
        ]))

async def _ask(cb, state, st, txt):
    await state.set_state(st)
    await cb.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor", callback_data="adm_settings")]]))

@router.callback_query(F.data=="adm_s_card")
async def sc(cb,state:FSMContext): await _ask(cb,state,S.edit_card,"💳 Yangi karta raqami:")
@router.message(S.edit_card)
async def save_card(msg:Message,state:FSMContext):
    if not iam(msg.from_user.id): return
    db.set_setting("payment_card",msg.text.strip()); await state.clear()
    await msg.answer("✅ Karta yangilandi!", reply_markup=adm_kb())

@router.callback_query(F.data=="adm_s_name")
async def sn(cb,state:FSMContext): await _ask(cb,state,S.edit_name,"👤 Karta egasi ismi:")
@router.message(S.edit_name)
async def save_name(msg:Message,state:FSMContext):
    if not iam(msg.from_user.id): return
    db.set_setting("payment_name",msg.text.strip()); await state.clear()
    await msg.answer("✅ Ism yangilandi!", reply_markup=adm_kb())

@router.callback_query(F.data=="adm_s_welcome")
async def sw(cb,state:FSMContext): await _ask(cb,state,S.edit_welcome,"📝 Yangi xush kelibsiz matni:")
@router.message(S.edit_welcome)
async def save_welcome(msg:Message,state:FSMContext):
    if not iam(msg.from_user.id): return
    db.set_setting("welcome_text",msg.text.strip()); await state.clear()
    await msg.answer("✅ Xush kelibsiz matni yangilandi!", reply_markup=adm_kb())

@router.callback_query(F.data=="adm_s_phone")
async def sph(cb,state:FSMContext): await _ask(cb,state,S.edit_phone,"📱 Yangi telefon raqami:")
@router.message(S.edit_phone)
async def save_phone(msg:Message,state:FSMContext):
    if not iam(msg.from_user.id): return
    db.set_setting("phone",msg.text.strip()); await state.clear()
    await msg.answer("✅ Telefon yangilandi!", reply_markup=adm_kb())

@router.callback_query(F.data=="adm_s_hours")
async def sh(cb,state:FSMContext): await _ask(cb,state,S.edit_hours,"⏰ Ish vaqti (masalan: 09:00 — 00:00):")
@router.message(S.edit_hours)
async def save_hours(msg:Message,state:FSMContext):
    if not iam(msg.from_user.id): return
    db.set_setting("work_hours",msg.text.strip()); await state.clear()
    await msg.answer("✅ Ish vaqti yangilandi!", reply_markup=adm_kb())

@router.callback_query(F.data=="adm_broadcast")
async def adm_bc_start(cb:CallbackQuery,state:FSMContext):
    if not iam(cb.from_user.id): return
    await state.set_state(S.broadcast)
    await cb.message.edit_text("📢 <b>Hammaga xabar yuborish</b>\n\nXabar matnini yozing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor",callback_data="adm_back")]]))

@router.message(S.broadcast)
async def adm_bc_send(msg:Message,state:FSMContext,bot:Bot):
    if not iam(msg.from_user.id): return
    await state.clear()
    users=db.get_all_user_ids(); sent=failed=0
    st=await msg.answer(f"⏳ Yuborilmoqda... 0/{len(users)}")
    for i,uid in enumerate(users):
        try: await bot.send_message(uid,msg.text,parse_mode="HTML"); sent+=1
        except: failed+=1
        if i%15==0:
            try: await st.edit_text(f"⏳ {i}/{len(users)}")
            except: pass
        await asyncio.sleep(0.04)
    await st.edit_text(f"✅ <b>Yuborildi!</b>\n✅ {sent} ta\n❌ {failed} ta", reply_markup=adm_kb())

@router.callback_query(F.data=="adm_users")
async def adm_users(cb:CallbackQuery):
    if not iam(cb.from_user.id): return
    await cb.message.edit_text(f"👥 <b>Foydalanuvchilar</b>\n\nJami: <b>{len(db.get_all_user_ids())}</b> ta",
        reply_markup=back_kb())
