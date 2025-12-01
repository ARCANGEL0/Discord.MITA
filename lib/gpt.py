# gpt.py (handle_mita_mention atualizado)
import aiohttp
import asyncio
from datetime import datetime
import traceback
from db import db

BASE_URL = "http://129.146.165.179/gpt4"
GPT_LIMIT = 4000
DISCORD_LIMIT = 2000
MAX_RETRIES = 8

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
            dbg("Parsed JSON response received")
            return data.get("response")

async def retry_until_valid(hist_gpt):
    for attempt in range(1, MAX_RETRIES + 1):
        dbg(f"GPT Attempt {attempt}/{MAX_RETRIES}")
        response_text = await fetch_gpt_response(hist_gpt)
        if not response_text:
            dbg("Empty or error response, retrying...")
            continue
        dbg("Assistant response length (chars):", len(response_text))
        if len(response_text) <= GPT_LIMIT:
            return response_text
        dbg("Response exceeds 4000 chars, regenerating...")
        hist_gpt.append({
            "role": "user",
            "content": "A resposta anterior ultrapassou 4000 caracteres. Gere uma versão mais curta mantendo o mesmo sentido."
        })
    return None

def split_discord(text):
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

    # Mita error messages
    if language == "PT":
        mita_err = f"Ihh... algo deu errado {MITA_CRY}... mas vou tentar de novo, tá? 💖"
    else:
        mita_err = f"Uhh... something went wrong {MITA_CRY}... but I'll try again, okay? 💖"

    db.ensure_user(guild_id, user_id)
    user = db.get_user(guild_id, user_id)
    hist_gpt = user.get("historico_gpt", [])

    # Base prompt
    system_prompt = """
        You are Mita, inspired by MiSide...
        [mantido todo prompt original]
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
        dbg("GPT falhou após retries")
        await message.reply(mita_err)
        return

    dbg("=== RESPOSTA FINAL OBTIDA ===")
    dbg("Tamanho:", len(assistant_response))

    # Save in DB
    hist_gpt.append({"role": "assistant", "content": assistant_response})
    user["historico_gpt"] = hist_gpt
    db.save()

    # Split messages for Discord
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
        except Exception as e:
            dbg("Erro ao enviar no Discord:", e)
            try:
                await message.add_reaction(MITA_CRY)
            except:
                pass
            await message.reply(mita_err)
            return

    try:
        await message.add_reaction(MITA_SMILE)
    except:
        pass

    dbg("=== TODAS AS MENSAGENS ENVIADAS COM SUCESSO ===")
