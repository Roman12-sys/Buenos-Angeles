import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Muestra la lista de comandos disponibles para usuarios y administradores")
    async def help(self, interaction: discord.Interaction):
        user_commands = []
        admin_commands = []

        for command in self.bot.tree.walk_commands():
            if command.description:
                is_admin = bool(command.checks)  # If has checks, it's admin
                if is_admin:
                    admin_commands.append(f"• /{command.name}: {command.description}")
                else:
                    user_commands.append(f"• /{command.name}: {command.description}")

        embed = discord.Embed(title="📖 Lista de comandos disponibles", color=discord.Color.blue())
        if user_commands:
            embed.add_field(name="👤 Comandos para usuarios", value="\n".join(user_commands), inline=False)
        else:
            embed.add_field(name="👤 Comandos para usuarios", value="No hay comandos disponibles.", inline=False)
        if admin_commands:
            embed.add_field(name="🛠️ Comandos para administradores", value="\n".join(admin_commands), inline=False)
        else:
            embed.add_field(name="🛠️ Comandos para administradores", value="No existen aún.", inline=False)

        embed.set_footer(text=f"Solicitado por {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
