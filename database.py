import sqlite3
from config import PRODUCTS

DB = "shop.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT, full_name TEXT,
        product_id TEXT, product TEXT, price INTEGER,
        tg_username TEXT, status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products(
        id TEXT PRIMARY KEY, name TEXT, category TEXT,
        price INTEGER, qty INTEGER DEFAULT 0,
        months INTEGER DEFAULT 0, active INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, username TEXT,
        full_name TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    for cat, items in PRODUCTS.items():
        for p in items:
            c.execute("INSERT OR IGNORE INTO products VALUES(?,?,?,?,?,?,1)",
                (p["id"],p["name"],cat,p["price"],p.get("qty",0),p.get("months",0)))
    for k,v in [("payment_card","5614 6822 1207 6758"),("payment_name","Zayniddinov Sirojiddin"),
                ("admin_username","@iammeduz"),("phone","+998507121607"),
                ("work_hours","09:00 — 00:00"),("welcome_text","Stars va Premium arzon narxlarda! 🌟")]:
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)",(k,v))
    conn.commit(); conn.close()

def get_products(cat=None):
    conn=get_conn(); c=conn.cursor()
    if cat: c.execute("SELECT * FROM products WHERE category=? AND active=1 ORDER BY price",(cat,))
    else:   c.execute("SELECT * FROM products WHERE active=1 ORDER BY category,price")
    r=[dict(x) for x in c.fetchall()]; conn.close(); return r

def get_all_products():
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT * FROM products ORDER BY category,price")
    r=[dict(x) for x in c.fetchall()]; conn.close(); return r

def get_product(pid):
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?",(pid,))
    r=c.fetchone(); conn.close(); return dict(r) if r else None

def update_price(pid,price):
    conn=get_conn(); conn.execute("UPDATE products SET price=? WHERE id=?",(price,pid)); conn.commit(); conn.close()

def toggle_product(pid):
    conn=get_conn(); conn.execute("UPDATE products SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?",(pid,)); conn.commit(); conn.close()

def add_order(user_id,username,full_name,product_id,product,price,tg_username):
    conn=get_conn(); c=conn.cursor()
    c.execute("INSERT INTO orders(user_id,username,full_name,product_id,product,price,tg_username) VALUES(?,?,?,?,?,?,?)",
        (user_id,username,full_name,product_id,product,price,tg_username))
    oid=c.lastrowid; conn.commit(); conn.close(); return oid

def get_orders(status=None,limit=50):
    conn=get_conn(); c=conn.cursor()
    if status: c.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at DESC LIMIT ?",(status,limit))
    else:      c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?",(limit,))
    r=[dict(x) for x in c.fetchall()]; conn.close(); return r

def get_order(oid):
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT * FROM orders WHERE id=?",(oid,))
    r=c.fetchone(); conn.close(); return dict(r) if r else None

def get_user_orders(uid,limit=10):
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?",(uid,limit))
    r=[dict(x) for x in c.fetchall()]; conn.close(); return r

def update_order(oid,status):
    conn=get_conn(); conn.execute("UPDATE orders SET status=? WHERE id=?",(status,oid)); conn.commit(); conn.close()

def get_stats():
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT COUNT(*),COALESCE(SUM(price),0) FROM orders WHERE status='done'"); done,inc=c.fetchone()
    c.execute("SELECT COUNT(*) FROM orders WHERE status='pending'"); pend=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders"); total=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users"); users=c.fetchone()[0]
    conn.close(); return {"done":done,"income":inc,"pending":pend,"total":total,"users":users}

def get_setting(key):
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?",(key,))
    r=c.fetchone(); conn.close(); return r["value"] if r else None

def set_setting(key,value):
    conn=get_conn(); conn.execute("INSERT OR REPLACE INTO settings VALUES(?,?)",(key,value)); conn.commit(); conn.close()

def get_all_settings():
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT * FROM settings"); r={x["key"]:x["value"] for x in c.fetchall()}; conn.close(); return r

def upsert_user(user_id,username,full_name):
    conn=get_conn(); conn.execute("INSERT OR IGNORE INTO users(user_id,username,full_name) VALUES(?,?,?)",(user_id,username or "",full_name or "")); conn.commit(); conn.close()

def get_all_user_ids():
    conn=get_conn(); c=conn.cursor()
    c.execute("SELECT user_id FROM users"); r=[x["user_id"] for x in c.fetchall()]; conn.close(); return r

init_db()
