import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import asyncio

LOG_CATEGORY_NAME = "Logs del servidor"
LOG_CHANNEL_NAME = "registro-actividades"
ADMIN_ROLE_NAME = "Admin"

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None

    async def cog_load(self):
        await self.initialize_log_channel()

    async def initialize_log_channel(self):
        if not self.bot.guilds:
            return
        guild = self.bot.guilds[0]
        category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
        if category is None:
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            category = await guild.create_category(LOG_CATEGORY_NAME, overwrites=overwrites)
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME, category=category)
        if channel is None:
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            channel = await guild.create_text_channel(LOG_CHANNEL_NAME, category=category, overwrites=overwrites)
        self.log_channel = channel

    @app_commands.command(name="logs", description="Configura el canal y categoría de logs del servidor")
    async def logs(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
            return
        await self.initialize_log_channel()
        await interaction.response.send_message(f"✅ Canal de logs configurado: {self.log_channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None or self.log_channel is None:
            return
        embed = discord.Embed(title="Mensaje eliminado", color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenido", value=message.content or "No disponible", inline=False)
        embed.set_footer(text=f"ID del mensaje: {message.id}")
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.guild is None or self.log_channel is None:
            return
        user = member
        if user is None or user.bot:
            return
        embed = discord.Embed(color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        if before.channel is None and after.channel is not None:
            embed.title = "Usuario entró a canal de voz"
            embed.description = f"{user.mention} entró a {after.channel.mention}"
        elif before.channel is not None and after.channel is None:
            embed.title = "Usuario salió de canal de voz"
            embed.description = f"{user.mention} salió de {before.channel.mention}"
        elif before.channel != after.channel:
            embed.title = "Usuario cambió de canal de voz"
            embed.description = f"{user.mention} se movió de {before.channel.mention} a {after.channel.mention}"
        else:
            return
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.log_channel is None:
            return
        embed = discord.Embed(title="Usuario entró al servidor", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.description = f"{member.mention} ha entrado al servidor."
        await self.log_channel.send(embed=embed)
        await self.update_status()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if self.log_channel is None:
            return
        embed = discord.Embed(title="Usuario salió del servidor", color=discord.Color.orange(), timestamp=datetime.utcnow())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.description = f"{member.mention} ha salido del servidor."
        await self.log_channel.send(embed=embed)
        await self.update_status()

    async def update_status(self):
        if not self.bot.guilds:
            return
        guild = self.bot.guilds[0]
        member_count = guild.member_count
        activity = discord.Game(name=f"Jugando con {member_count} miembros")
        await asyncio.sleep(1)
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

async def setup(bot):
    await bot.add_cog(Logs(bot))
