import discord
from discord.ext import commands
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.command()
async def ambil(ctx):
    await ctx.send("🔍 Koin apa yang perlu saya ambil datanya? (contoh: BTC, ETH, SOL, XRP)")

    def check_coin(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    coin_msg = await bot.wait_for("message", check=check_coin)
    coin = coin_msg.content.upper() + "USDT"

    await ctx.send("⏳ Berapa lama datanya? (ketik: 1 bulan, 3 bulan, atau 1 tahun)")

    def check_duration(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ['1 bulan', '3 bulan', '1 tahun']

    duration_msg = await bot.wait_for("message", check=check_duration)
    duration = duration_msg.content.lower()
    days_map = {'1 bulan': 30, '3 bulan': 90, '1 tahun': 365}
    days = days_map[duration]

    await ctx.send("🗓️ Dari bulan dan tahun berapa kamu ingin mulai? (Contoh: Juni 2024)")

    def check_date(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    date_msg = await bot.wait_for("message", check=check_date)
    try:
        start_date = pd.to_datetime("01 " + date_msg.content, dayfirst=True)
        end_date = start_date + timedelta(days=days)

        limit = min(days, 1000)
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            "symbol": coin,
            "interval": "1d",
            "startTime": int(start_date.timestamp() * 1000),
            "endTime": int(end_date.timestamp() * 1000),
            "limit": limit
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            await ctx.send("❌ Gagal mengambil data dari Binance.")
            return

        data = response.json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        filename = f"{coin}_{start_date.strftime('%Y%m')}_{duration.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False)

        await ctx.send(
            f"✅ Berhasil mengambil data koin **{coin}** dari **{start_date.strftime('%d %b %Y')}** selama **{duration}**.",
            file=discord.File(fp=filename)
        )

    except Exception as e:
        await ctx.send("⚠️ Format tanggal tidak valid atau terjadi kesalahan lainnya.")

bot.run(TOKEN)
