import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from db import db  # seu helper de banco

# Custom emojis
MITA_SMILE = "<:mitasmile:1444758849046184069>"
MITA_CRY = "<:mitacry:1444760327714504954>"
MITA_COOL = "<:mitaglasses:1444759883990962269>"    
       
class Imagine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="imagine",
        description=f"Make an image with AI "
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
            f"Humm~ então você quer que eu desenha algo tipo:\n```plaintext\n**{prompt}**… \n```\n Pode deixar! 💖" 
            if language == "PT" 
            else f"Okiee~~, soo, you want me to make something like:\n ```plaintext\n**{prompt}**…\n```\n Got it! 💖"
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
                f"Tadaa~~! <:mitasmile:1444758849046184069> Sua imagem ficou prontinha! Entãão~.. gostou? 💖\n{data['response']}" 
                if language == "PT" 
                else f"Tadaa~! <:mitasmile:1444758849046184069> Your image is ready!! Soo~ did you liked it? 💖\n{data['response']}"
            )

            # Envia a resposta
            followup = await interaction.followup.send(final_msg)

            # Reage à mensagem com emoji da Mita
            emoji = discord.utils.get(interaction.guild.emojis, name="mitasmile")
            if emoji:
                await followup.add_reaction(emoji)

        except Exception as e:
            error_msg = (
                f"ih...Ocorreu um errinho  <:mitacry:1444760327714504954> ❌: `{e}`"
                if language == "PT"
                else f"Oops, something went wrong <:mitacry:1444760327714504954> ❌: `{e}`"
            )
            fail_msg = await interaction.followup.send(error_msg)

            # Reage com emoji de choro da Mita
            emoji = discord.utils.get(interaction.guild.emojis, name="mitacry")
            if emoji:
                await fail_msg.add_reaction(emoji)


async def setup(bot):
    await bot.add_cog(Imagine(bot))
