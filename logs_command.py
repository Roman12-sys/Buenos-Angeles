import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from datetime import datetime

LOG_CATEGORY_NAME = "Logs del servidor"
LOG_CHANNEL_NAME = "registro-actividades"
ADMIN_ROLE_NAME = "Admin"

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None

    async def initialize_log_channel(self):
        if not self.bot.guilds:
            return
        guild = self.bot.guilds[0]
        category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
        if category is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            category = await guild.create_category(LOG_CATEGORY_NAME, overwrites=overwrites)

        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME, category=category)
        if channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            channel = await guild.create_text_channel(LOG_CHANNEL_NAME, category=category, overwrites=overwrites)
        self.log_channel = channel

    async def create_log_category_and_channel(self, guild: discord.Guild):
        # Check if category exists
        category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
        if category is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            # Find admin role
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            category = await guild.create_category(LOG_CATEGORY_NAME, overwrites=overwrites)

        # Check if channel exists
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME, category=category)
        if channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            channel = await guild.create_text_channel(LOG_CHANNEL_NAME, category=category, overwrites=overwrites)
        self.log_channel = channel
        return channel

import asyncio

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None

    async def initialize_log_channel(self):
        if not self.bot.guilds:
            return
        guild = self.bot.guilds[0]
        category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
        if category is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            category = await guild.create_category(LOG_CATEGORY_NAME, overwrites=overwrites)

        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME, category=category)
        if channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            channel = await guild.create_text_channel(LOG_CHANNEL_NAME, category=category, overwrites=overwrites)
        self.log_channel = channel

    async def create_log_category_and_channel(self, guild: discord.Guild):
        # Check if category exists
        category = discord.utils.get(guild.categories, name=LOG_CATEGORY_NAME)
        if category is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            # Find admin role
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            category = await guild.create_category(LOG_CATEGORY_NAME, overwrites=overwrites)

        # Check if channel exists
        channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME, category=category)
        if channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            admin_role = discord.utils.get(guild.roles, name=ADMIN_ROLE_NAME)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            channel = await guild.create_text_channel(LOG_CHANNEL_NAME, category=category, overwrites=overwrites)
        self.log_channel = channel
        return channel

    async def update_status(self):
        print("DEBUG: update_status called")
        # Update the bot's status with the total member count of the first guild
        if not self.bot.guilds:
            print("DEBUG: No guilds found")
            return
        guild = self.bot.guilds[0]
        member_count = guild.member_count
        print(f"DEBUG: Setting presence with member count {member_count}")
        activity = discord.Game(name=f"Jugando con {member_count} miembros")
        await asyncio.sleep(1)  # small delay to ensure connection is ready
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @app_commands.command(name="logs", description="Configura el canal y categoría de logs del servidor")
    async def logs(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
            return
        channel = await self.create_log_category_and_channel(guild)
        await interaction.response.send_message(f"✅ Canal de logs configurado: {channel.mention}", ephemeral=True)

    async def log_message_delete(self, message: discord.Message):
        if message.guild is None or self.log_channel is None:
            return
        embed = discord.Embed(title="Mensaje eliminado", color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Contenido", value=message.content or "No disponible", inline=False)
        embed.set_footer(text=f"ID del mensaje: {message.id}")
        await self.log_channel.send(embed=embed)

    async def log_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
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

    async def log_member_join(self, member: discord.Member):
        if self.log_channel is None:
            return
        embed = discord.Embed(title="Usuario entró al servidor", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.description = f"{member.mention} ha entrado al servidor."
        await self.log_channel.send(embed=embed)
        await self.update_status()

    async def log_member_remove(self, member: discord.Member):
        if self.log_channel is None:
            return
        embed = discord.Embed(title="Usuario salió del servidor", color=discord.Color.orange(), timestamp=datetime.utcnow())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.description = f"{member.mention} ha salido del servidor."
        await self.log_channel.send(embed=embed)
        await self.update_status()

    async def log_member_ban(self, guild: discord.Guild, user: discord.User):
        if self.log_channel is None:
            return
        embed = discord.Embed(title="Usuario baneado", color=discord.Color.dark_red(), timestamp=datetime.utcnow())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url if hasattr(user, 'display_avatar') else None)
        embed.description = f"{user.mention} ha sido baneado del servidor."
        await self.log_channel.send(embed=embed)

    async def log_member_unban(self, guild: discord.Guild, user: discord.User):
        if self.log_channel is None:
            return
        embed = discord.Embed(title="Usuario desbaneado", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url if hasattr(user, 'display_avatar') else None)
        embed.description = f"{user.mention} ha sido desbaneado del servidor."
        await self.log_channel.send(embed=embed)

    async def log_member_update(self, before: discord.Member, after: discord.Member):
        # Detect guild mute/unmute changes
        if self.log_channel is None:
            return
        if before.guild is None:
            return
        if before.bot:
            return

        # Check if guild mute changed
        if before.voice and after.voice:
            if before.voice.mute != after.voice.mute:
                embed = discord.Embed(title="Usuario silenciado/desilenciado", color=discord.Color.dark_orange(), timestamp=datetime.utcnow())
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                status = "silenciado" if after.voice.mute else "desilenciado"
                embed.description = f"{after.mention} ha sido {status} en el canal de voz {after.voice.channel.mention}."
                await self.log_channel.send(embed=embed)

async def setup_logs(bot_client):
    logs_cog = Logs(bot_client)
    await bot_client.add_cog(logs_cog)
    await logs_cog.initialize_log_channel()

    @bot_client.event
    async def on_ready():
        await logs_cog.update_status()

    @bot_client.event
    async def on_message_delete(message):
        await logs_cog.log_message_delete(message)

    @bot_client.event
    async def on_voice_state_update(member, before, after):
        await logs_cog.log_voice_state_update(member, before, after)

    @bot_client.event
    async def on_member_join(member):
        await logs_cog.log_member_join(member)

    @bot_client.event
    async def on_member_remove(member):
        await logs_cog.log_member_remove(member)

    @bot_client.event
    async def on_member_ban(guild, user):
        await logs_cog.log_member_ban(guild, user)

    @bot_client.event
    async def on_member_unban(guild, user):
        await logs_cog.log_member_unban(guild, user)

    @bot_client.event
    async def on_member_update(before, after):
        await logs_cog.log_member_update(before, after)
