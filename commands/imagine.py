import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from db import db  # seu helper de banco

# Custom emojis
MITA_SMILE = "<:mitasmile:1444758849046184069>"
MITA_CRY = "<:mitacry:1444760327714504954>"

class Imagine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="imagine",
        description="Gera uma imagem a partir de um prompt."
    )
    async def imagine(self, interaction: discord.Interaction, prompt: str = None):
        guild_id = str(interaction.guild.id)
        language = db.get_server_value(guild_id, "language", default="EN")

        # Caso não tenha prompt
        if not prompt:
            msg = (
                "Humm~ você precisa me dizer o que quer que eu crie, tá? 💖🌸"
                if language == "PT" 
                else "Hehe~ you need to tell me what to create, okay? 💖🌸"
            )
            await interaction.response.send_message(msg)
            return

        # Mensagem inicial
        waiting_msg = (
            f"Humm~ estou pensando no que você pediu: **{prompt}**… 💖" 
            if language == "PT" 
            else f"Hehe~ thinking about your request: **{prompt}**… 💖"
        )
        await interaction.response.send_message(waiting_msg)
        sent_msg = await interaction.original_response()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://129.146.165.179/createImg",
                    json={"prompt": prompt},
                ) as resp:
                    text = await resp.text()

            # Extrai JSON do texto estranho
            start = text.index("{")
            end = text.rindex("}") + 1
            json_str = text[start:end]
            data = json.loads(json_str)

            # Mensagem final
            final_msg = (
                f"Sua imagem ficou prontinha! 💖\n{data['response']}" 
                if language == "PT" 
                else f"Your image is ready! 💖\n{data['response']}"
            )

            # Envia a resposta
            followup = await interaction.followup.send(final_msg)

            # Reage à mensagem com emoji da Mita
            emoji = discord.utils.get(interaction.guild.emojis, name="mitasmile")
            if emoji:
                await followup.add_reaction(emoji)

        except Exception as e:
            error_msg = (
                f"Ocorreu um errinho ❌: `{e}`"
                if language == "PT"
                else f"Oops, something went wrong ❌: `{e}`"
            )
            fail_msg = await interaction.followup.send(error_msg)

            # Reage com emoji de choro da Mita
            emoji = discord.utils.get(interaction.guild.emojis, name="mitacry")
            if emoji:
                await fail_msg.add_reaction(emoji)


async def setup(bot):
    await bot.add_cog(Imagine(bot))
