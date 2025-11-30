from lib.uploadImage import upload_image
from db import db
import aiohttp
import urllib.parse

API_KEY = "syOYUG" # essa e minha chave API pra autenticacao

async def editar_imagem(texto: str, imagem_url: str) -> str:
    # codifica o texto pra usar na URL
    prompt = urllib.parse.quote(texto)
    img = urllib.parse.quote(imagem_url)
    # url abaixo com o prompt

    url = f"https://api.alyachan.dev/api/ai-edit?image={img}&prompt={prompt}&apikey={API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            # tenta pegar a url da imagem editada
            try:
                return data["data"]["images"][0]["url"]
            except:
                raise Exception("API não retornou imagem editada.")
            
@bot.command(name="edit")
async def edit(ctx, *, texto=None):
    guild_id = str(ctx.guild.id)
    language = db.get_server_value(guild_id, "language", default="EN")

    # Mensagens estilo Mita, fofinhas e gentis
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

    # lê a imagem enviada e salva em buffer
    buffer = await ctx.message.attachments[0].read()

    # upload pra pegar URL
    original_url = await upload_image(buffer)

    # chama a API de edição com o link da imagem
    editada_url = await editar_imagem(texto, original_url)

    # envia de volta pro Discord com jeitinho Mita
    await ctx.send(f"{sending_msg} 🌸\n{editada_url}\n\nPrompt:\n{texto} 💖")
