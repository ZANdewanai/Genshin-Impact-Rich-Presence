"""Quick script to clear Discord Rich Presence."""
import time
import pypresence as discord

DISC_APP_ID = "944346292568596500"

print("Clearing Discord Rich Presence...")
try:
    rpc = discord.Presence(DISC_APP_ID)
    rpc.connect()
    rpc.clear()  # Clear the presence
    print("✅ Discord presence cleared!")
    time.sleep(1)
    rpc.close()
except discord.exceptions.DiscordNotFound:
    print("❌ Discord not running")
except Exception as e:
    print(f"⚠️ Error: {e}")
