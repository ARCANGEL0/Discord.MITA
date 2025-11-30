import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import platform
import psutil
from db import db
from lib.lang import ask_server_language
from lib import gpt_history, gpt
from pathlib import Path
import asyncio

# Load .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ------------------------------
# System info & header
# ------------------------------
def get_system_info():
    return {
        "OS": platform.system() + " " + platform.release(),
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
        "Python": platform.python_version()
    }

def print_mita_header():
    header = r"""
,--.   ,--.,--.  ,--.               ,---.   ,---.  
|   `.'   |`--',-'  '-. ,--,--.    '   .-' '.-.  \ 
|  |'.'|  |,--.'-.  .-'' ,-.  |    `.  `-.  .-' .' 
|  |   |  ||  |  |  |  \ '-'  |    .-'    |/   '-. 
`--'   `--'`--'  `--'   `--`--'    `-----' '-----' 
       ~ Mita is awake ~ 😏
"""
    print(header)

# ------------------------------
# EVENTS
# ------------------------------
@bot.event
async def on_ready():
    print_mita_header()
    print(f"BOT ONLINE: {bot.user} (ID: {bot.user.id})")
    sys_info = get_system_info()
    print("===== System Info =====")
    for k, v in sys_info.items():
        print(f"{k}: {v}")
    print("=======================")
    print(f"Prefix: {PREFIX}")
    print(f"Invite link: {os.getenv('INVITE_LINK')}")
    print("Mita is ready and online! 😏")

    # Sync slash commands após todos os cogs carregados
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands!")
    except Exception as e:
        print("❌ Erro ao sync:", e)

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    user_id = str(member.id)
    db.ensure_user(guild_id, user_id)
    db.set_user_value(guild_id, user_id, "name", member.name)
    print(f"Usuário {member.name} registrado no banco do servidor {member.guild.name}")

@bot.event
async def on_guild_join(guild):
    await ask_server_language(bot, guild)

# ------------------------------
# ON MESSAGE
# ------------------------------
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    # 1️⃣ Salva mensagem no histórico normal
    gpt_history.register_message(message)

    # 2️⃣ Se a mensagem for reply a uma resposta do GPT
    if message.reference and message.reference.message_id:
        ref_id = message.reference.message_id
        if gpt_history.is_gpt_message(message.guild.id, ref_id):
            await gpt.handle_mita_mention(message, reference=True)
            await bot.process_commands(message)
            return

    # 3️⃣ Se cita "mita"
    if "mita" in message.content.lower():
        await gpt.handle_mita_mention(message)

    await bot.process_commands(message)

# ------------------------------
# COMMANDS
# ------------------------------
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong ♡ Latency: {round(bot.latency*1000)}ms")

# ------------------------------
# MAIN LOOP
# ------------------------------
async def main():
    async with bot:
        # Load all commands/cogs in commands/
        commands_path = Path("commands")
        for file in commands_path.glob("*.py"):
            if file.name.startswith("__"):
                continue
            try:
                await bot.load_extension(f"commands.{file.stem}")
                print(f"✅ {file.name} carregado!")
            except Exception as e:
                print(f"❌ Falha ao carregar {file.name}: {e}")

        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
