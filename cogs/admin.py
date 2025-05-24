import discord
from discord import app_commands
from discord.ext import commands
from utils.common import crear_categoria, crear_rol
import re
import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_rol_map = {}
        self.verificacion_roles_msg_id = None
        self.verificacion = None

    @app_commands.command(name="estadisticas", description="Muestra estadísticas del servidor")
    async def estadisticas(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
            return
        voice_channels = len(guild.voice_channels)
        text_channels = len(guild.text_channels)
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
        offline_members = sum(1 for m in guild.members if m.status == discord.Status.offline and not m.bot)
        embed = discord.Embed(title=f"Estadísticas de {guild.name}", color=discord.Color.green())
        embed.add_field(name="Canales de voz", value=str(voice_channels), inline=True)
        embed.add_field(name="Canales de texto", value=str(text_channels), inline=True)
        embed.add_field(name="Miembros totales", value=str(total_members), inline=True)
        embed.add_field(name="Miembros en línea", value=str(online_members), inline=True)
        embed.add_field(name="Miembros desconectados", value=str(offline_members), inline=True)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        embed.set_footer(text=f"Fecha: {current_date}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='setup', description='Configura el servidor automáticamente')
    async def setup_servidor(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.send_message("🔧 Configurando el servidor...")
        for canal in guild.channels:
            try:
                await canal.delete()
            except Exception:
                pass
        rol_verificado = await crear_rol(guild, '✅ Verificado')
        reglas_cat = await crear_categoria(guild, '📌 Reglas')
        try:
            canal_reglas = await guild.create_text_channel('📜┃reglas', category=reglas_cat)
        except Exception:
            canal_reglas = None
        if canal_reglas:
            try:
                mensaje_reglas = await canal_reglas.send(
                    "**📜 Reglas del servidor**\n\n"
                    "1. Respeto mutuo.\n"
                    "2. No spam.\n"
                    "3. No contenido ofensivo.\n\n"
                    "✅ **Reacciona con ✅ para verificarte y acceder al servidor.**"
                )
                await mensaje_reglas.add_reaction("✅")
            except Exception:
                mensaje_reglas = None
        else:
            mensaje_reglas = None
        if mensaje_reglas:
            self.verificacion = {
                "mensaje_id": mensaje_reglas.id,
                "canal_id": canal_reglas.id,
                "rol_id": rol_verificado.id
            }
        else:
            self.verificacion = None
        chat_cat = await crear_categoria(guild, '💬 Chat General')
        canales_texto = [
            '💬┃general',
            '📸┃clips-y-destacados',
            '🎵┃musica',
            '💬┃chats-lol',
            '😂┃meme',
            '🌸┃casa-rosada',
        ]
        for nombre in canales_texto:
            try:
                await guild.create_text_channel(nombre, category=chat_cat)
            except Exception:
                pass
        voz_cat = await crear_categoria(guild, '🎮 Canales de Voz')
        canales_voz = [
            '🎙️ SoloQ/duo',
            '🚀 Rocket League',
            '👥 SQUAD',
            '🔥 La grieta del tilteo',
            '🎧 Squad'
        ]
        for nombre in canales_voz:
            try:
                await guild.create_voice_channel(nombre, category=voz_cat)
            except Exception:
                pass
        await interaction.followup.send("✅ ¡Servidor configurado con éxito!")

    @app_commands.command(name='reset', description='Elimina todos los canales del servidor')
    async def reset_servidor(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.send_message("🧹 Eliminando todos los canales...")
        for canal in guild.channels:
            try:
                await canal.delete()
            except Exception:
                pass
        await interaction.followup.send("🗑️ Canales eliminados.")

    @app_commands.command(name='crear_roles', description='Crear roles de juegos con emojis y configurar reacciones para asignarlos')
    async def crear_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        roles_emojis = {
            "Fortnite": "🎮",
            "Rocket League": "⚽",
            "Squad": "🪖",
            "Counter Strike 2": "🔫",
            "R.E.P.O": "🚓",
            "Minecraft": "⛏️"
        }
        mensajes_confirmacion = []
        for nombre in roles_emojis.keys():
            rol_existente = discord.utils.get(guild.roles, name=nombre)
            if rol_existente:
                try:
                    await rol_existente.delete()
                except Exception:
                    pass
        roles_creados = {}
        for nombre, emoji in roles_emojis.items():
            try:
                rol_creado = await guild.create_role(name=nombre, mentionable=True)
                roles_creados[emoji] = rol_creado.id
                mensajes_confirmacion.append(f"✅ Rol '{nombre}' creado correctamente.")
            except Exception:
                mensajes_confirmacion.append(f"⚠️ No se pudo crear el rol '{nombre}'.")
        mensaje = "🎮 **Roles disponibles:**\n"
        for nombre, emoji in roles_emojis.items():
            mensaje += f"{emoji} - {nombre}\n"
        msg = await interaction.channel.send(mensaje)
        for emoji in roles_emojis.values():
            try:
                await msg.add_reaction(emoji)
            except Exception:
                pass
        self.verificacion_roles_msg_id = msg.id
        self.emoji_rol_map = roles_creados
        # Mensaje de confirmación sólo para el usuario
        await interaction.followup.send("\n".join(mensajes_confirmacion) + "\n✅ Roles creados y mensaje de reacciones configurado.", ephemeral=True)

    @app_commands.command(name='borrar_roles', description='Borrar roles relacionados a videojuegos separados por comas')
    async def borrar_roles(self, interaction: discord.Interaction, roles: str):
        guild = interaction.guild
        nombres_roles = [rol.strip() for rol in roles.split(',') if rol.strip()]
        roles_borrados = []
        errores = []
        for nombre in nombres_roles:
            rol_existente = discord.utils.get(guild.roles, name=nombre)
            if not rol_existente:
                errores.append(f"El rol '{nombre}' no existe.")
                continue
            try:
                await rol_existente.delete()
                roles_borrados.append(nombre)
            except Exception as e:
                errores.append(f"Error al borrar el rol '{nombre}': {e}")
        mensaje = ""
        if roles_borrados:
            mensaje += f"✅ Roles borrados: {', '.join(roles_borrados)}\n"
        if errores:
            mensaje += f"⚠️ Errores:\n" + "\n".join(errores)
        await interaction.response.send_message(mensaje or "No se borraron roles.")

    @app_commands.command(name='purga', description='Eliminar una cantidad de mensajes en el canal actual')
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    async def purga(self, interaction: discord.Interaction, cantidad: int, usuario: discord.Member = None):
        if cantidad < 1:
            await interaction.response.send_message("La cantidad debe ser al menos 1.", ephemeral=True)
            return
        if cantidad > 100:
            await interaction.response.send_message("La cantidad máxima a eliminar es 100.", ephemeral=True)
            return
        canal = interaction.channel
        await interaction.response.defer(ephemeral=True)
        try:
            if usuario:
                def filtro(m):
                    return m.author.id == usuario.id
                deleted = await canal.purge(limit=cantidad, check=filtro)
            else:
                deleted = await canal.purge(limit=cantidad)
            await interaction.followup.send(f"🧹 Se eliminaron {len(deleted)} mensajes.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("No tengo permisos para eliminar mensajes en este canal.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
