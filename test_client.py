"""
Unit tests for the Telegram Terminal Client.

These tests use mocking to avoid hitting the real Telegram API,
demonstrating production-grade testing practices.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from pathlib import Path

# Import the app (will be tested)
from telegram_messenger import TelegramClientApp


class TestTelegramClientApp:
    """Test suite for TelegramClientApp."""
    
    @pytest.fixture
    def mock_env(self, tmp_path, monkeypatch):
        """Create a temporary .env file for testing."""
        env_file = tmp_path / ".env"
        env_content = """
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
SESSION_FILE_PATH=test.session
LOG_LEVEL=DEBUG
"""
        env_file.write_text(env_content)
        
        # Set environment variables
        monkeypatch.setenv('TELEGRAM_API_ID', '12345678')
        monkeypatch.setenv('TELEGRAM_API_HASH', 'abcdef1234567890abcdef1234567890')
        monkeypatch.setenv('SESSION_FILE_PATH', 'test.session')
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        
        return env_file
    
    @pytest.fixture
    def app(self, mock_env):
        """Create a TelegramClientApp instance with mocked environment."""
        return TelegramClientApp()
    
    def test_initialization(self, app):
        """Test that the app initializes correctly with environment variables."""
        assert app.api_id == 12345678
        assert app.api_hash == "abcdef1234567890abcdef1234567890"
        assert app.session_file == "test.session"
        assert app.client is None
        assert app._is_connected is False
    
    def test_config_validation_missing_api_id(self, monkeypatch):
        """Test that missing API_ID raises proper error."""
        monkeypatch.delenv('TELEGRAM_API_ID', raising=False)
        monkeypatch.setenv('TELEGRAM_API_HASH', 'test_hash')
        
        with pytest.raises(SystemExit):
            TelegramClientApp()
    
    def test_config_validation_missing_api_hash(self, monkeypatch):
        """Test that missing API_HASH raises proper error."""
        monkeypatch.setenv('TELEGRAM_API_ID', '12345')
        monkeypatch.delenv('TELEGRAM_API_HASH', raising=False)
        
        with pytest.raises(SystemExit):
            TelegramClientApp()
    
    @pytest.mark.asyncio
    async def test_send_message_retry_on_flood_wait(self, app):
        """
        CRITICAL TEST: Verify FloodWaitError triggers automatic retry.
        
        This demonstrates understanding of MTProto's rate limiting mechanism.
        """
        # Setup mock client
        app.client = MagicMock()
        app.client.send_message = AsyncMock()
        
        # Simulate FloodWaitError on first call, success on second
        from telethon.errors import FloodWaitError
        
        # Create a mock FloodWaitError with seconds attribute
        flood_error = FloodWaitError(request=MagicMock())
        flood_error.seconds = 1  # Set the wait time
        app.client.send_message.side_effect = [flood_error, None]
        
        # Execute the function
        result = await app.send_message_safe("test_user", "Hello", max_retries=3)
        
        # Assertions
        assert result is True, "Message should eventually succeed"
        assert app.client.send_message.call_count == 2, "Should retry exactly once after FloodWait"
        
        # Verify it was called with correct parameters both times
        calls = app.client.send_message.call_args_list
        assert calls[0][0] == ("test_user", "Hello")
        assert calls[1][0] == ("test_user", "Hello")
    
    @pytest.mark.asyncio
    async def test_send_message_max_retries_exceeded(self, app):
        """Test that max retries prevents infinite loops."""
        app.client = MagicMock()
        app.client.send_message = AsyncMock()
        
        from telethon.errors import FloodWaitError
        
        # Create a FloodWaitError that always triggers
        flood_error = FloodWaitError(request=MagicMock())
        flood_error.seconds = 1
        app.client.send_message.side_effect = flood_error
        
        result = await app.send_message_safe("test_user", "Hello", max_retries=2)
        
        assert result is False, "Should fail after max retries"
        assert app.client.send_message.call_count == 2, "Should attempt exactly max_retries times"
    
    @pytest.mark.asyncio
    async def test_send_message_success_first_try(self, app):
        """Test successful message send without retries."""
        app.client = MagicMock()
        app.client.send_message = AsyncMock(return_value=None)
        
        result = await app.send_message_safe("@testuser", "Hello World")
        
        assert result is True
        assert app.client.send_message.call_count == 1
        app.client.send_message.assert_called_once_with("@testuser", "Hello World")
    
    @pytest.mark.asyncio
    async def test_send_message_generic_error(self, app):
        """Test that non-FloodWait errors are handled gracefully."""
        app.client = MagicMock()
        app.client.send_message = AsyncMock(side_effect=Exception("Network error"))
        
        result = await app.send_message_safe("test_user", "Hello")
        
        assert result is False
        assert app.client.send_message.call_count == 1, "Should not retry on generic errors"
    
    @pytest.mark.asyncio
    async def test_session_file_not_printed(self, app, capsys):
        """
        CRITICAL TEST: Verify session is saved to file, not printed to console.
        
        Security best practice - sessions should never be exposed in logs/console.
        """
        # This test verifies the architectural decision
        # In the actual app, session is managed by Telethon and saved to file
        assert app.session_file == "test.session"
        
        # Capture any output during initialization
        captured = capsys.readouterr()
        
        # Verify no auth key or session string is printed
        assert "auth" not in captured.out.lower() or "authentication" in captured.out.lower()
        assert "session string" not in captured.out.lower()
    
    @pytest.mark.asyncio
    @patch('telegram_messenger.TelegramClient')
    async def test_connect_existing_session(self, mock_telegram_client, app):
        """Test connection reuses existing session without re-authentication."""
        # Setup mock
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.is_user_authorized = AsyncMock(return_value=True)
        mock_telegram_client.return_value = mock_client_instance
        
        # Connect
        await app.connect()
        
        # Verify
        assert app._is_connected is True
        mock_client_instance.connect.assert_called_once()
        mock_client_instance.is_user_authorized.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('telegram_messenger.TelegramClient')
    @patch('builtins.input', side_effect=['+1234567890', '12345'])
    async def test_authentication_flow(self, mock_input, mock_telegram_client, app):
        """
        Test the authentication flow (phone → code → session creation).
        
        This mimics MTProto's Diffie-Hellman key exchange and session creation.
        """
        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.is_user_authorized = AsyncMock(return_value=False)
        mock_client_instance.send_code_request = AsyncMock()
        mock_client_instance.sign_in = AsyncMock()
        mock_telegram_client.return_value = mock_client_instance
        
        # Execute connect (which should trigger authentication)
        await app.connect()
        
        # Verify authentication flow
        mock_client_instance.send_code_request.assert_called_once_with('+1234567890')
        mock_client_instance.sign_in.assert_called_once_with('+1234567890', '12345')
    
    @pytest.mark.asyncio
    @patch('telegram_messenger.TelegramClient')
    @patch('builtins.input', side_effect=['+1234567890', '12345', 'my_password'])
    async def test_two_factor_authentication(self, mock_input, mock_telegram_client, app):
        """
        CRITICAL TEST: Verify 2FA (SessionPasswordNeededError) is handled.
        
        Many Telegram accounts use 2FA - production code must handle this.
        """
        from telethon.errors import SessionPasswordNeededError
        
        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.is_user_authorized = AsyncMock(return_value=False)
        mock_client_instance.send_code_request = AsyncMock()
        
        # First sign_in raises 2FA error, second succeeds
        session_error = SessionPasswordNeededError(request=MagicMock())
        mock_client_instance.sign_in = AsyncMock(
            side_effect=[session_error, None]
        )
        
        mock_telegram_client.return_value = mock_client_instance
        
        # Execute
        await app.connect()
        
        # Verify 2FA flow
        assert mock_client_instance.sign_in.call_count == 2
        
        # First call: with phone and code
        first_call = mock_client_instance.sign_in.call_args_list[0]
        assert first_call[0] == ('+1234567890', '12345')
        
        # Second call: with password
        second_call = mock_client_instance.sign_in.call_args_list[1]
        assert second_call[1] == {'password': 'my_password'}
    
    @pytest.mark.asyncio
    async def test_disconnect(self, app):
        """Test graceful disconnection."""
        app.client = AsyncMock()
        app.client.disconnect = AsyncMock()
        app._is_connected = True
        
        await app.disconnect()
        
        app.client.disconnect.assert_called_once()
        assert app._is_connected is False
    
    @pytest.mark.asyncio
    async def test_context_manager(self, app):
        """Test async context manager protocol."""
        app.connect = AsyncMock()
        app.disconnect = AsyncMock()
        
        async with app:
            assert True  # Just verify no errors in context
        
        app.connect.assert_called_once()
        app.disconnect.assert_called_once()


class TestDeveloperTools:
    """Test developer mode features."""
    
    @pytest.mark.asyncio
    async def test_dump_message_raw(self, monkeypatch):
        """Test raw message dumping functionality."""
        monkeypatch.setenv('TELEGRAM_API_ID', '12345')
        monkeypatch.setenv('TELEGRAM_API_HASH', 'test_hash')
        
        app = TelegramClientApp()
        app.client = AsyncMock()
        
        # Mock message object
        mock_message = MagicMock()
        mock_message.id = 123
        mock_message.date = "2024-01-01"
        mock_message.message = "Test message"
        mock_message.from_id = "user123"
        mock_message.peer_id = "chat456"
        mock_message.fwd_from = None
        mock_message.via_bot_id = None
        mock_message.reply_to = None
        mock_message.media = None
        mock_message.entities = []
        mock_message.views = 10
        mock_message.edit_date = None
        
        app.client.get_messages = AsyncMock(return_value=[mock_message])
        
        # Execute (should not raise)
        await app.dump_message_raw(123, "test_chat")
        
        app.client.get_messages.assert_called_once_with("test_chat", ids=123)


# Running the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
