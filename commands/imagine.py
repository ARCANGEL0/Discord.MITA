import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class Imagine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="imagine",
        description="Gera uma imagem a partir de um prompt."
    )
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.send_message(f"Gerando imagem para: **{prompt}** ... 💭")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://129.146.165.179/createImg",
                    json={"prompt": prompt},
                ) as resp:

                    text = await resp.text()

            # Identifica o JSON dentro da string zoada
            start = text.index("{")
            end = text.rindex("}") + 1
            json_str = text[start:end]
            data = json.loads(json_str)

            await interaction.followup.send(data["response"])

        except Exception as e:
            await interaction.followup.send(f"Ocorreu um erro ❌: `{e}`")

async def setup(bot):
    await bot.add_cog(Imagine(bot))
