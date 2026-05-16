import logging
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "slowmode_state.json")

def get_author_name(author: discord.abc.User) -> str:
    """discord.abc.User から表示名を取得する"""
    if isinstance(author, discord.Member):
        return author.nick or author.name
    return author.name

class SentBot(commands.Bot):
    def __init__(
        self,
        analyzer,
        slow_mode_delay: int = 10,
        slow_mode_duration: int = 300,
        max_context: int = 20,
        context_timeout: int = 10,
        guild_id: str = None
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.analyzer = analyzer
        self.is_monitoring = False
        self.slow_mode_delay = slow_mode_delay
        self.slow_mode_duration = slow_mode_duration
        self.slow_mode_tasks = {}
        self.max_context = max_context
        self.context_timeout = context_timeout
        self.guild_id = guild_id
        
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        if not os.path.exists(STATE_FILE):
            with open(STATE_FILE, "w") as f:
                json.dump({}, f)

    async def setup_hook(self):
        if self.guild_id:
            guild = discord.Object(id=int(self.guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        
        await self._restore_slowmode_tasks()
        logger.info(f"スラッシュコマンドを同期しました: {self.user}")

    async def _restore_slowmode_tasks(self):
        """起動時に保存された低速モード設定を復旧する"""
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            
            now = datetime.now(timezone.utc)
            for channel_id_str, expiry_str in state.items():
                channel_id = int(channel_id_str)
                expiry = datetime.fromisoformat(expiry_str)
                
                channel = self.get_channel(channel_id)
                if not channel or not isinstance(channel, discord.TextChannel):
                    continue

                if now >= expiry:
                    await channel.edit(slowmode_delay=0)
                    self._remove_state(channel_id)
                else:
                    seconds_left = (expiry - now).total_seconds()
                    task = asyncio.create_task(self._reset_slowmode(channel, delay=seconds_left))
                    self.slow_mode_tasks[channel_id] = task
        except Exception as e:
            logger.error(f"低速モード設定の復旧中にエラーが発生しました: {e}")

    def _save_state(self, channel_id: int, expiry: datetime):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        state[str(channel_id)] = expiry.isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    def _remove_state(self, channel_id: int):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        state.pop(str(channel_id), None)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    async def on_ready(self):
        logger.info(f"ログインしました: {self.user} (ID: {self.user.id})")
        logger.info("------")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if not self.is_monitoring:
            await self.process_commands(message)
            return

        try:
            history_messages = await build_conversation_context(
                message.channel,
                self.max_context,
                self.context_timeout,
                message.id,
                message.created_at
            )

            current_author = get_author_name(message.author)
            
            if self.analyzer.analyze_context(current_author, message.content, history_messages):
                if isinstance(message.channel, discord.TextChannel):
                    await message.channel.edit(slowmode_delay=self.slow_mode_delay)
                    await message.channel.send(
                        f"🌱 ちょっとだけ深呼吸してみませんか？\n会話がヒートアップしちゃいそうなので、このチャンネルを{self.slow_mode_delay}秒間のゆっくりモードにしました（{self.slow_mode_duration}秒後にまた元通りになりますね）。",
                        delete_after=10
                    )

                    channel_id = message.channel.id
                    if channel_id in self.slow_mode_tasks:
                        self.slow_mode_tasks[channel_id].cancel()
                    
                    expiry = datetime.now(timezone.utc) + timedelta(seconds=self.slow_mode_duration)
                    self._save_state(channel_id, expiry)
                    task = asyncio.create_task(self._reset_slowmode(message.channel))
                    self.slow_mode_tasks[channel_id] = task

        except Exception as e:
            logger.error(f"解析中にエラーが発生しました: {e}")

        await self.process_commands(message)

    async def _reset_slowmode(self, channel: discord.TextChannel, delay: float = None):
        """指定時間待機した後、低速モードを解除する"""
        try:
            wait_time = delay if delay is not None else self.slow_mode_duration
            await asyncio.sleep(wait_time)
            await channel.edit(slowmode_delay=0)
            self._remove_state(channel.id)
            await channel.send("✨ ゆっくりモードを解除しました！引き続き、楽しい会話を楽しんでくださいね。", delete_after=10)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"低速モード解除中にエラーが発生しました: {e}")
        finally:
            if self.slow_mode_tasks.get(channel.id) == asyncio.current_task():
                self.slow_mode_tasks.pop(channel.id, None)
