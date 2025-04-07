import telegram

# Your bot token
TOKEN = '7339350903:AAHKHlNHiPr-J0U48IYde1oo7n-VxPjfLm0'

# Initialize the bot
bot = telegram.Bot(token=TOKEN)

# Get updates
updates = bot.get_updates()
print("Updates:", updates)

# If no updates, try sending a test message
if not updates:
    print("\nNo updates found. Please send a message to your bot and run this script again.")
    print("Bot username:", bot.get_me().username)
    print("Please message the bot and then run this script again.") 