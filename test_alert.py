import telegram
from datetime import datetime

# Configuration
TOKEN = '7339350903:AAHKHlNHiPr-J0U48IYde1oo7n-VxPjfLm0'
CHAT_ID = '1114081526'

# Initialize bot
bot = telegram.Bot(token=TOKEN)

# Test location (example coordinates)
location = {
    'latitude': 28.6139,
    'longitude': 77.2090
}

# Send test alert
try:
    message = f"🔥 TEST FIRE ALERT!\nLocation: https://www.google.com/maps?q={location['latitude']},{location['longitude']}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    bot.send_message(chat_id=CHAT_ID, text=message)
    print("Test alert sent successfully!")
except Exception as e:
    print(f"Error sending alert: {e}") 