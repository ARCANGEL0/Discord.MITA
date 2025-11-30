import discord
from discord.ext import commands
from lib.lang import LanguageView

class LangToggle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lang")
    async def lang(self, ctx):
        """Reenvia a seleção de idioma"""
        await ctx.send(
            "> Entãão..~ vamos ver… qual será o idioma deste servidor, hm~ ? 💖\n> Soo~ let’s see… what will be the language of our server, hm~~ 💖?\n\n",
            view=LanguageView()
        )

    @commands.command(name="idioma")
    async def idioma(self, ctx):
        """Alias em português"""
        await self.lang(ctx)


async def setup(bot):
    await bot.add_cog(LangToggle(bot))
