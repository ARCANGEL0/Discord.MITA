import aiohttp
import json
import time
import traceback
from db import db

BASE_URL = "http://129.146.165.179/gpt4"

# Mita emojis (use os que você já usa no seu projeto)
MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"

async def handle_mita_mention(message, reference=False):
    """Se a mensagem citar 'mita' ou responder uma mensagem do GPT, chama a API GPT.

    Versão com debug extensivo, retries até resposta <= 4000 chars, e respostas de erro como Mita.
    """
    def dbg(*args):
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        try:
            print("[DEBUG]", ts, *args)
        except Exception:
            # garantir que debug não quebra por qualquer motivo
            pass

    if message.author.bot or message.guild is None:
        dbg("Ignored: author is bot or not in a guild")
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    # Pega idioma do servidor
    try:
        language = db.get_server_value(guild_id, "language", default="EN")
    except Exception as e:
        dbg("Failed to get language from db:", e)
        language = "EN"

    # Mensagens Mita-style de erro (mantendo seu estilo)
    if language == "PT":
        edit_error_msg = f"Ih... Algo deu errado {MITA_CRY}! 🌸 Me perdoa (╥﹏╥), vamos tentar de novo 💖"
    else:
        edit_error_msg = f"Hm… something went wrong {MITA_CRY}! Sorry (╥﹏╥), let’s try again, okay?~ 💖"

    dbg("Preparing prompt for user", message.author.id, message.author.name)

    # system prompt base (sua definição)
    base_system_prompt = """
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

    # garante usuário no db
    try:
        db.ensure_user(guild_id, user_id)
    except Exception as e:
        dbg("Failed to ensure user in DB:", e)

    user = db.get_user(guild_id, user_id)
    hist_gpt = user.get("historico_gpt", [])

    # Monta a entrada do usuário (mantendo o prompt original)
    user_entry = {
        "role": "user",
        "content": (
            f"{base_system_prompt}\n\n"
            f"User Information:\n"
            f"- Username: {message.author.name}\n"
            f"- Client ID: {message.author.id}\n\n"
            f"User Message:\n"
            f"{message.content}\n\n"
            f"Now answer the following user request in "
            f"{'Português' if language == 'PT' else 'English'}."
        )
    }

    hist_gpt.append(user_entry)

    # Debug: tamanho do payload
    try:
        payload_preview = json.dumps({"conversation": hist_gpt[-1]}, ensure_ascii=False)[:1000]
        dbg("Payload preview (truncated):", payload_preview)
    except Exception:
        dbg("Could not preview payload")

    # Loop de requisições até resposta <= 4000 chars
    max_attempts = 10
    attempt = 0
    assistant_response = None

    while attempt < max_attempts:
        attempt += 1
        dbg(f"Attempt {attempt} - sending request to GPT API", BASE_URL)

        # Para forçar o modelo a encurtar quando pedirmos, adicionamos uma instrução temporária
        # que pede explicitamente uma resposta <=4000 chars. Esta entrada NÃO é persistida no hist_gpt original.
        shrink_instruction = {
            "role": "system",
            "content": "Respond in at most 4000 characters. If your full answer would exceed 4000 characters, produce a shorter version that fits within 4000 characters."
        }

        payload_conversation = hist_gpt + [shrink_instruction]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BASE_URL, json={"conversation": payload_conversation}) as resp:
                    dbg("GPT API HTTP status:", resp.status)
                    raw_text = await resp.text()
                    dbg("Raw response length (chars):", len(raw_text))

                    # Tenta interpretar JSON
                    parsed = None
                    try:
                        parsed = json.loads(raw_text)
                    except Exception:
                        parsed = None

                    if parsed and isinstance(parsed, dict) and "response" in parsed:
                        assistant_response = parsed.get("response")
                        dbg("Parsed JSON response received")
                    else:
                        # se API retorna texto puro
                        assistant_response = raw_text
                        dbg("Using raw text as assistant_response")

        except Exception as e:
            dbg("Exception while calling GPT API:", e)
            dbg(traceback.format_exc())
            # responder como Mita ao usuário em caso de falha de chamada
            try:
                await message.reply(edit_error_msg)
            except Exception as send_err:
                dbg("Failed to send Mita-style error reply:", send_err)
            return

        # Se não recebeu nada
        if not assistant_response:
            dbg("assistant_response empty on attempt", attempt)
            # tentar novamente (irá para próxima iteração)
            continue

        # Remove espaços extras e normalize
        assistant_response = assistant_response.strip()
        dbg("Assistant response length (chars):", len(assistant_response))

        # Se adequa ao limite, sai do loop
        if len(assistant_response) <= 4000:
            dbg("Response within limit, proceeding to send to Discord")
            break
        else:
            dbg(f"Response too long ({len(assistant_response)} chars). Retrying (will request shorter version).")
            # loop continuará e fará nova tentativa
            # pequena espera para não spammar a API
            await asyncio.sleep(0.5)

    # Após o loop
    if not assistant_response or len(assistant_response) > 4000:
        dbg("Failed to obtain assistant_response <= 4000 after attempts:", attempt)
        # enviar mensagem de erro como Mita
        try:
            await message.reply(edit_error_msg)
        except Exception as send_err:
            dbg("Failed to send final Mita-style error reply:", send_err)
        return

    # Envia a resposta e salva no histórico com ID
    try:
        dbg("Sending reply to Discord, length:", len(assistant_response))
        sent_msg = await message.reply(assistant_response)
        dbg("Message sent, id:", getattr(sent_msg, 'id', None))

        # Salva no histórico (apende assistant)
        hist_gpt.append({
            "role": "assistant",
            "content": assistant_response,
            "id": sent_msg.id
        })
        user["historico_gpt"] = hist_gpt
        db.save()
        dbg("Saved conversation to DB")

    except Exception as e:
        dbg("Failed to send reply to Discord:", e)
        dbg(traceback.format_exc())
        try:
            await message.reply(edit_error_msg)
        except Exception as send_err:
            dbg("Failed to send fallback Mita error message:", send_err)
        return

    dbg("handle_mita_mention finished successfully")
