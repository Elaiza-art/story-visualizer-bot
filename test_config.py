from config import config

print("🔑 BOT_TOKEN:", config.BOT_TOKEN[:10] + "..." if config.BOT_TOKEN else "❌ Не задан")
print("🌐 API_URL:", config.API_URL)
print("👤 ADMIN_ID:", config.ADMIN_ID)
print("📊 LOG_LEVEL:", config.LOG_LEVEL)