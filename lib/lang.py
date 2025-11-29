import discord
from discord.ui import Button, View
from db import db  # seu banco de dados

class LanguageView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="English", style=discord.ButtonStyle.primary)
    async def english(self, interaction: discord.Interaction, button: Button):
        db.set_server_value(str(interaction.guild.id), "language", "EN")
        await interaction.response.edit_message(content="Language set to English ✅", view=None)

    @discord.ui.button(label="Português", style=discord.ButtonStyle.success)
    async def portuguese(self, interaction: discord.Interaction, button: Button):
        db.set_server_value(str(interaction.guild.id), "language", "PT")
        await interaction.response.edit_message(content="Idioma definido para Português ✅", view=None)

async def ask_server_language(bot, guild: discord.Guild):
    # Pega o primeiro canal que o bot pode enviar mensagem
    channel = None
    for c in guild.text_channels:
        if c.permissions_for(guild.me).send_messages:
            channel = c
            break
    if not channel:
        return
    
    await channel.send(
        "> Entãão..~ vamos ver… qual será o idioma deste servidor, hm~ ? 💖\n> Soo~ let’s see… what will be the language of our server, hm~~ 💖?\n\n",
        view=LanguageView()
    )
