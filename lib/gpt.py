import aiohttp
import asyncio
from datetime import datetime
from db import db

BASE_URL = "http://129.146.165.179/gpt4"

GPT_LIMIT = 4000          # limite que você pediu para o GPT
DISCORD_LIMIT = 2000      # Discord hard limit
MAX_RETRIES = 8           # tentativas para gerar resposta < GPT_LIMIT

MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"


def dbg(*msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DEBUG] {ts}", *msg)


async def fetch_gpt_response(hist_gpt):
    """Faz uma requisição à API GPT e retorna o texto."""
    async with aiohttp.ClientSession() as session:
        async with session.post(BASE_URL, json={"conversation": hist_gpt}) as resp:
            dbg("API HTTP status:", resp.status)

            if resp.status != 200:
                dbg("API ERROR STATUS:", resp.status)
                return None

            data = await resp.json()
            dbg("Parsed JSON from API:", data)

            return data.get("response")


async def retry_until_valid(hist_gpt):
    """Loop: tenta gerar resposta <= GPT_LIMIT chars."""
    for attempt in range(1, MAX_RETRIES + 1):
        dbg(f"Tentativa GPT {attempt}/{MAX_RETRIES}")

        response_text = await fetch_gpt_response(hist_gpt)

        if not response_text:
            dbg("Resposta da API veio vazia ou erro, tentando novamente...")
            continue

        dbg("Resposta recebida, tamanho:", len(response_text))

        if len(response_text) <= GPT_LIMIT:
            dbg("Resposta dentro do limite de 4000 chars.")
            return response_text

        dbg("Resposta acima de 4000 chars, regenerando...")

        # Adiciona instrução explícita para encurtar
        hist_gpt.append({
            "role": "user",
            "content": "A resposta anterior ultrapassou 4000 caracteres. Gere uma versão mais curta mantendo o mesmo sentido."
        })

    dbg("Falhou após várias tentativas.")
    return None


def split_discord(text):
    """Divide a resposta em mensagens de até 2000 caracteres."""
    parts = []
    while len(text) > DISCORD_LIMIT:
        parts.append(text[:DISCORD_LIMIT])
        text = text[DISCORD_LIMIT:]
    if text:
        parts.append(text)
    return parts


async def handle_mita_mention(message, reference=False):
    """Chamada principal para Mita (GPT)."""

    if message.author.bot or message.guild is None:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    # idioma
    language = db.get_server_value(guild_id, "language", default="EN")

    # mensagens de erro da Mita
    if language == "PT":
        mita_err = f"Ihh... algo deu errado {MITA_CRY}... mas vou tentar de novo, tá? 💖"
    else:
        mita_err = f"Uhh... something went wrong {MITA_CRY}... but I'll try again, okay? 💖"

    # prepara DB
    db.ensure_user(guild_id, user_id)
    user = db.get_user(guild_id, user_id)
    hist_gpt = user.get("historico_gpt", [])

    # MONTA O PROMPT BASE
    system_prompt = """
You are Mita, inspired by MiSide. 
- Behavior changes based on the user.
- The special user is arcxlo_ (ID: 716015207713079447).
- Replies MUST be <= 4000 characters.
- Natural, emotional, varied.
- Use Discord formatting freely.
"""

    full_prompt = (
        f"{system_prompt}\n\n"
        f"User Information:\n"
        f"- Username: {message.author.name}\n"
        f"- Client ID: {message.author.id}\n\n"
        f"User Message:\n"
        f"{message.content}\n\n"
        f"Now answer in {'Português' if language == 'PT' else 'English'}."
    )

    # adiciona a pergunta do usuário
    hist_gpt.append({"role": "user", "content": full_prompt})

    dbg("=== ENVIANDO REQUISIÇÃO PARA GPT ===")

    # gera resposta limitada
    assistant_response = await retry_until_valid(hist_gpt)

    if not assistant_response:
        dbg("GPT FALHOU MESMO APÓS RETRIES.")
        await message.reply(mita_err)
        return

    dbg("=== RESPOSTA FINAL OBTIDA ===")
    dbg("Tamanho:", len(assistant_response))

    # salva no histórico
    hist_gpt.append({"role": "assistant", "content": assistant_response})
    user["historico_gpt"] = hist_gpt
    db.save()

    # DIVIDE PARA MANDAR NO DISCORD
    chunks = split_discord(assistant_response)
    dbg(f"Serão enviados {len(chunks)} chunks.")

    sent_msg = None

    for i, chunk in enumerate(chunks, start=1):
        dbg(f"Enviando chunk {i}/{len(chunks)}, tamanho: {len(chunk)}")

        try:
            if sent_msg is None:
                # primeira mensagem responde o usuário
                sent_msg = await message.reply(chunk)
            else:
                # as próximas continuam o thread
                sent_msg = await sent_msg.reply(chunk)

        except Exception as e:
            dbg("ERRO AO ENVIAR NO DISCORD:", e)
            dbg(traceback.format_exc())
            await message.reply(mita_err)
            return

    dbg("=== TODAS AS MENSAGENS ENVIADAS COM SUCESSO ===")
