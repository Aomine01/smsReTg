"""
Quick test script to verify Telegram API credentials.
This tests the credentials without requiring phone number authentication.
"""
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os

async def test_api_credentials():
    """Test if API credentials are valid."""
    load_dotenv()
    
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print(f"Testing API credentials:")
    print(f"  API ID: {api_id}")
    print(f"  API Hash: {api_hash[:10]}...{api_hash[-10:]}")
    print()
    
    try:
        # Create a temporary client
        client = TelegramClient('test_session', api_id, api_hash)
        
        print("Attempting connection to Telegram servers...")
        await client.connect()
        
        if client.is_connected():
            print("✅ SUCCESS: Connected to Telegram servers!")
            print("✅ API credentials are VALID")
            print()
            print("Your API credentials are correct.")
            print("The issue is likely with:")
            print("  1. Phone number format")
            print("  2. Code delivery (check Telegram app)")
            print("  3. Account restrictions")
        else:
            print("❌ FAILED: Could not connect to Telegram")
            print("API credentials may be invalid.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Possible issues:")
        print("  1. API credentials are invalid")
        print("  2. Network connection problem")
        print("  3. Telegram servers are down")
    finally:
        await client.disconnect()
        # Clean up test session
        if os.path.exists('test_session.session'):
            os.remove('test_session.session')

if __name__ == "__main__":
    asyncio.run(test_api_credentials())
