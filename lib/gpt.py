import aiohttp
from db import db

BASE_URL = "http://129.146.165.179/gpt4"

async def handle_mita_mention(message):
    """Se a mensagem citar 'mita', chama a API GPT e salva resposta"""
    if message.author.bot or message.guild is None:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    # Pega idioma  
    language = db.get_server_value(guild_id, "language", default="EN")

    # Pega histórico GPT
    db.ensure_user(guild_id, user_id)
    user = db.get_user(guild_id, user_id)
    hist_gpt = user.get("historico_gpt", [])

    # Adiciona nova pergunta do usuário
    hist_gpt.append({
        "role": "user",
        "content": f"{message.content}\n\nNow answer the following user request in {'Português' if language=='PT' else 'English'}."
    })

    # Chama API GPT
    async with aiohttp.ClientSession() as session:
        async with session.post(BASE_URL, json={"conversation": hist_gpt}) as resp:
            data = await resp.json()
            assistant_response = data.get("response", "Erro: sem resposta da API")

    # Adiciona a resposta no histórico GPT
    hist_gpt.append({"role": "assistant", "content": assistant_response})
    user["historico_gpt"] = hist_gpt
    db.save()

    # Responde diretamente na mensagem
    await message.reply(f"{assistant_response}")
