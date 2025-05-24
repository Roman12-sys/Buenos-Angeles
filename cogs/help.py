import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Muestra la lista de comandos disponibles para administradores")
    @app_commands.checks.has_permissions(administrator=True)
    async def help(self, interaction: discord.Interaction):
        commands_list = []
        for command in self.bot.tree.walk_commands():
            if command.description:
                commands_list.append(f"**/{command.name}**: {command.description}")
        embed = discord.Embed(title="Lista de comandos disponibles", color=discord.Color.blue())
        embed.description = "\n".join(commands_list) if commands_list else "No hay comandos disponibles."
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
