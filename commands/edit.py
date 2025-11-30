import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from db import db

MITA_SMILE = "<:mitasmile:1444758849046184069>"
MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"

class Edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="edit",
        description=f"Edit an image using AI "
    )
    async def edit(self, interaction: discord.Interaction, texto: str):
        """Edits an image based on the provided prompt."""
        guild_id = str(interaction.guild.id)

        # Safe language fallback
        try:
            language = db.get_server_value(guild_id, "language", default="EN")
        except Exception:
            language = "EN"

        # ===========================
        # Mita-style messages
        # ===========================
        if language == "PT":
            no_text_msg = "Oiii~ (๑・ω・๑)💖 O que você quer que eu edite? Me conta tudo, por favor~ 🌸"
            no_image_msg = "Hm~ 🌸 parece que não tem imagem junto! Manda a imagem junto com `.edit`, tá~? 💖"
            sending_msg = f"Tcharam~ {MITA_COOL} Sua obra de arte ficou prontinha! 💖"
            upload_error_msg = "Ih... {MITA_CRY} não consegui enviar a imagem! Tenta me enviar denovo, por favor~💖"
            edit_error_msg = f"Ih... Algo deu errado ao editar {MITA_CRY}! 🌸 Me perdoa (╥﹏╥), vamos tentar de novo 💖"
        else:
            no_text_msg = "Hehe~ (๑・ω・๑)💖 What would you like me to edit? Tell me everything~ 🌸"
            no_image_msg = "Hm~ 🌸 Looks like there’s no image! Please send the image along with `.edit`~ 💖"
            sending_msg = f"Tada~ {MITA_COOL} Your masterpiece is ready! 💖"
            upload_error_msg = "Oops… {MITA_CRY} Sorry ! I couldn’t upload your image! Try sending me the image again, okay~? 💖"
            edit_error_msg = "Hm… something went wrong while editing {MITA_CRY}! Sorry (╥﹏╥), let’s try again, okay?~ 💖"

        # ===============================
        # Check text
        # ===============================
        if not texto:
            await interaction.response.send_message(no_text_msg)
            return

        # ===============================
        # Get image (attachment OR marked)
        # ===============================
        image_bytes = None
        image_filename = None

        # A) User uploaded an image with the slash command
        if interaction.attachments:
            att = interaction.attachments[0]
            image_bytes = await att.read()
            image_filename = att.filename

        # B) User selected an image (resolved attachments)
        elif interaction.data.get("resolved") and interaction.data["resolved"].get("attachments"):
            ref_att = next(iter(interaction.data["resolved"]["attachments"].values()))
            async with aiohttp.ClientSession() as session:
                async with session.get(ref_att["url"]) as resp:
                    image_bytes = await resp.read()
                    image_filename = ref_att["filename"]

        # C) No image found
        if not image_bytes:
            await interaction.response.send_message(no_image_msg)
            return

        # reply first
        await interaction.response.send_message("🌸")

        # ===============================
        # Send to API
        # ===============================
        try:
            form = aiohttp.FormData()
            form.add_field("prompt", texto)
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

                    edited_bytes = await resp.read()

        except Exception as e:
            await interaction.followup.send(f"{edit_error_msg}\n\n`{e}`")
            return

        # ===============================
        # Send final result
        # ===============================
        await interaction.followup.send(
            f"{sending_msg} 🌸\n\nPrompt:\n{texto} 💖",
            file=discord.File(edited_bytes, filename="edited.png")
        )


async def setup(bot):
    await bot.add_cog(Edit(bot))
