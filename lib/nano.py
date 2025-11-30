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