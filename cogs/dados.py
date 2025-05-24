import discord
from discord import app_commands
from discord.ext import commands
import random

class Dados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dados", description="Tira un número al azar del 1 al 100")
    async def dados(self, interaction: discord.Interaction):
        numero = random.randint(1, 100)
        await interaction.response.send_message(f"🎲 Has sacado un {numero} en el dado.")

async def setup(bot):
    await bot.add_cog(Dados(bot))