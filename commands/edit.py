import discord
from discord.ext import commands
import aiohttp
from db import db

MITA_SMILE = "<:mitasmile:1444758849046184069>"
MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"

class Edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="edit", aliases=["imagem"])
    async def edit(self, ctx, *, texto=None):
        """Edits an image based on the provided prompt."""
        print("[DEBUG] Command received")

        guild_id = str(ctx.guild.id)
        # Safe language fallback
        try:
            language = db.get_server_value(guild_id, "language", default="EN")
        except Exception:
            language = "EN"
        print(f"[DEBUG] Language: {language}")

        # Mita-style messages
        if language == "PT":
            no_text_msg = "Oiii~ (๑・ω・๑)💖 O que você quer que eu edite? Me conta tudo, por favor~ 🌸"
            no_image_msg = "Hm~ 🌸 parece que não tem imagem junto! Manda a imagem junto com `.edit`, tá~? 💖"
            sending_msg = f"Tcharam~ {MITA_COOL} Sua obra de arte ficou prontinha! 💖"
            edit_error_msg = f"Ih... Algo deu errado ao editar {MITA_CRY}! 🌸 Me perdoa (╥﹏╥), vamos tentar de novo 💖"
        else:
            no_text_msg = "Hehe~ (๑・ω・๑)💖 What would you like me to edit? Tell me everything~ 🌸"
            no_image_msg = "Hm~ 🌸 Looks like there’s no image! Please send the image along with `.edit`~ 💖"
            sending_msg = f"Tada~ {MITA_COOL} Your masterpiece is ready! 💖"
            edit_error_msg = "Hm… something went wrong while editing {MITA_CRY}! Sorry (╥﹏╥), let’s try again 💖"

        # Check prompt
        if not texto:
            print("[DEBUG] No prompt provided")
            await ctx.send(no_text_msg)
            return
        print(f"[DEBUG] Prompt: {texto}")

        # Get image: attachment first
        image_bytes = None
        image_filename = None

        if ctx.message.attachments:
            att = ctx.message.attachments[0]
            image_bytes = await att.read()
            image_filename = att.filename
            print(f"[DEBUG] Using uploaded attachment: {image_filename} ({len(image_bytes)} bytes)")

        # If message is a reply, try to get attachment from replied message
        elif ctx.message.reference:
            replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if replied_msg.attachments:
                att = replied_msg.attachments[0]
                image_bytes = await att.read()
                image_filename = att.filename
                print(f"[DEBUG] Using replied message attachment: {image_filename} ({len(image_bytes)} bytes)")

        if not image_bytes:
            print("[DEBUG] No image found")
            await ctx.send(no_image_msg)
            return

        await ctx.message.add_reaction("🌸")

        # ===============================
        # Send POST request to API
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
                    print(f"[DEBUG] API response status: {resp.status}")
                    if resp.status != 200:
                        text = await resp.text()
                        print(f"[DEBUG] API error text: {text}")
                        await ctx.send(f"{edit_error_msg}\n\n`{text}`")
                        return

                    # API already returns the image buffer
                    edited_bytes = await resp.read()
                    print(f"[DEBUG] API response received, length: {len(edited_bytes)} bytes")

        except Exception as e:
            print(f"[DEBUG] API call failed: {e}")
            await ctx.send(f"{edit_error_msg}\n\n`{e}`")
            return

        # ===============================
        # Send final result
        # ===============================
        await ctx.send(
            f"{sending_msg} 🌸\n\nPrompt:\n{texto} 💖",
            file=discord.File(fp=edited_bytes, filename="edited.png")
        )
        print("[DEBUG] Image sent successfully to Discord")


async def setup(bot):
    await bot.add_cog(Edit(bot))
