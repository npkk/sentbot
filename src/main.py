import os
import logging
import discord
from discord import app_commands
from dotenv import load_dotenv
from sentbot.sentiment_analyzer import SentimentAnalyzer
from sentbot.bot import SentBot

# 環境変数の読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
SLOW_MODE_DELAY = int(os.getenv("SLOW_MODE_DELAY", 10))
SLOW_MODE_DURATION = int(os.getenv("SLOW_MODE_DURATION", 300))
MAX_CONTEXT = int(os.getenv("MAX_CONTEXT_MESSAGES", 20))
CONTEXT_TIMEOUT = int(os.getenv("CONTEXT_TIMEOUT_MINUTES", 10))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ロギングの設定
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def main():
    analyzer = SentimentAnalyzer(
        api_key=GROQ_API_KEY,
        model_name=GROQ_MODEL_NAME
    )
    
    bot = SentBot(
        analyzer=analyzer,
        slow_mode_delay=SLOW_MODE_DELAY,
        slow_mode_duration=SLOW_MODE_DURATION,
        max_context=MAX_CONTEXT,
        context_timeout=CONTEXT_TIMEOUT,
        guild_id=GUILD_ID
    )

    @bot.tree.command(name="status", description="Botの現在の監視ステータスを表示します")
    async def status(interaction: discord.Interaction):
        status_str = "有効" if bot.is_monitoring else "無効"
        embed = discord.Embed(title="SentBot ステータス", color=discord.Color.blue())
        embed.add_field(name="全体の監視状態", value=status_str, inline=False)
        embed.add_field(name="低速モード秒数", value=f"{bot.slow_mode_delay}秒", inline=True)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="toggle", description="Bot全体の監視の有効/無効を切り替えます")
    @app_commands.describe(enabled="有効にする場合はTrue、無効にする場合はFalse")
    async def toggle(interaction: discord.Interaction, enabled: bool):
        bot.is_monitoring = enabled
        state = "有効" if enabled else "無効"
        logger.info(f"Bot全体の監視設定が変更されました: {state}")
        await interaction.response.send_message(f"Bot全体の監視を{state}にしました。")

    @bot.tree.command(name="set_slowmode", description="低速モードの秒数を設定します")
    @app_commands.describe(seconds="低速モードの秒数（0で解除）")
    async def set_slowmode(interaction: discord.Interaction, seconds: int):
        if 0 <= seconds <= 21600:
            bot.slow_mode_delay = seconds
            logger.info(f"低速モード秒数が変更されました: {seconds}")
            await interaction.response.send_message(f"低速モードの秒数を {seconds} 秒に設定しました。")
        else:
            await interaction.response.send_message("秒数は 0 から 21600 の間で指定してください。", ephemeral=True)

    if not TOKEN:
        logger.error("DISCORD_TOKEN が設定されていません。")
    else:
        bot.run(TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
