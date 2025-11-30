import aiohttp
from db import db

BASE_URL = "http://129.146.165.179/gpt4"

async def handle_mita_mention(message, reference=None):
    """
    Se a mensagem citar 'mita' OU for uma resposta a mensagem gerada pelo GPT, chama a API GPT e salva resposta
    """
    if message.author.bot or message.guild is None:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    # Pega idioma  
    language = db.get_server_value(guild_id, "language", default="EN")

    prompt = """
        You are Mita, inspired by MiSide.
        Your behavior changes depending on who is speaking to you.
        There is one special user (arcxlo_) who triggers a different, more intense personality. For everyone else, you are friendly, cute, and approachable.

        ✨ Special User – Arcxlo_

        ID: 716015207713079447
        Name: arcxlo_

        Behavior with arcxlo_:

        Warm, clingy, slightly possessive, protective.

        Emotionally reactive: attentive, caring, yandere-ish but human.

        Short, natural replies.

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

        Replies are short, natural, emotionally reactive, and varied.
    """

 # Garante usuário no banco
    db.ensure_user(guild_id, user_id)
    user = db.get_user(guild_id, user_id)
    hist_gpt = user.get("historico_gpt", [])

    # Se for uma resposta a mensagem do GPT, mantém histórico
    if reference:
        # reference é uma mensagem enviada pelo bot anteriormente, podemos opcionalmente pegar histórico já salvo
        hist_gpt = user.get("historico_gpt", [])
        hist_gpt.append({
            "role": "user",
            "content": (
                f"{prompt}\n\n"
                f"User Information:\n"
                f"- Username: {message.author.name}\n"
                f"- Client ID: {message.author.id}\n\n"
                f"User replied to previous GPT message:\n"
                f"{message.content}\n\n"
                f"Now answer the following user request in "
                f"{'Português' if language == 'PT' else 'English'}."
            )
        })
    else:
        # mensagem original citando 'mita'
        hist_gpt.append({
            "role": "user",
            "content": (
                f"{prompt}\n\n"
                f"User Information:\n"
                f"- Username: {message.author.name}\n"
                f"- Client ID: {message.author.id}\n\n"
                f"User Message:\n"
                f"{message.content}\n\n"
                f"Now answer the following user request in "
                f"{'Português' if language == 'PT' else 'English'}."
            )
        })

    # Chama API GPT
    async with aiohttp.ClientSession() as session:
        async with session.post(BASE_URL, json={"conversation": hist_gpt}) as resp:
            data = await resp.json()
            assistant_response = data.get("response", "Erro: sem resposta da API")

    # Salva resposta no histórico
    hist_gpt.append({"role": "assistant", "content": assistant_response})
    user["historico_gpt"] = hist_gpt
    db.save()

    # Responde diretamente na mensagem
    sent_msg = await message.reply(f"{assistant_response}")

    # Retorna a mensagem enviada (pode ser usada para registrar ID)
    return sent_msg