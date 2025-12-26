# 📱 Telegram Terminal Client - Production Edition

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Telethon](https://img.shields.io/badge/telethon-1.34+-green.svg)](https://github.com/LonamiWebs/Telethon)
[![Async](https://img.shields.io/badge/async-asyncio-orange.svg)](https://docs.python.org/3/library/asyncio.html)
[![Code Style](https://img.shields.io/badge/code%20style-production-brightgreen.svg)]()

> A robust, fault-tolerant Telegram client designed for high-throughput messaging with automatic FloodWait backoff, concurrent event handling, and MTProto protocol awareness.

## 🎯 The "Why"

This project demonstrates production-grade backend engineering practices suitable for companies like Telegram. It showcases:

- **Async Architecture**: Non-blocking I/O using `asyncio` for concurrent operations
- **Protocol Mastery**: Deep understanding of MTProto's authentication flow, rate limiting, and session management
- **Enterprise Patterns**: Proper error handling, retry logic, logging, and configuration management
- **Test-Driven Development**: Comprehensive test suite with mocking to avoid API rate limits
- **Modern Python**: Type hints (PEP 484), async context managers, and professional code organization

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (TUI)                      │
│  Interactive menu, contact selection, message composition    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              TelegramClientApp (Async Core)                 │
│  • Event Loop Management (asyncio)                          │
│  • Session Management (Diffie-Hellman Auth Key)             │
│  • FloodWait Handler (Exponential Backoff)                  │
│  • 2FA Authentication (SessionPasswordNeededError)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Telethon Library Layer                      │
│  MTProto Protocol Implementation                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Telegram Servers (MTProto)                    │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Key Features

### 🛡️ Resilient
- **FloodWait Auto-Retry**: Automatically sleeps and retries when rate-limited by Telegram
- **Exponential Backoff**: Intelligent retry strategy prevents API bans
- **Network Resilience**: Graceful error handling with detailed logging

### 🔒 Secure
- **Environment-Based Config**: No hardcoded credentials (uses `python-dotenv`)
- **Local Session Encryption**: Auth keys stored in `.session` files, never printed to console
- **2FA Support**: Handles `SessionPasswordNeededError` for password-protected accounts

### ⚡ Async & Non-Blocking
- **Concurrent Event Handling**: Monitor messages while maintaining interactive TUI
- **Async/Await Throughout**: Every network operation is non-blocking
- **Context Manager Protocol**: Proper resource cleanup with `async with`

### 🛠 Developer Tools
- **Raw Message Inspector**: Dump MTProto message objects as JSON
- **Entity Information**: Inspect user/chat/channel metadata
- **Comprehensive Logging**: File + console logging with configurable levels

### 🧪 Production-Ready Testing
- **Unit Test Suite**: `pytest` with async support (`pytest-asyncio`)
- **Mocked Telethon Client**: Tests run without hitting real API
- **Coverage**: FloodWait retry, 2FA flow, session persistence

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Telegram API credentials ([Get them here](https://my.telegram.org/apps))

### Setup with Poetry (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd telegram-terminal-client

# 2. Install Poetry (if not already installed)
pip install poetry

# 3. Install dependencies
poetry install

# 4. Configure environment
cp .env.example .env
# Edit .env and add your TELEGRAM_API_ID and TELEGRAM_API_HASH

# 5. Run the application
poetry run python telegram_messenger.py
```

### Alternative: pip installation

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install telethon python-dotenv

# 3. Configure .env (same as above)
cp .env.example .env

# 4. Run
python telegram_messenger.py
```

## 🚀 Usage

### First Run - Authentication

On first launch, you'll be prompted to authenticate:

```
Enter your phone number (with country code, e.g., +1234567890): +1234567890
Enter the verification code: 12345

✅ Authentication successful
Session saved to telegram.session
```

If you have 2FA enabled:
```
Two-factor authentication enabled
Enter your 2FA password: ********
✅ 2FA authentication successful
```

### Main Menu

```
╔══════════════════════════════════════════════════════════╗
║  Telegram Terminal Client - Production Grade            ║
║  Async Architecture | MTProto Protocol | Enterprise Ready║
╚══════════════════════════════════════════════════════════╝

========================================================
📱 TELEGRAM TERMINAL CLIENT - Production Edition
========================================================
1. 📤 Send a message
2. 📋 List recent contacts
3. 🎧 Monitor chats (real-time)
4. 🔍 Dump raw message (Developer Mode)
5. 🔍 Get entity info (Developer Mode)
6. ❌ Exit
========================================================
```

### Example Workflows

**Sending a Message:**
```
Enter your choice (1-6): 1

How would you like to specify the recipient?
1. Username (e.g., @username)
2. Phone number
3. User ID

Enter your choice (1-3): 1
Enter username: @example_user
Enter your message: Hello from the terminal!

✅ Message delivered successfully!
```

**Monitoring Chats:**
```
Enter your choice (1-6): 3

🎧 Monitoring all chats... (Press Ctrl+C to stop)

📩 New Message
From: alice_dev (ID: 123456789)
Chat: Development Team
Message: Hey, check out this new feature!
```

**Developer Mode - Message Inspector:**
```
Enter your choice (1-6): 4
Enter chat identifier: @mygroup
Enter message ID: 12345

🔍 RAW MESSAGE OBJECT (MTProto Structure)
{
  "id": 12345,
  "date": "2024-12-23 14:30:00",
  "message": "Sample message text",
  "from_id": "PeerUser(user_id=123456)",
  "peer_id": "PeerChat(chat_id=789012)",
  "media": null,
  "entities": [],
  "views": 42
}
```

## 🧪 Running Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test
poetry run pytest test_client.py::TestTelegramClientApp::test_send_message_retry_on_flood_wait -v

# Run with coverage
poetry run pytest --cov=telegram_messenger --cov-report=html
```

### Test Coverage

The test suite covers:
- ✅ **FloodWaitError retry logic** - Verifies automatic sleep and retry
- ✅ **2FA authentication flow** - Mocks password prompt
- ✅ **Session persistence** - Validates no console printing
- ✅ **Error handling** - Generic errors, max retries
- ✅ **Connection management** - Connect, disconnect, context manager

## 🏗️ Architecture Deep Dive

### Event Loop Pattern

The application uses `asyncio` to maintain a non-blocking event loop:

```python
async def main():
    app = TelegramClientApp()
    await app.run()  # Non-blocking

asyncio.run(main())
```

This allows the TUI to remain responsive while:
- Waiting for user input
- Listening for incoming messages
- Handling network I/O

### Session Management

**Understanding MTProto Authentication:**

1. **First Login**: 
   - Phone number → Code request
   - Diffie-Hellman key exchange → Auth Key generated
   - Auth Key stored in `.session` file

2. **Subsequent Logins**:
   - App reads `.session` file
   - Reuses Auth Key (no re-authentication needed)
   - Persistent session across restarts

**Why This Matters**: The `.session` file contains your authorization key. Never commit it to version control or share it publicly.

### FloodWait Handling

Telegram's rate limiting mechanism:

```python
try:
    await client.send_message(user, text)
except FloodWaitError as e:
    # Telegram says: "Too many requests, wait X seconds"
    wait_time = e.seconds
    await asyncio.sleep(wait_time)
    # Retry automatically
```

**Production Pattern**: Exponential backoff prevents cascading failures and respects API limits.

## 🗂️ Project Structure

```
telegram-terminal-client/
├── telegram_messenger.py    # Main application
├── test_client.py           # Test suite
├── pyproject.toml           # Poetry dependencies
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── telegram.session         # Session file (auto-generated, gitignored)
└── telegram_client.log      # Application logs (auto-generated)
```

## 📋 Configuration

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_API_ID` | Your API ID from my.telegram.org | `12345678` |
| `TELEGRAM_API_HASH` | Your API Hash | `abcdef1234567890...` |
| `SESSION_FILE_PATH` | Path to session file | `telegram.session` |
| `LOG_LEVEL` | Logging verbosity | `INFO`, `DEBUG`, `WARNING` |
| `LOG_FILE` | Log file path | `telegram_client.log` |

## 🐛 Troubleshooting

### "Configuration error: TELEGRAM_API_ID not found"
**Solution**: Create a `.env` file from `.env.example` and add your API credentials.

### "SessionPasswordNeededError"
**Solution**: Your account has 2FA enabled. Enter your cloud password when prompted.

### "FloodWaitError: A wait of X seconds is required"
**Solution**: The app handles this automatically. Just wait - it will retry.

### "Phone number invalid"
**Solution**: Include country code (e.g., `+1234567890`, not `234567890`).

### Session file doesn't persist
**Solution**: Ensure the app has write permissions in the current directory.

## 🎤 Interview Talking Points

When presenting this project, highlight:

### 1. Async Mastery
*"The entire app uses asyncio with no blocking calls, allowing concurrent operations like monitoring messages while maintaining an interactive TUI."*

### 2. Protocol Understanding
*"I implemented FloodWait handling because MTProto uses rate limiting to protect server resources. The exponential backoff strategy prevents API bans while ensuring message delivery."*

### 3. Session Security
*"The session file contains the Auth Key from the Diffie-Hellman exchange. I deliberately avoid printing it to console and use .gitignore to prevent accidental exposure."*

### 4. Production Patterns
*"I used Poetry for dependency management, pytest for testing, and comprehensive logging - all standard practices for enterprise Python applications."*

### 5. Type Safety
*"Every function uses type hints (PEP 484) for better IDE support and early error detection."*

## 📚 Learning Resources

- [MTProto Protocol Documentation](https://core.telegram.org/mtproto)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Python asyncio Guide](https://docs.python.org/3/library/asyncio.html)
- [Telegram API Methods](https://core.telegram.org/methods)

## 📄 License

MIT License - Feel free to use this for your portfolio or learning.

## 🤝 Contributing

This is a portfolio/learning project, but suggestions are welcome! Open an issue or submit a PR.

---

**Built with 💙 by SHAROFIDDIN**  
*Demonstrating production-grade Python for backend engineering roles*
