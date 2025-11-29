import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import platform
import psutil

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

# Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! Mita is awake 😏 Latency: {round(bot.latency*1000)}ms")

# Run bot
bot.run(TOKEN)
