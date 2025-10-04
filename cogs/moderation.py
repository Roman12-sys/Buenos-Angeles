import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import re
from utils.common import load_json, save_json, parse_time, format_time
import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = load_json('warnings.json')
        self.config = load_json('moderation_config.json')
        self.temp_roles = load_json('temp_roles.json')
        self.bot.loop.create_task(self.check_temp_roles())

    async def check_temp_roles(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            current_time = asyncio.get_event_loop().time()
            to_remove = []
            for guild_id, roles in self.temp_roles.items():
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    continue
                for user_id, role_data in roles.items():
                    if current_time >= role_data['end_time']:
                        member = guild.get_member(int(user_id))
                        role = guild.get_role(role_data['role_id'])
                        if member and role:
                            await member.remove_roles(role)
                        to_remove.append((guild_id, user_id))
            for guild_id, user_id in to_remove:
                del self.temp_roles[guild_id][user_id]
                if not self.temp_roles[guild_id]:
                    del self.temp_roles[guild_id]
            save_json('temp_roles.json', self.temp_roles)
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        auto_role_id = self.config.get(str(member.guild.id), {}).get('auto_role_id')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        guild_config = self.config.get(str(message.guild.id), {})
        banned_words = guild_config.get('banned_words', [])
        anti_links = guild_config.get('anti_links', False)
        anti_spam = guild_config.get('anti_spam', False)

        content = message.content.lower()
        if banned_words and any(word in content for word in banned_words):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, mensaje eliminado por palabra prohibida.")
            return

        if anti_links and re.search(r'http[s]?://', content):
            await message.delete()
            await message.channel.send(f"{message.author.mention}, links no permitidos.")
            return

        # Simple anti-spam: if more than 5 messages in 10 seconds, warn
        if anti_spam:
            # This is basic, in real use, track per user
            pass  # Placeholder

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_event(member.guild, f"👋 {member} se fue del servidor.")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.log_event(guild, f"🚫 {user} fue baneado.")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.log_event(guild, f"✅ {user} fue desbaneado.")

    async def log_event(self, guild, message):
        log_channel_id = self.config.get(str(guild.id), {}).get('log_channel_id')
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                await channel.send(message)

    @app_commands.command(name="mute", description="Silencia a un usuario temporalmente")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, usuario: discord.Member, tiempo: str, razon: str = "Sin razón"):
        try:
            seconds = parse_time(tiempo)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return
        duration = datetime.timedelta(seconds=seconds)
        await usuario.timeout(duration, reason=razon)
        await interaction.response.send_message(f"🔇 {usuario} silenciado por {format_time(seconds)}. Razón: {razon}")
        await self.log_event(interaction.guild, f"🔇 {usuario} silenciado por {interaction.user}. Razón: {razon}")

    @app_commands.command(name="unmute", description="Quita el silencio a un usuario")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, usuario: discord.Member):
        await usuario.timeout(None)
        await interaction.response.send_message(f"🔊 {usuario} ya no está silenciado.")
        await self.log_event(interaction.guild, f"🔊 {usuario} desilenciado por {interaction.user}.")

    @app_commands.command(name="kick", description="Expulsa a un usuario")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
        await usuario.kick(reason=razon)
        await interaction.response.send_message(f"👢 {usuario} expulsado. Razón: {razon}")
        await self.log_event(interaction.guild, f"👢 {usuario} expulsado por {interaction.user}. Razón: {razon}")

    @app_commands.command(name="ban", description="Banea a un usuario")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
        await usuario.ban(reason=razon)
        await interaction.response.send_message(f"🚫 {usuario} baneado. Razón: {razon}")
        await self.log_event(interaction.guild, f"🚫 {usuario} baneado por {interaction.user}. Razón: {razon}")

    @app_commands.command(name="advertencia", description="Registra una advertencia")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def advertencia(self, interaction: discord.Interaction, usuario: discord.Member, razon: str):
        user_id = str(usuario.id)
        if user_id not in self.warnings:
            self.warnings[user_id] = []
        self.warnings[user_id].append({'reason': razon, 'by': str(interaction.user.id), 'time': str(datetime.datetime.now())})
        save_json('warnings.json', self.warnings)
        count = len(self.warnings[user_id])
        await interaction.response.send_message(f"⚠️ Advertencia registrada para {usuario}. Total: {count}")
        if count >= 3:
            await interaction.followup.send("Usuario tiene 3+ advertencias. Considera acción adicional.", ephemeral=True)

    @app_commands.command(name="anuncio", description="Envía un anuncio en un canal")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def anuncio(self, interaction: discord.Interaction, canal: discord.TextChannel, mensaje: str):
        embed = discord.Embed(title="📢 Anuncio", description=mensaje, color=discord.Color.red())
        embed.set_footer(text=f"Anunciado por {interaction.user}")
        await canal.send(embed=embed)
        await interaction.response.send_message("✅ Anuncio enviado.", ephemeral=True)

    @app_commands.command(name="bloquear_canal", description="Bloquea un canal")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def bloquear_canal(self, interaction: discord.Interaction, canal: discord.TextChannel, razon: str = "Sin razón"):
        await canal.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message(f"🚫 Canal {canal} bloqueado. Razón: {razon}")
        await self.log_event(interaction.guild, f"🚫 {canal} bloqueado por {interaction.user}. Razón: {razon}")

    @app_commands.command(name="desbloquear_canal", description="Desbloquea un canal")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def desbloquear_canal(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await canal.set_permissions(interaction.guild.default_role, send_messages=None)
        await interaction.response.send_message(f"✅ Canal {canal} desbloqueado.")
        await self.log_event(interaction.guild, f"✅ {canal} desbloqueado por {interaction.user}.")

    @app_commands.command(name="roles_automaticos", description="Configura rol automático para nuevos miembros")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roles_automaticos(self, interaction: discord.Interaction, rol: discord.Role):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['auto_role_id'] = rol.id
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message(f"✅ Rol automático configurado: {rol}")

    @app_commands.command(name="rol_temporal", description="Asigna un rol temporal")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rol_temporal(self, interaction: discord.Interaction, usuario: discord.Member, rol: discord.Role, tiempo: str):
        try:
            seconds = parse_time(tiempo)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return
        await usuario.add_roles(rol)
        end_time = asyncio.get_event_loop().time() + seconds
        guild_id = str(interaction.guild.id)
        user_id = str(usuario.id)
        if guild_id not in self.temp_roles:
            self.temp_roles[guild_id] = {}
        self.temp_roles[guild_id][user_id] = {'role_id': rol.id, 'end_time': end_time}
        save_json('temp_roles.json', self.temp_roles)
        await interaction.response.send_message(f"✅ {usuario} recibió {rol} por {format_time(seconds)}.")
        await self.log_event(interaction.guild, f"✅ {usuario} recibió rol temporal {rol} por {interaction.user}.")

    @app_commands.command(name="backup", description="Hace backup de la configuración del servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction):
        guild = interaction.guild
        backup_data = {
            'name': guild.name,
            'channels': [{'name': c.name, 'type': str(c.type)} for c in guild.channels],
            'roles': [{'name': r.name, 'color': r.color.value} for r in guild.roles]
        }
        save_json(f'backup_{guild.id}.json', backup_data)
        await interaction.response.send_message("✅ Backup guardado.", ephemeral=True)

    @app_commands.command(name="set_welcome_channel", description="Configura el canal de bienvenida")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, canal: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['welcome_channel_id'] = canal.id
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message(f"✅ Canal de bienvenida configurado: {canal}", ephemeral=True)

    @app_commands.command(name="set_welcome_message", description="Configura el mensaje de bienvenida")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_welcome_message(self, interaction: discord.Interaction, mensaje: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['welcome_message'] = mensaje
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message("✅ Mensaje de bienvenida configurado.", ephemeral=True)

    @app_commands.command(name="set_welcome_image", description="Configura la imagen de bienvenida")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_welcome_image(self, interaction: discord.Interaction, url: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['welcome_image'] = url
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message("✅ Imagen de bienvenida configurada.", ephemeral=True)

    @app_commands.command(name="set_goodbye_channel", description="Configura el canal de despedida")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_goodbye_channel(self, interaction: discord.Interaction, canal: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['goodbye_channel_id'] = canal.id
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message(f"✅ Canal de despedida configurado: {canal}", ephemeral=True)

    @app_commands.command(name="set_goodbye_message", description="Configura el mensaje de despedida")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_goodbye_message(self, interaction: discord.Interaction, mensaje: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['goodbye_message'] = mensaje
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message("✅ Mensaje de despedida configurado.", ephemeral=True)

    @app_commands.command(name="set_goodbye_image", description="Configura la imagen de despedida")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_goodbye_image(self, interaction: discord.Interaction, url: str):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        self.config[guild_id]['goodbye_image'] = url
        save_json('moderation_config.json', self.config)
        await interaction.response.send_message("✅ Imagen de despedida configurada.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))