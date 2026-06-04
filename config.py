import os
BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "5087957447"))
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "@tgpremium_stars")
API_SECRET  = os.getenv("API_SECRET", "change_this_secret")
PORT        = int(os.getenv("PORT", "8000"))
MINI_APP_URL= os.getenv("MINI_APP_URL", "https://meduztrade-maker.github.io/mini_app")
PRODUCTS = {
    "stars": [
        {"id":"s50",  "name":"⭐ 50 Stars",    "price":11000,  "qty":50  },
        {"id":"s75",  "name":"⭐ 75 Stars",    "price":16500,  "qty":75  },
        {"id":"s100", "name":"⭐ 100 Stars",   "price":22000,  "qty":100 },
        {"id":"s150", "name":"⭐ 150 Stars",   "price":33000,  "qty":150 },
        {"id":"s250", "name":"⭐ 250 Stars",   "price":55000,  "qty":250 },
        {"id":"s350", "name":"⭐ 350 Stars",   "price":77000,  "qty":350 },
        {"id":"s500", "name":"⭐ 500 Stars",   "price":110000, "qty":500 },
        {"id":"s750", "name":"⭐ 750 Stars",   "price":164000, "qty":750 },
        {"id":"s1k",  "name":"⭐ 1,000 Stars", "price":219000, "qty":1000},
        {"id":"s1h5", "name":"⭐ 1,500 Stars", "price":329000, "qty":1500},
        {"id":"s2h5", "name":"⭐ 2,500 Stars", "price":548000, "qty":2500},
        {"id":"s5k",  "name":"⭐ 5,000 Stars", "price":1095000,"qty":5000},
    ],
    "premium": [
        {"id":"p3",  "name":"💎 Premium 3 oy",  "price":175000, "months":3 },
        {"id":"p6",  "name":"💎 Premium 6 oy",  "price":234000, "months":6 },
        {"id":"p12", "name":"💎 Premium 1 yil", "price":423000, "months":12},
    ]
}
