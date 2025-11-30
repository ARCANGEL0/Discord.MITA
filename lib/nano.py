import aiohttp
import urllib.parse
from db import db

API_KEY = "syOYUG"  # sua chave API

async def editar_imagem(texto: str, imagem_url: str, guild_id: str = None) -> str:
    """
    Edita uma imagem via API externa.
    Se guild_id for fornecido, usa o idioma do servidor para mensagens de erro.
    """
    # define idioma
    language = "EN"
    if guild_id:
        language = db.get_server_value(guild_id, "language", default="EN")

    messages = {
        "PT": {
            "requesting": "Hm~ 🌸 estou processando sua obra de arte… 💖",
            "error": "Ops~ 🌸 algo deu errado ao editar a imagem… 💖"
        },
        "EN": {
            "requesting": "Hehe~ 🌸 I’m processing your masterpiece… 💖",
            "error": "Oops~ 🌸 something went wrong while editing the image… 💖"
        }
    }

    msgs = messages.get(language, messages["EN"])

    # codifica texto e imagem para URL
    prompt = urllib.parse.quote(texto)
    img = urllib.parse.quote(imagem_url)
    url = f"https://api.alyachan.dev/api/ai-edit?image={img}&prompt={prompt}&apikey={API_KEY}"

    print(msgs["requesting"])
    print(f"Making request to\n>> {url}\n")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                data = await resp.json()

                # tenta pegar a url da imagem editada
                try:
                    return data["data"]["images"][0]["url"]
                except (KeyError, IndexError):
                    raise Exception(msgs["error"])
        except Exception as e:
            raise Exception(f"{msgs['error']}\nDetalhes: {e}")
