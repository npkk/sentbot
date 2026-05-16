import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
import discord
from src.sentbot.bot import get_author_name, build_conversation_context

def test_get_author_name_member():
    member = MagicMock(spec=discord.Member)
    member.nick = "NickName"
    member.name = "UserName"
    assert get_author_name(member) == "NickName"

    member_no_nick = MagicMock(spec=discord.Member)
    member_no_nick.nick = None
    member_no_nick.name = "UserName"
    assert get_author_name(member_no_nick) == "UserName"

def test_get_author_name_user():
    user = MagicMock(spec=discord.User)
    user.name = "UserName"
    assert get_author_name(user) == "UserName"

@pytest.mark.asyncio
async def test_build_conversation_context():
    # Mock Channel
    channel = MagicMock(spec=discord.TextChannel)
    
    # メッセージの作成
    now = datetime.now()
    
    # 1. 正常なメッセージ
    msg1 = MagicMock(spec=discord.Message)
    msg1.id = 1
    msg1.created_at = now - timedelta(minutes=1)
    msg1.content = "Hello"
    msg1.author = MagicMock(spec=discord.User)
    msg1.author.name = "User1"
    
    # 2. current_message (除外対象)
    current_msg_id = 2
    
    # 3. タイムアウトメッセージ
    msg3 = MagicMock(spec=discord.Message)
    msg3.id = 3
    msg3.created_at = now - timedelta(minutes=15)
    msg3.content = "Old message"
    msg3.author = MagicMock(spec=discord.User)
    msg3.author.name = "User2"

    # historyのイテレータをモック
    channel.history.return_value = [
        MagicMock(id=current_msg_id), # current
        msg1, # 正常
        msg3  # タイムアウト
    ]
    
    history = await build_conversation_context(
        channel, limit=10, timeout_minutes=5, 
        current_message_id=current_msg_id, last_time=now
    )
    
    # 結果の検証
    assert len(history) == 1
    assert history[0]["author"] == "User1"
    assert history[0]["content"] == "Hello"
