import asyncio, json, logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, PORT, API_SECRET, LOG_CHANNEL, ADMIN_ID
import database as db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher(storage=MemoryStorage())

from handlers import start, admin, payment
dp.include_router(start.router)
dp.include_router(payment.router)
dp.include_router(admin.router)

def ok(data=None):
    return web.Response(content_type="application/json",
        text=json.dumps({"ok":True,**({"data":data} if data else {})}))

def err(msg, status=400):
    return web.Response(status=status, content_type="application/json",
        text=json.dumps({"ok":False,"error":msg}))

def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Secret"
    return r

def auth(req): return req.headers.get("X-Secret") == API_SECRET

async def handle_options(req): return cors(web.Response(status=204))

async def api_products(req):
    return cors(ok({"stars":db.get_products("stars"),"premium":db.get_products("premium"),"settings":db.get_all_settings()}))

async def api_order(req):
    if not auth(req): return cors(err("Unauthorized",401))
    try: body = await req.json()
    except: return cors(err("Invalid JSON"))
    for f in ["user_id","product_id","tg_username"]:
        if not body.get(f): return cors(err(f"Missing: {f}"))
    prod = db.get_product(body["product_id"])
    if not prod or not prod["active"]: return cors(err("Product not found"))
    oid = db.add_order(body["user_id"],body.get("username",""),body.get("full_name",""),
        prod["id"],prod["name"],prod["price"],body["tg_username"].lstrip("@"))
    db.upsert_user(body["user_id"],body.get("username",""),body.get("full_name",""))
    caption=(f"🆕 <b>Yangi buyurtma #{oid}</b>\n\n"
        f"👤 {body.get('full_name','?')} (@{body.get('username','?')})\n"
        f"🆔 ID: <code>{body['user_id']}</code>\n"
        f"📦 {prod['name']}\n💰 {prod['price']:,} so'm\n"
        f"📱 Yuborish: @{body['tg_username'].lstrip('@')}")
    kb={"inline_keyboard":[[{"text":"✅ Tasdiqlash","callback_data":f"confirm_{oid}"},{"text":"❌ Rad etish","callback_data":f"reject_{oid}"}]]}
    photo_id = body.get("photo_file_id")
    for chat in [LOG_CHANNEL, ADMIN_ID]:
        try:
            if photo_id: await bot.send_photo(chat_id=chat,photo=photo_id,caption=caption,reply_markup=kb)
            else: await bot.send_message(chat_id=chat,text=caption,reply_markup=kb)
        except Exception as e: log.warning(f"Notify {chat}: {e}")
    return cors(ok({"order_id":oid,"price":prod["price"],"product":prod["name"]}))

async def api_photo(req):
    if not auth(req): return cors(err("Unauthorized",401))
    try:
        data = await req.post()
        photo = data.get("photo"); uid = int(data.get("user_id",0))
        if not photo or not uid: return cors(err("Missing photo or user_id"))
        msg = await bot.send_photo(chat_id=ADMIN_ID,photo=photo.file.read())
        fid = msg.photo[-1].file_id
        await bot.delete_message(chat_id=ADMIN_ID,message_id=msg.message_id)
        return cors(ok({"file_id":fid}))
    except Exception as e: return cors(err(str(e)))

async def api_user_orders(req):
    if not auth(req): return cors(err("Unauthorized",401))
    try: uid=int(req.rel_url.query.get("user_id",0))
    except: return cors(err("Invalid user_id"))
    return cors(ok(db.get_user_orders(uid)))

async def api_stats(req):
    if not auth(req): return cors(err("Unauthorized",401))
    return cors(ok(db.get_stats()))

async def api_price(req):
    if not auth(req): return cors(err("Unauthorized",401))
    body=await req.json(); pid,price=body.get("id"),body.get("price")
    if not pid or not price: return cors(err("Missing id or price"))
    db.update_price(pid,int(price)); return cors(ok())

async def api_broadcast(req):
    if not auth(req): return cors(err("Unauthorized",401))
    body=await req.json(); text=body.get("text","").strip()
    if not text: return cors(err("Empty text"))
    users=db.get_all_user_ids(); sent=failed=0
    for uid in users:
        try: await bot.send_message(uid,text,parse_mode="HTML"); sent+=1
        except: failed+=1
        await asyncio.sleep(0.05)
    return cors(ok({"sent":sent,"failed":failed}))

def make_app():
    app=web.Application()
    app.router.add_route("OPTIONS","/{p:.*}",handle_options)
    app.router.add_get ("/api/products", api_products)
    app.router.add_post("/api/order",    api_order)
    app.router.add_post("/api/photo",    api_photo)
    app.router.add_get ("/api/orders",   api_user_orders)
    app.router.add_get ("/api/stats",    api_stats)
    app.router.add_post("/api/price",    api_price)
    app.router.add_post("/api/broadcast",api_broadcast)
    app.router.add_get ("/",             lambda r:web.Response(text="Stars & Premium API ✅"))
    return app

async def main():
    app=make_app(); runner=web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner,"0.0.0.0",PORT).start()
    log.info(f"✅ API :{PORT}")
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("✅ Bot polling")
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
