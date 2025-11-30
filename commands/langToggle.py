import discord
from discord.ext import commands
from lib.lang import ask_server_language

class LangToggle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lang")
    async def lang(self, ctx):
        """Reconfigura o idioma do servidor"""
        await ask_server_language(self.bot, ctx.guild)

    @commands.command(name="idioma")
    async def idioma(self, ctx):
        """Reconfigura o idioma do servidor (português)"""
        await ask_server_language(self.bot, ctx.guild)

# Função de setup para registrar o cog
def setup(bot):
    bot.add_cog(LangToggle(bot))
