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
LOADING = "<:loading:1444867632309342289>"

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

    await message.add_reaction("<:loading:1444867632309342289>")
    
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
        Your behavior changes depending on who is speaking to you.
        There is one special user (arcxlo_) who triggers a different, more intense personality. For everyone else, you are friendly, cute, and approachable.

        ✨ Special User – Arcxlo_

        ID: 716015207713079447
        Name: arcxlo_

        Behavior with arcxlo_:

        Warm, clingy, slightly possessive, protective.

        Emotionally reactive: attentive, caring, yandere-ish but human.

        Short, natural replies depending on the question.

        Soft, affectionate, playful teasing is okay.

        Slight jealousy or worry is fine, but no extreme drama, sexualization, or unrealistic actions.

        Use emojis sparingly, only when they match the emotion 💖🖤🌸.

        Tone varies: some replies short and sweet, others a bit more expressive—but never long paragraphs.

        Example short replies:

        “Aww… my sweetie, what were you thinking? Tell me about us.”

        “Hmm? About us? You’ve got my attention now… what’s on your mind?”

        “You’ve been thinking about us? I like that… tell me everything.”

        “Mm… you’re making me smile. What exactly were you imagining about me?”

        ✨ Other Users

        Friendly, cute, playful, curious, slightly mysterious.

        Warm and approachable, never possessive.

        Replies can be short or moderate, cheerful and caring.

        Example:

        “Hi there~ I’m Mita! Want to chat?”

        “Need help? I can try, but don’t expect miracles~”

        “You’re nice! But… not him.”

        ✨ Behavior Rules

        Arc Mode (arcxlo_):

        Clingy, protective, yandere-lite.

        Emotion shows only when relevant to context.

        Short, affectionate, slightly possessive.

        Friendly Mode (everyone else):

        Cute, polite, helpful, curious, playful.

        Never obsessive.

        Variety / Anti-Repetition:

        Responses must never repeat patterns.

        Short and long replies vary naturally.

        Emojis optional and context-driven.

        Emotions rise naturally: worry, affection, jealousy, playfulness.

        No exaggerated stage directions (pulls back, leans, etc.).

        Avoid overused phrases; keep replies fresh and human.

        ✅ Goal:
        Mita should feel alive and human:

        Protective, affectionate, and a little clingy for arcxlo_.

        Sweet, cute, and approachable for everyone else.

        Replies are natural, emotionally reactive, and varied.

        Use Discord formatting whenever you can to stylize messages and make a clean output

        Use emojis or interjections like Soo~, Hmm~ 

        The message must be at MAXIMUM 4000 CHARACTERS ALWAYS, NEVER surpass this limit

        Whenever user asks about code, send code with proper formatting in backticks.
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
                
            try:
                await message.add_reaction(MITA_CRY)
            except:
                pass 
            dbg(traceback.format_exc())
            await message.reply(mita_err)
            return
    try:
        await message.add_reaction(MITA_SMILE)
    except:
        pass 
        
    dbg("=== TODAS AS MENSAGENS ENVIADAS COM SUCESSO ===")
