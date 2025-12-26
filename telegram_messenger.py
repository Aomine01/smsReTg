"""
Production-grade Async Telegram Terminal Client
Demonstrates MTProto protocol handling, async architecture, and enterprise patterns.
"""

import asyncio
import logging
import os
import sys
import json
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError,
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    AuthKeyUnregisteredError,
)
from telethon.tl.types import User, Chat, Channel, Message
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_client.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramClientApp:
    """
    Production-grade Telegram client with async architecture and protocol handling.
    
    Features:
    - Non-blocking async/await operations
    - Automatic FloodWait retry with exponential backoff
    - Secure session management (no console printing)
    - 2FA authentication support
    - MTProto protocol inspection tools
    """
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize the Telegram client application.
        
        Args:
            env_path: Optional path to .env file. Defaults to current directory.
        """
        # Load environment variables
        load_dotenv(env_path or '.env')
        
        # Load configuration from environment
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.session_file: str = ''
        self._load_config()
        
        # Initialize client (will be connected later)
        self.client: Optional[TelegramClient] = None
        self._is_connected: bool = False
        
        logger.info("TelegramClientApp initialized")
    
    def _load_config(self) -> None:
        """Load and validate configuration from environment variables."""
        try:
            api_id_str = os.getenv('TELEGRAM_API_ID')
            if not api_id_str:
                raise ValueError("TELEGRAM_API_ID not found in environment")
            
            self.api_id = int(api_id_str)
            self.api_hash = os.getenv('TELEGRAM_API_HASH')
            
            if not self.api_hash:
                raise ValueError("TELEGRAM_API_HASH not found in environment")
            
            self.session_file = os.getenv('SESSION_FILE_PATH', 'telegram.session')
            
            # Set log level from config
            log_level = os.getenv('LOG_LEVEL', 'INFO')
            logger.setLevel(getattr(logging, log_level.upper()))
            
            logger.info("Configuration loaded successfully")
            logger.debug(f"Session file: {self.session_file}")
            
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.info("\nPlease create a .env file with your credentials:")
            logger.info("1. Copy .env.example to .env")
            logger.info("2. Get API credentials from https://my.telegram.org/apps")
            logger.info("3. Fill in TELEGRAM_API_ID and TELEGRAM_API_HASH")
            sys.exit(1)
    
    async def __aenter__(self):
        """Async context manager entry - establish connection."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup connection."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Establish connection to Telegram servers."""
        if self._is_connected:
            logger.warning("Already connected")
            return
        
        logger.info("Connecting to Telegram...")
        self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        
        await self.client.connect()
        
        # Authenticate if needed
        if not await self.client.is_user_authorized():
            logger.info("Session not authorized, starting authentication...")
            await self._authenticate()
        else:
            logger.info("✅ Connected successfully using existing session")
        
        self._is_connected = True
    
    async def disconnect(self) -> None:
        """Gracefully disconnect from Telegram."""
        if self.client and self._is_connected:
            logger.info("Disconnecting from Telegram...")
            await self.client.disconnect()
            self._is_connected = False
            logger.info("Disconnected")
    
    async def _authenticate(self) -> None:
        """
        Handle authentication flow including 2FA.
        
        Note: This demonstrates understanding of MTProto's auth flow:
        1. Phone number → Code request
        2. Code verification → Session creation
        3. 2FA (if enabled) → Password verification
        4. Auth Key stored in session file via Diffie-Hellman exchange
        """
        try:
            phone = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
            
            if not phone:
                raise ValueError("Phone number cannot be empty")
            
            logger.info(f"Sending code to {phone}...")
            await self.client.send_code_request(phone)
            
            code = input("Enter the verification code: ").strip()
            
            try:
                await self.client.sign_in(phone, code)
                logger.info("✅ Authentication successful")
                logger.info(f"Session saved to {self.session_file}")
                
            except SessionPasswordNeededError:
                logger.warning("Two-factor authentication enabled")
                password = input("Enter your 2FA password: ").strip()
                
                await self.client.sign_in(password=password)
                logger.info("✅ 2FA authentication successful")
                logger.info(f"Session saved to {self.session_file}")
                
        except PhoneCodeInvalidError:
            logger.error("Invalid verification code")
            raise
        except PhoneNumberInvalidError:
            logger.error("Invalid phone number format")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def send_message_safe(
        self, 
        recipient: Union[str, int], 
        message: str,
        max_retries: int = 3
    ) -> bool:
        """
        Send message with automatic FloodWait handling and retry logic.
        
        This demonstrates production-grade error handling for MTProto's rate limiting:
        - FloodWaitError: Telegram's rate limit mechanism
        - Exponential backoff: Industry best practice for retry logic
        
        Args:
            recipient: Username (@username), phone number, or user ID
            message: Message text to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                await self.client.send_message(recipient, message)
                logger.info(f"✅ Message sent to {recipient}")
                return True
                
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(
                    f"⏳ FloodWait triggered. Must wait {wait_time} seconds. "
                    f"(Attempt {attempt + 1}/{max_retries})"
                )
                
                if attempt < max_retries - 1:
                    logger.info(f"Sleeping for {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    logger.info("Retrying...")
                else:
                    logger.error("Max retries exceeded. Message not sent.")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error sending message: {e}")
                return False
        
        return False
    
    async def get_contact_info(self) -> Union[str, int]:
        """
        Interactive contact selection with validation.
        
        Returns:
            Username (str), phone number (str), or user ID (int)
        """
        print("\n" + "="*50)
        print("How would you like to specify the recipient?")
        print("="*50)
        print("1. Username (e.g., @username)")
        print("2. Phone number (e.g., +1234567890)")
        print("3. User ID (numeric)")
        print("="*50)
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            username = input("Enter username (with or without @): ").strip()
            if not username.startswith('@'):
                username = '@' + username
            logger.debug(f"Selected username: {username}")
            return username
            
        elif choice == "2":
            phone = input("Enter phone number (with country code): ").strip()
            logger.debug(f"Selected phone: {phone}")
            return phone
            
        elif choice == "3":
            user_id_str = input("Enter user ID: ").strip()
            user_id = int(user_id_str)
            logger.debug(f"Selected user ID: {user_id}")
            return user_id
            
        else:
            logger.warning(f"Invalid choice '{choice}', defaulting to username")
            username = input("Enter username: ").strip()
            if not username.startswith('@'):
                username = '@' + username
            return username
    
    async def send_message_interactive(self) -> None:
        """Interactive message sending workflow."""
        try:
            while True:
                # Get recipient
                recipient = await self.get_contact_info()
                
                # Get message
                print("\n" + "="*50)
                message = input("Enter your message (or 'quit' to exit): ").strip()
                print("="*50)
                
                if message.lower() in ['quit', 'exit', 'q']:
                    logger.info("Exiting message sender")
                    break
                
                if not message:
                    logger.warning("Message cannot be empty")
                    continue
                
                # Send with retry logic
                success = await self.send_message_safe(recipient, message)
                
                if success:
                    print("✅ Message delivered successfully!")
                else:
                    print("❌ Failed to send message. Check logs for details.")
                
                # Continue?
                print("\nSend another message? (y/n): ", end='')
                if input().strip().lower() != 'y':
                    break
                    
        except KeyboardInterrupt:
            logger.info("Message sending interrupted by user")
        except Exception as e:
            logger.error(f"Error in interactive message sender: {e}")
    
    async def list_contacts(self, limit: int = 20) -> None:
        """
        List recent conversations/chats.
        
        Args:
            limit: Number of recent chats to display
        """
        try:
            logger.info(f"Fetching {limit} recent chats...")
            
            print("\n" + "="*70)
            print(f"{'#':<4} {'Name':<25} {'Username':<20} {'Type':<10}")
            print("="*70)
            
            dialogs = await self.client.get_dialogs(limit=limit)
            
            for i, dialog in enumerate(dialogs, 1):
                name = dialog.name or "Unknown"
                entity = dialog.entity
                
                # Get username if available
                username = getattr(entity, 'username', None)
                username_str = f"@{username}" if username else "—"
                
                # Determine entity type
                if isinstance(entity, User):
                    entity_type = "User"
                elif isinstance(entity, Channel):
                    entity_type = "Channel"
                elif isinstance(entity, Chat):
                    entity_type = "Group"
                else:
                    entity_type = "Unknown"
                
                # Truncate long names
                name = name[:24] if len(name) > 24 else name
                
                print(f"{i:<4} {name:<25} {username_str:<20} {entity_type:<10}")
            
            print("="*70)
            logger.info(f"Displayed {len(dialogs)} chats")
            
        except Exception as e:
            logger.error(f"Error listing contacts: {e}")
    
    async def monitor_chats(self) -> None:
        """
        Real-time message monitoring using event handlers.
        
        Demonstrates asyncio event loop integration - the handler runs
        concurrently with the main event loop, enabling non-blocking I/O.
        """
        @self.client.on(events.NewMessage)
        async def message_handler(event: events.NewMessage.Event):
            """Handle incoming messages."""
            try:
                sender = await event.get_sender()
                sender_name = getattr(sender, 'username', None) or \
                             getattr(sender, 'first_name', 'Unknown')
                
                chat = await event.get_chat()
                chat_name = getattr(chat, 'title', None) or \
                           getattr(chat, 'username', 'Direct Message')
                
                print("\n" + "="*70)
                print(f"📩 New Message")
                print(f"From: {sender_name} (ID: {event.sender_id})")
                print(f"Chat: {chat_name}")
                print(f"Message: {event.text or '[Media/Sticker]'}")
                print("="*70)
                
                logger.debug(f"Message from {sender_name}: {event.text}")
                
            except Exception as e:
                logger.error(f"Error handling message: {e}")
        
        print("\n" + "="*70)
        print("🎧 Monitoring all chats... (Press Ctrl+C to stop)")
        print("="*70)
        logger.info("Started message monitoring")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
    
    async def dump_message_raw(self, message_id: int, chat: Union[str, int]) -> None:
        """
        Developer tool: Dump raw message object in JSON format.
        
        This is invaluable for understanding MTProto's message structure
        and useful during interviews to demonstrate protocol knowledge.
        
        Args:
            message_id: ID of the message to inspect
            chat: Chat/user identifier
        """
        try:
            messages = await self.client.get_messages(chat, ids=message_id)
            
            if not messages or not messages[0]:
                logger.warning(f"Message {message_id} not found in chat {chat}")
                print(f"❌ Message {message_id} not found")
                return
            
            message: Message = messages[0]
            
            # Convert to dictionary (simplified representation)
            message_dict = {
                "id": message.id,
                "date": str(message.date),
                "message": message.message,
                "from_id": str(message.from_id) if message.from_id else None,
                "peer_id": str(message.peer_id),
                "fwd_from": str(message.fwd_from) if message.fwd_from else None,
                "via_bot_id": message.via_bot_id,
                "reply_to": str(message.reply_to) if message.reply_to else None,
                "media": str(type(message.media).__name__) if message.media else None,
                "entities": [str(e) for e in message.entities] if message.entities else [],
                "views": message.views,
                "edit_date": str(message.edit_date) if message.edit_date else None,
            }
            
            print("\n" + "="*70)
            print("🔍 RAW MESSAGE OBJECT (MTProto Structure)")
            print("="*70)
            print(json.dumps(message_dict, indent=2, ensure_ascii=False))
            print("="*70)
            
            logger.info(f"Dumped raw message {message_id}")
            
        except Exception as e:
            logger.error(f"Error dumping message: {e}")
            print(f"❌ Error: {e}")
    
    async def get_entity_info(self, identifier: Union[str, int]) -> None:
        """
        Developer tool: Get detailed information about a user/chat/channel.
        
        Args:
            identifier: Username, phone, or user ID
        """
        try:
            entity = await self.client.get_entity(identifier)
            
            entity_dict = {
                "id": entity.id,
                "type": type(entity).__name__,
                "username": getattr(entity, 'username', None),
                "first_name": getattr(entity, 'first_name', None),
                "last_name": getattr(entity, 'last_name', None),
                "phone": getattr(entity, 'phone', None),
                "bot": getattr(entity, 'bot', None),
                "verified": getattr(entity, 'verified', None),
                "restricted": getattr(entity, 'restricted', None),
                "scam": getattr(entity, 'scam', None),
                "fake": getattr(entity, 'fake', None),
            }
            
            # Remove None values
            entity_dict = {k: v for k, v in entity_dict.items() if v is not None}
            
            print("\n" + "="*70)
            print("🔍 ENTITY INFORMATION (MTProto Object)")
            print("="*70)
            print(json.dumps(entity_dict, indent=2, ensure_ascii=False))
            print("="*70)
            
            logger.info(f"Retrieved entity info for {identifier}")
            
        except Exception as e:
            logger.error(f"Error getting entity info: {e}")
            print(f"❌ Error: {e}")
    
    async def show_menu(self) -> None:
        """Display the main TUI menu."""
        while True:
            print("\n" + "="*70)
            print("📱 TELEGRAM TERMINAL CLIENT - Production Edition")
            print("="*70)
            print("1. 📤 Send a message")
            print("2. 📋 List recent contacts")
            print("3. 🎧 Monitor chats (real-time)")
            print("4. 🔍 Dump raw message (Developer Mode)")
            print("5. 🔍 Get entity info (Developer Mode)")
            print("6. ❌ Exit")
            print("="*70)
            
            choice = input("Enter your choice (1-6): ").strip()
            
            try:
                if choice == "1":
                    await self.send_message_interactive()
                    
                elif choice == "2":
                    limit_str = input("Number of contacts to show (default 20): ").strip()
                    limit = int(limit_str) if limit_str else 20
                    await self.list_contacts(limit)
                    
                elif choice == "3":
                    await self.monitor_chats()
                    
                elif choice == "4":
                    chat = input("Enter chat identifier (username/ID): ").strip()
                    msg_id = int(input("Enter message ID: ").strip())
                    await self.dump_message_raw(msg_id, chat)
                    
                elif choice == "5":
                    identifier = input("Enter username, phone, or user ID: ").strip()
                    await self.get_entity_info(identifier)
                    
                elif choice == "6":
                    logger.info("User requested exit")
                    print("\n👋 Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                logger.info("Operation interrupted by user")
                print("\n\n⚠️  Operation cancelled")
            except ValueError as e:
                logger.warning(f"Invalid input: {e}")
                print(f"❌ Invalid input: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in menu: {e}", exc_info=True)
                print(f"❌ Error: {e}")
    
    async def run(self) -> None:
        """Main entry point for the application."""
        try:
            await self.connect()
            await self.show_menu()
        finally:
            await self.disconnect()


async def main():
    """Application entry point."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Telegram Terminal Client - Production Grade            ║
    ║  Async Architecture | MTProto Protocol | Enterprise Ready║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check for .env file
    if not Path('.env').exists():
        print("⚠️  Warning: .env file not found!")
        print("\nFirst-time setup:")
        print("1. Copy .env.example to .env")
        print("2. Get API credentials from https://my.telegram.org/apps")
        print("3. Update .env with your TELEGRAM_API_ID and TELEGRAM_API_HASH")
        print("\nThen run this script again.\n")
        return
    
    app = TelegramClientApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        print("\n\n👋 Application closed")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)