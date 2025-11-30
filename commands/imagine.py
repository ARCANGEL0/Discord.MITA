import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from db import db  # seu helper de banco

# Custom emojis
MITA_SMILE = "<:mitasmile:1444758849046184069>"
MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"    
       
class Imagine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="imagine",
        description=f"Generate an image using AI {MITA_COOL} \n Gera uma imagem usando IA {MITA_COOL}"
    )
    async def imagine(self, interaction: discord.Interaction, prompt: str = None):
        guild_id = str(interaction.guild.id)
        language = db.get_server_value(guild_id, "language", default="EN")

        # -------------------------
        # 1️⃣ valida prompt
        # -------------------------
        if not prompt:
            msg = (
                "Humm~ você precisa me dizer o que quer que eu crie, tá? 💖🌸"
                if language == "PT" 
                else "Hehe~ you need to tell me what to create, okay? 💖🌸"
            )
            await interaction.response.send_message(msg)
            return

        # -------------------------
        # 2️⃣ mensagem inicial
        # -------------------------
        waiting_msg = (
            f"Humm~ então você quer que eu desenha algo tipo:\n```plaintext\n**{prompt}**… \n```\n Pode deixar! 💖" 
            if language == "PT" 
            else f"Okiee~~, soo, you want me to make something like:\n ```plaintext\n**{prompt}**…\n```\n Got it! 💖"
        )
        await interaction.response.send_message(waiting_msg)
        await interaction.original_response()

        # -------------------------
        # 3️⃣ PEGAR A IMAGEM:
        #    - se usuário enviou attachment
        #    - se usuário marcou uma imagem (message reference)
        # -------------------------
        image_bytes = None
        image_filename = None

        # a) se veio como attachment
        if interaction.attachments:
            att = interaction.attachments[0]
            image_bytes = await att.read()
            image_filename = att.filename

        # b) se usuário clicou em "usar imagem marcada"
        if not image_bytes and interaction.data:
            # message_reference se o user “clicou na imagem”
            ref = interaction.data.get("resolved", {}).get("attachments", {})
            if ref:
                # pega a primeira imagem
                ref_att = next(iter(ref.values()))
                async with aiohttp.ClientSession() as session:
                    async with session.get(ref_att["url"]) as resp:
                        image_bytes = await resp.read()
                        image_filename = ref_att["filename"]

        # c) se nenhuma imagem foi encontrada
        if not image_bytes:
            msg = (
                "Você precisa me enviar ou marcar uma imagem também! 💖"
                if language == "PT"
                else "You need to send or select an image too! 💖"
            )
            await interaction.followup.send(msg)
            return

        # -------------------------
        # 4️⃣ enviar pro endpoint /imagedit
        # -------------------------
        try:
            form = aiohttp.FormData()
            form.add_field("prompt", prompt)
            form.add_field(
                "image",
                image_bytes,
                filename=image_filename,
                content_type="application/octet-stream"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.zenzxz.my.id/api/maker/imagedit",
                    data=form
                ) as resp:

                    if resp.status != 200:
                        raise Exception(await resp.text())

                    edited_image = await resp.read()

            # -------------------------
            # 5️⃣ enviar a imagem final
            # -------------------------
            final_msg = (
                f"Tadaa~~! <:mitasmile:1444758849046184069> Sua imagem ficou prontinha! Entãão~.. gostou? 💖"
                if language == "PT"
                else f"Tadaa~! <:mitasmile:1444758849046184069> Your image is ready!! Soo~ did you liked it? 💖"
            )

            file = discord.File(fp=edited_image, filename="edited.png")
            followup = await interaction.followup.send(final_msg, file=file)

            emoji = discord.utils.get(interaction.guild.emojis, name="mitasmile")
            if emoji:
                await followup.add_reaction(emoji)

        except Exception as e:
            error_msg = (
                f"ih...Ocorreu um errinho  <:mitacry:1444760327714504954> ❌: `{e}`"
                if language == "PT"
                else f"Oops, something went wrong <:mitacry:1444760327714504954> ❌: `{e}`"
            )
            fail_msg = await interaction.followup.send(error_msg)

            emoji = discord.utils.get(interaction.guild.emojis, name="mitacry")
            if emoji:
                await fail_msg.add_reaction(emoji)


async def setup(bot):
    await bot.add_cog(Imagine(bot))
