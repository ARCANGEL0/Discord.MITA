import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import platform
import psutil
from db import db
from lib.lang import ask_server_language
from lib import gpt_history, gpt
import asyncio

# Load .env variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Bot instance
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# -----------------------------
# Helper functions
# -----------------------------
def get_system_info():
    info = {
        "OS": platform.system() + " " + platform.release(),
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
        "Python": platform.python_version()
    }
    return info

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

# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
    print_mita_header()
    print(f"MitaBot is online as {bot.user} (ID: {bot.user.id})")
    
    sys_info = get_system_info()
    print("===== System Info =====")
    for k, v in sys_info.items():
        print(f"{k}: {v}")
    print("=======================")
    print(f"Prefix: {PREFIX}")
    print(f"Invite link: {os.getenv('INVITE_LINK')}")
    print("Mita is ready and online! 😏")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1️⃣ Salva no histórico normal
    gpt_history.register_message(message)

    # 2️⃣ Checa se é uma resposta a mensagem GPT
    reference_id = getattr(message.reference, "message_id", None)
    if reference_id:
        guild_chat = db.get_chat(str(message.guild.id))
        for user_data in guild_chat["users"].values():
            for entry in user_data.get("historico_gpt", []):
                if entry.get("role") == "assistant" and entry.get("id") == reference_id:
                    await gpt.handle_mita_mention(message, reference=True)
                    return

    # 3️⃣ Checa se a mensagem cita "mita"
    if "mita" in message.content.lower():
        await gpt.handle_mita_mention(message)
        return

    # 4️⃣ Processa outros comandos normalmente
    await bot.process_commands(message)

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

# -----------------------------
# Commands
# -----------------------------
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong ♡ Latency: {round(bot.latency*1000)}ms")

# -----------------------------
# Run bot
# -----------------------------
async def main():
    async with bot:
        await bot.load_extension("commands.langToggle")  # carrega cog
        await bot.start(TOKEN)

# Para rodar
import asyncio
asyncio.run(main())
