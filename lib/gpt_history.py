from db import db

def register_message(message):
    """Adiciona qualquer mensagem enviada pelo usuário ao histórico"""
    if message.author.bot or message.guild is None:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    db.ensure_user(guild_id, user_id)

    # Inicializa os históricos se não existirem
    user = db.get_user(guild_id, user_id)
    if "historico" not in user:
        user["historico"] = []
    if "historico_gpt" not in user:
        # Inicializa com o mesmo conteúdo do histórico
        user["historico_gpt"] = [{"role": "user", "content": m} for m in user["historico"]]

    # Adiciona a mensagem ao histórico normal
    user["historico"].append(message.content)

    # Se historico_gpt estiver vazio, copia do historico
    if not user["historico_gpt"]:
        user["historico_gpt"].extend([{"role": "user", "content": m} for m in user["historico"]])

    db.save()
