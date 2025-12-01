import discord
from discord.ext import commands
import aiohttp
from db import db 
from lib.nano import nanobanana
import imghdr
import io  # <- importante

MITA_SMILE = "<:mitasmile:1444758849046184069>"
MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"
  
class Edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="edit", aliases=["imagem"])
    async def edit(self, ctx, *, texto=None):
        print("[DEBUG] Command received")
        guild_id = str(ctx.guild.id)
        await ctx.add_reaction("<:loading:1444867632309342289>")

        try:
            language = db.get_server_value(guild_id, "language", default="EN")
        except Exception:
            language = "EN"
        print(f"[DEBUG] Language: {language}")

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

        if not texto:
            print("[DEBUG] No prompt provided")
            await ctx.send(no_text_msg)
            return
        print(f"[DEBUG] Prompt: {texto}")

        image_bytes = None
        image_filename = None

        if ctx.message.attachments:
            att = ctx.message.attachments[0]
            image_bytes = await att.read()
            image_filename = att.filename
            print(f"[DEBUG] Using uploaded attachment: {image_filename} ({len(image_bytes)} bytes)")
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

 
        # ===============================
        # Send POST request
        # ===============================
        try:
            resp = nanobanana(texto,image_bytes)
            edited_bytes = await resp.read()
            print(f"[DEBUG] API response received, length: {len(edited_bytes)} bytes")
            img_type = imghdr.what(None, edited_bytes)
            if not img_type:
                img_type = "jpg"
            print(f"[DEBUG] Detected image type: {img_type}")

        except Exception as e:
        
            try:
                await ctx.add_reaction(MITA_CRY)
            except:
                pass 
            print(f"[DEBUG] API call failed: {e}")
            await ctx.send(f"{edit_error_msg}\n\n`{e}`")
            return

        # ===============================
        # Send final result (wrap bytes in io.BytesIO)
        # ===============================
        try:
            file_buffer = io.BytesIO(edited_bytes)
            await ctx.send(
                f"{sending_msg} 🌸\n\nPrompt:\n{texto} 💖",
                file=discord.File(fp=file_buffer, filename=f"edited.{img_type}")
            )
            print("[DEBUG] Image sent successfully to Discord")
            
            try:
                await ctx.add_reaction(MITA_SMILE)
            except:
                pass 

        except Exception as e:
            try:
                await ctx.add_reaction(MITA_CRY)
            except:
                pass 
            print(f"[DEBUG] Failed to send Discord file: {e}")
            await ctx.send(f"{edit_error_msg}\n\n`{e}`")


async def setup(bot):
    await bot.add_cog(Edit(bot))
