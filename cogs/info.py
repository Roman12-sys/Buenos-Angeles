import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Muestra información de un usuario")
    @app_commands.describe(user="El usuario para mostrar información (opcional)")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(title=f"Información de {user}", color=discord.Color.blue())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="Nombre", value=str(user), inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Cuenta creada", value=user.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="Se unió al servidor", value=user.joined_at.strftime("%d/%m/%Y %H:%M:%S") if user.joined_at else "Desconocido", inline=False)
        roles = [role.mention for role in user.roles if role.name != "@everyone"]
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "Ninguno", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="serverinfo", description="Muestra información del servidor")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"Información del servidor: {guild.name}", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        embed.add_field(name="Nombre", value=guild.name, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Dueño", value=str(guild.owner), inline=True)
        embed.add_field(name="Miembros", value=guild.member_count, inline=True)
        embed.add_field(name="Canales", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Creado el", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))
