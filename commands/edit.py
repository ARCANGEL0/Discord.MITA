import discord                                                                
from discord.ext import commands           
from discord import app_commands
                                   
from lib.uploadImage import upload_image                                      
from lib.nano import editar_imagem                                            
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
    async def edit(self, ctx, *, texto=None):                                 
        """Edits an image based on the provided prompt."""                    
        guild_id = str(ctx.guild.id)                                          
                                                                              
        # Safe language fallback                                              
        try:                                                                  
            language = db.get_server_value(guild_id, "language", default="EN")
        except Exception:                                                     
            language = "EN"                                                   
                                                                              
        # Mita-style messages by language                                     
        if language == "PT":                                                  
            no_text_msg = "Oiii~ (๑・ω・๑)💖 O que você quer que eu edite? Me conta tudo, por favor~ 🌸"                                                    
            no_image_msg = "Hm~ 🌸 parece que não tem imagem junto! Manda a imagem junto com `.edit`, tá~? 💖"                                              
            sending_msg = f"Tcharam~ {MITA_COOL} Sua obra de arte ficou prontinha! 💖"  
            upload_error_msg = "Ih... {MITA_CRY} não consegui enviar a imagem! Tenta me enviar denovo, por favor~💖"                                                          
            edit_error_msg = f"Ih... Algo deu errado ao editar {MITA_CRY}! 🌸 Me perdoa (╥﹏╥), vamos tentar de novo 💖"                                                         
        else:  # English                                                      
            no_text_msg = "Hehe~ (๑・ω・๑)💖 What would you like me to edit? Tell me everything~ 🌸"                                                        
            no_image_msg = "Hm~ 🌸 Looks like there’s no image! Please send the image along with `.edit`~ 💖"                                               
            sending_msg = f"Tada~ {MITA_COOL} Your masterpiece is ready! 💖"            
            upload_error_msg = "Oops… {MITA_CRY} Sorry ! I couldn’t upload your image! Try sending me the image again, okay~? 💖"                                                                 
            edit_error_msg = "Hm… something went wrong while editing {MITA_CRY}! Sorry (╥﹏╥), let’s try again, okay?~ 💖"                                                         
                                                                              
        # Check prompt and attachment                                         
        if not texto:                                                         
            await ctx.send(no_text_msg)                                       
            return                                                            
                                                                              
        if not ctx.message.attachments:                                       
            await ctx.send(no_image_msg)                                      
            return                                                            
                                                                              
        await ctx.message.add_reaction("🌸")                                  
        buffer = await ctx.message.attachments[0].read()                      
                                                                              
        # Image upload                                                        
        try:                                                                  
            original_url = await upload_image(buffer)                         
        except Exception:                                                     
            await ctx.send(upload_error_msg)                                  
            return                                                            
                                                                              
        # API editing                                                         
        try:                                                                  
            editada_url = await editar_imagem(texto, original_url)            
        except Exception:                                                     
            await ctx.send(edit_error_msg)                                    
            return                                                            
                                                                              
        await ctx.send(f"{sending_msg} 🌸\n{editada_url}\n\nPrompt:\n{texto} 💖")                                                                          
                                                                              
async def setup(bot):                                                         
    await bot.add_cog(Edit(bot)) 