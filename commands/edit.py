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
        description=f"Edit an image using AI {MITA_COOL} \n Edita uma imagem usando IA {MITA_COOL}"
    )                     
    async def edit(self, ctx: discord.Interaction, texto: str):                                 
        """Edits an image based on the provided prompt."""                    
        guild_id = str(ctx.guild.id)                                          
                                                                              
        try:                                                                  
            language = db.get_server_value(guild_id, "language", default="EN")
        except Exception:                                                     
            language = "EN"                                                   
                                                                              
        # Mensagens originais preservadas                                  
        if language == "PT":                                                  
            no_image_msg = "Hm~ 🌸 parece que não tem imagem junto! Manda a imagem junto com `.edit`, tá~? 💖"                                              
            sending_msg = f"Tcharam~ {MITA_COOL} Sua obra de arte ficou prontinha! 💖"  
            edit_error_msg = f"Ih... Algo deu errado ao editar {MITA_CRY}! 🌸 Me perdoa (╥﹏╥), vamos tentar de novo 💖"                                                         
        else:
            no_image_msg = "Hm~ 🌸 Looks like there’s no image! Please send the image along with `.edit`~ 💖"
            sending_msg = f"Tada~ {MITA_COOL} Your masterpiece is ready! 💖"
            edit_error_msg = "Hm… something went wrong while editing {MITA_CRY}! Sorry (╥﹏╥), let’s try again, okay?~ 💖"
                                                                              
        # ------------------------------------------
        # PEGAR A IMAGEM (attachment ou selecionada)
        # ------------------------------------------
        image_bytes = None
        image_filename = None

        # A) imagem enviada junto ao comando
        if ctx.attachments:
            att = ctx.attachments[0]
            image_bytes = await att.read()
            image_filename = att.filename

        # B) imagem selecionada (message reference)
        elif ctx.data.get("resolved") and ctx.data["resolved"].get("attachments"):
            ref_att = next(iter(ctx.data["resolved"]["attachments"].values()))
            async with aiohttp.ClientSession() as session:
                async with session.get(ref_att["url"]) as resp:
                    image_bytes = await resp.read()
                    image_filename = ref_att["filename"]

        if not image_bytes:
            await ctx.response.send_message(no_image_msg)
            return

        await ctx.response.send_message("🌸")  # mantém sua reação/resposta inicial
                                                                              
        # ------------------------------------------
        # POST para o endpoint /imagedit
        # ------------------------------------------
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
            await ctx.followup.send(f"{edit_error_msg}\n\n`{e}`")
            return

        # ------------------------------------------
        # Enviar imagem final ao Discord
        # ------------------------------------------
        await ctx.followup.send(
            f"{sending_msg} 🌸\n\nPrompt:\n{texto} 💖",
            file=discord.File(edited_bytes, filename="edited.png")
        )
                                                                              
async def setup(bot):                                                         
    await bot.add_cog(Edit(bot))
