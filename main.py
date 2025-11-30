import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import platform
import psutil
from db import db
from lib.lang import ask_server_language
from lib import gpt_history, gpt

# Load .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

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

# -------- EVENTS --------

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands!")
    except Exception as e:
        print("Erro ao sync:", e)

    print(f"BOT ONLINE: {bot.user}")
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
async def on_member_join(member):
    guild_id = str(member.guild.id)
    user_id = str(member.id)
    db.ensure_user(guild_id, user_id)
    db.set_user_value(guild_id, user_id, "name", member.name)
    print(f"Usuário {member.name} registrado no banco do servidor {member.guild.name}")

@bot.event
async def on_guild_join(guild):
    await ask_server_language(bot, guild)

# --------- ON MESSAGE ---------
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    # Salva mensagem no histórico normal
    gpt_history.register_message(message)

    handled = False
    ref_id = getattr(message.reference, "message_id", None)

    if ref_id:
        guild_id = str(message.guild.id)
        guild_chat = db.get_chat(guild_id)
        for user_id, user_data in guild_chat["users"].items():
            for entry in user_data.get("historico_gpt", []):
                if entry.get("role") == "assistant" and entry.get("id") == ref_id:
                    # mensagem do GPT respondida
                    await gpt.handle_mita_mention(message, reference=True)
                    handled = True
                    break
            if handled:
                break

    # Se não for resposta a GPT, checa se cita "mita"
    if not handled and "mita" in message.content.lower():
        await gpt.handle_mita_mention(message)

    await bot.process_commands(message)

# --------- COMMANDS ---------
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong ♡ Latency: {round(bot.latency*1000)}ms")

# Run bot
async def main():
    async with bot:
        # Carrega todos os comandos automaticamente
        for filename in os.listdir("commands"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await bot.load_extension(f"commands.{filename[:-3]}")
                    print(f"✅ {filename} carregado!")
                except Exception as e:
                    print(f"❌ Falha ao carregar {filename}: {e}")
        
        await bot.start(TOKEN)
# Para rodar
import asyncio
asyncio.run(main())

