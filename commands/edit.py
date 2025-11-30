import discord
from discord.ext import commands
from lib.uploadImage import upload_image
from lib.nano import editar_imagem
from db import db
import aiohttp
import urllib.parse

class Edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="edit")
    async def edit(self, ctx, *, texto=None):
        """Edita uma imagem com base no prompt fornecido."""
        guild_id = str(ctx.guild.id)
        language = db.get_server_value(guild_id, "language", default="EN")

        if language == "PT":
            no_text_msg = "Oiii~ (๑・ω・๑)💖 O que você quer que eu edite? Me conta tudo, por favor~ 🌸"
            no_image_msg = "Hm~ 🌸 parece que não tem imagem junto! Manda a imagem junto com `.imagem`, tá~? 💖"
            sending_msg = "Tcharam~ 🌸 Sua obra de arte ficou prontinha! 💖"
        else:  # English
            no_text_msg = "Hehe~ (๑・ω・๑)💖 What would you like me to edit? Tell me everything~ 🌸"
            no_image_msg = "Hm~ 🌸 Looks like there’s no image! Please send the image along with `.imagem`~ 💖"
            sending_msg = "Tada~ 🌸 Your masterpiece is ready! 💖"

        if not texto:
            await ctx.send(no_text_msg)
            return

        if not ctx.message.attachments:
            await ctx.send(no_image_msg)
            return

        buffer = await ctx.message.attachments[0].read()
        original_url = await upload_image(buffer)
        editada_url = await editar_imagem(texto, original_url)
        await ctx.send(f"{sending_msg} 🌸\n{editada_url}\n\nPrompt:\n{texto} 💖")

async def setup(bot):
    await bot.add_cog(EditImage(bot))