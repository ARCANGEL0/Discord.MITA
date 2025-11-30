import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import platform
import psutil
from db import db
from lib.lang import ask_server_language
from lib import gpt_history, gpt

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

# Function to get system info
def get_system_info():
    info = {
        "OS": platform.system() + " " + platform.release(),
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB",
        "Python": platform.python_version()
    }
    return info

# New Mita-style header
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

# Event: Bot ready
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


 # ---------
 # load modules
 # -------------
bot.load_extension("commands.langToggle")


@bot.event
async def on_message(message):
    # 1️⃣ Salva mensagem no histórico
    gpt_history.register_message(message)

    # 2️⃣ Verifica se cita "mita" e responde
    if "mita" in message.content.lower():
        await gpt.handle_mita_mention(message)

    # 3️⃣ Permite outros comandos
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    user_id = str(member.id)
    
    # Garante que o usuário exista no banco
    db.ensure_user(guild_id, user_id)
    
    # Exemplo: guardar o nome do usuário
    db.set_user_value(guild_id, user_id, "name", member.name)
    
    print(f"Usuário {member.name} registrado no banco do servidor {member.guild.name}")
@bot.event
async def on_guild_join(guild):
    # Quando o bot entrar em um servidor novo
    await ask_server_language(bot, guild)


# Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong ♡ Latency: {round(bot.latency*1000)}ms")

# Run bot
bot.run(TOKEN)
