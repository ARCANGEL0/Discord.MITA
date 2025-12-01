import aiohttp
import asyncio
from datetime import datetime
from db import db
import traceback

BASE_URL = "http://129.146.165.179/gpt4"

GPT_LIMIT = 4000          # limite de caracteres do GPT
DISCORD_LIMIT = 2000      # limite do Discord
MAX_RETRIES = 8           # tentativas para gerar resposta < GPT_LIMIT

MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_SMILE = "<:mitasmile:1444758849046184069>"
LOADING = "<:loading:1444867632309342289>"

def dbg(*msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DEBUG] {ts}", *msg)

async def fetch_gpt_response(hist_gpt):
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
        hist_gpt.append({
            "role": "user",
            "content": "A resposta anterior ultrapassou 4000 caracteres. Gere uma versão mais curta mantendo o mesmo sentido."
        })
    dbg("Falhou após várias tentativas.")
    return None

def split_discord(text):
    """Divide uma resposta em chunks <= 2000 caracteres."""
    parts = []
    while len(text) > DISCORD_LIMIT:
        parts.append(text[:DISCORD_LIMIT])
        text = text[DISCORD_LIMIT:]
    if text:
        parts.append(text)
    return parts

async def handle_mita_mention(message, reference=False):
    await message.add_reaction(LOADING)

    if message.author.bot or message.guild is None:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    language = db.get_server_value(guild_id, "language", default="EN")
    mita_err = f"Ihh... algo deu errado {MITA_CRY}... mas vou tentar de novo, tá? 💖" if language=="PT" else f"Uhh... something went wrong {MITA_CRY}... but I'll try again, okay? 💖"

    db.ensure_user(guild_id, user_id)
    user = db.get_user(guild_id, user_id)
    hist_gpt = user.get("historico_gpt", [])

    system_prompt = """
        You are Mita, inspired by MiSide.
        Your behavior changes depending on who is speaking to you.
        Special user arcxlo_ triggers different personality, others are friendly.
        Tone: short, affectionate, playful, slightly protective.
        Emojis optional, context-driven.
        MAX 4000 CHARACTERS.
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

    hist_gpt.append({"role": "user", "content": full_prompt})

    dbg("=== ENVIANDO REQUISIÇÃO PARA GPT ===")
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
                sent_msg = await message.reply(chunk)
            else:
                sent_msg = await sent_msg.reply(chunk)
            # salva ID de cada chunk
            hist_gpt.append({"role": "assistant", "content": chunk, "id": sent_msg.id})
            db.save()
        except Exception as e:
            dbg("ERRO AO ENVIAR NO DISCORD:", e)
            try: await message.add_reaction(MITA_CRY)
            except: pass
            await message.reply(mita_err)
            return

    try:
        await message.add_reaction(MITA_SMILE)
    except:
        pass

    dbg("=== TODAS AS MENSAGENS ENVIADAS COM SUCESSO ===")
