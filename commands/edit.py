import discord
from discord.ext import commands
from lib.uploadImage import upload_image
from lib.nano import editar_imagem
from db import db

class Edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="edit", aliases=["imagem"])
    async def edit(self, ctx, *, texto=None):
        """Edita uma imagem com base no prompt fornecido."""
        guild_id = str(ctx.guild.id)

        # Fallback seguro de idioma
        try:
            language = db.get_server_value(guild_id, "language", default="EN")
        except Exception:
            language = "EN"

        # Mensagens Mita-style por idioma
        if language == "PT":
            no_text_msg = "Oiii~ (๑・ω・๑)💖 O que você quer que eu edite? Me conta tudo, por favor~ 🌸"
            no_image_msg = "Hm~ 🌸 parece que não tem imagem junto! Manda a imagem junto com `.imagem`, tá~? 💖"
            sending_msg = "Tcharam~ 🌸 Sua obra de arte ficou prontinha! 💖"
            upload_error_msg = "Ops… 🌸 não consegui enviar a imagem! Tenta de novo, por favor 💖"
            edit_error_msg = "Hm… algo deu errado ao editar! 🌸 Me perdoa, vamos tentar de novo 💖"
        else:  # English
            no_text_msg = "Hehe~ (๑・ω・๑)💖 What would you like me to edit? Tell me everything~ 🌸"
            no_image_msg = "Hm~ 🌸 Looks like there’s no image! Please send the image along with `.imagem`~ 💖"
            sending_msg = "Tada~ 🌸 Your masterpiece is ready! 💖"
            upload_error_msg = "Oops… 🌸 I couldn’t upload your image! Please try again 💖"
            edit_error_msg = "Hm… something went wrong while editing! 🌸 Sorry, let’s try again 💖"

        # Verifica prompt e anexo
        if not texto:
            await ctx.send(no_text_msg)
            return

        if not ctx.message.attachments:
            await ctx.send(no_image_msg)
            return

        await ctx.message.add_reaction("🌸")
        buffer = await ctx.message.attachments[0].read()

        # Upload da imagem
        try:
            original_url = await upload_image(buffer)
        except Exception:
            await ctx.send(upload_error_msg)
            return

        # Edição via API
        try:
            editada_url = await editar_imagem(texto, original_url)
        except Exception:
            await ctx.send(edit_error_msg)
            return

        await ctx.send(f"{sending_msg} 🌸\n{editada_url}\n\nPrompt:\n{texto} 💖")

async def setup(bot):
    await bot.add_cog(Edit(bot))
