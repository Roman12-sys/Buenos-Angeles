import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import discord
from setup_game_command import setup_game
from logs_command import setup_logs
import help_command
import random

# Cargar variables de entorno desde el archivo .env en el root
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("El token del bot no está configurado en la variable de entorno DISCORD_BOT_TOKEN")

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

import asyncio

@client.event
async def on_ready():
    # Evento que se conecta y está listo
    # Sincronizar comandos globales
    await help_command.setup(client)
    await tree.sync()
    # Setup logs cog and event listeners
    await setup_logs(client)
    print(f'✅ Bot conectado como {client.user}')
    # Start background task for status updates
    client.loop.create_task(status_task())

async def status_task():
    await client.wait_until_ready()
    statuses = [
        "Usa /help para comandos",
        "Contando miembros del servidor...",
        "Disfruta tu estadía"
    ]
    i = 0
    while not client.is_closed():
        status = statuses[i % len(statuses)]
        if status == "Contando miembros del servidor...":
            total_members = 0
            for guild in client.guilds:
                total_members += guild.member_count
            activity = discord.Game(f"Miembros: {total_members}")
        else:
            activity = discord.Game(status)
        await client.change_presence(activity=activity)
        i += 1
        await asyncio.sleep(15)  # wait 60 seconds before changing status

# Register the /setup_game command by adding it to the command tree
tree.add_command(setup_game)

@tree.command(name="estadisticas", description="Muestra estadísticas del servidor")
async def estadisticas(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
        return

    voice_channels = len(guild.voice_channels)
    text_channels = len(guild.text_channels)
    total_members = guild.member_count
    online_members = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    offline_members = sum(1 for m in guild.members if m.status == discord.Status.offline and not m.bot)
    region = str(guild.region) if hasattr(guild, "region") else "Desconocida"

    embed = discord.Embed(title=f"Estadísticas de {guild.name}", color=discord.Color.green())
    embed.add_field(name="Canales de voz", value=str(voice_channels), inline=True)
    embed.add_field(name="Canales de texto", value=str(text_channels), inline=True)
    embed.add_field(name="Miembros totales", value=str(total_members), inline=True)
    embed.add_field(name="Miembros en línea", value=str(online_members), inline=True)
    embed.add_field(name="Miembros desconectados", value=str(offline_members), inline=True)
    import datetime
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    embed.set_footer(text=f"Fecha: {current_date}")

    await interaction.response.send_message(embed=embed)

# Función para crear categoría si no existe
async def crear_categoria(guild, nombre):
    for category in guild.categories:
        if category.name == nombre:
            return category
    return await guild.create_category(nombre)

# Función para crear rol si no existe
async def crear_rol(guild, nombre):
    for rol in guild.roles:
        if rol.name == nombre:
            return rol
    return await guild.create_role(name=nombre, mentionable=True)

# SETUP GENERAL
@tree.command(name='setup', description='Configura el servidor automáticamente')
async def setup_servidor(interaction: discord.Interaction):
    print(f"Comando 'setup' ejecutado por usuario {interaction.user} en guild {interaction.guild.name}")
    guild = interaction.guild
    await interaction.response.send_message("🔧 Configurando el servidor...")

    for canal in guild.channels:
        try:
            await canal.delete()
        except Exception as e:
            print(f"Error al eliminar canal {canal.name}: {e}")

    rol_verificado = await crear_rol(guild, '✅ Verificado')

    reglas_cat = await crear_categoria(guild, '📌 Reglas')
    try:
        canal_reglas = await guild.create_text_channel('📜┃reglas', category=reglas_cat)
    except Exception as e:
        print(f"Error al crear canal de reglas: {e}")
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
        except Exception as e:
            print(f"Error al enviar mensaje de reglas o añadir reacción: {e}")
            mensaje_reglas = None
    else:
        mensaje_reglas = None

    if mensaje_reglas:
        client.verificacion = {
            "mensaje_id": mensaje_reglas.id,
            "canal_id": canal_reglas.id,
            "rol_id": rol_verificado.id
        }
    else:
        client.verificacion = None

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
        except Exception as e:
            print(f"Error al crear canal de texto {nombre}: {e}")

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
        except Exception as e:
            print(f"Error al crear canal de voz {nombre}: {e}")

    await interaction.followup.send("✅ ¡Servidor configurado con éxito!")

# VERIFICACIÓN AUTOMÁTICA
@client.event
async def on_raw_reaction_add(payload):
    if client.verificacion_roles_msg_id and payload.message_id == client.verificacion_roles_msg_id:
        emoji = str(payload.emoji)
        if emoji in client.emoji_rol_map:
            guild = client.get_guild(payload.guild_id)
            if guild is None:
                return
            miembro = guild.get_member(payload.user_id)
            if miembro is None or miembro.bot:
                return
            rol_id = client.emoji_rol_map[emoji]
            rol = guild.get_role(rol_id)
            if rol is None:
                return
            if rol in miembro.roles:
                return
            try:
                await miembro.add_roles(rol)
                canal = guild.get_channel(payload.channel_id)
                if canal:
                    await canal.send(f"✅ {miembro.mention} recibió el rol {rol.name} por reacción.")
            except Exception as e:
                print(f"Error al asignar rol por reacción: {e}")
            return

    if not hasattr(client, "verificacion") or not client.verificacion:
        return

    if payload.message_id == client.verificacion["mensaje_id"] and str(payload.emoji) == "✅":
        if payload.member is None or payload.member.bot:
            return
        guild = client.get_guild(payload.guild_id)
        if guild is None:
            return
        miembro = guild.get_member(payload.user_id)
        if miembro is None or miembro.bot:
            return
        rol = guild.get_role(client.verificacion["rol_id"])
        if rol is None:
            return
        if rol in miembro.roles:
            return
        try:
            await miembro.add_roles(rol)
            canal = guild.get_channel(client.verificacion["canal_id"])
            if canal:
                await canal.send(f"✅ {miembro.mention} fue verificado correctamente.")
        except Exception as e:
            print(f"Error al asignar rol o enviar mensaje de verificación: {e}")

# RESET: BORRA LOS CANALES
@tree.command(name='reset', description='Elimina todos los canales del servidor')
async def reset_servidor(interaction: discord.Interaction):
    print(f"Comando 'reset' ejecutado por usuario {interaction.user} en guild {interaction.guild.name}")
    guild = interaction.guild
    await interaction.response.send_message("🧹 Eliminando todos los canales...")
    for canal in guild.channels:
        try:
            await canal.delete()
        except Exception as e:
            print(f"Error al eliminar canal {canal.name}: {e}")
    await interaction.followup.send("🗑️ Canales eliminados.")

import re

client.emoji_rol_map = {}
client.verificacion_roles_msg_id = None

def extraer_emoji(texto):
    emoji_pattern = re.compile(
        r'(<a?:\w+:\d+>)|([\U0001F1E0-\U0001F6FF])', flags=re.UNICODE)
    match = emoji_pattern.search(texto)
    if match:
        return match.group(0)
    return None

@tree.command(name='crear_roles', description='Crear roles de juegos con emojis y configurar reacciones para asignarlos')
async def crear_roles(interaction: discord.Interaction):
    print(f"Comando 'crear_roles' realizado por usuario {interaction.user}")
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

    for nombre in roles_emojis.keys():
        rol_existente = discord.utils.get(guild.roles, name=nombre)
        if rol_existente:
            try:
                await rol_existente.delete()
                print(f"Rol eliminado: {nombre}")
            except Exception as e:
                print(f"Error al eliminar rol {nombre}: {e}")

    roles_creados = {}
    for nombre, emoji in roles_emojis.items():
        try:
            rol_creado = await guild.create_role(name=nombre, mentionable=True)
            roles_creados[emoji] = rol_creado.id
            print(f"Rol creado: {nombre}")
        except Exception as e:
            print(f"Error al crear rol {nombre}: {e}")

    mensaje = "🎮 **Roles disponibles:**\n"
    for nombre, emoji in roles_emojis.items():
        mensaje += f"{emoji} - {nombre}\n"

    msg = await interaction.channel.send(mensaje)

    for emoji in roles_emojis.values():
        try:
            await msg.add_reaction(emoji)
        except Exception as e:
            print(f"Error al añadir reacción {emoji}: {e}")

    client.verificacion_roles_msg_id = msg.id
    client.emoji_rol_map = roles_creados

    await interaction.followup.send("✅ Roles creados y mensaje de reacciones configurado.", ephemeral=True)

@tree.command(name='borrar_roles', description='Borrar roles relacionados a videojuegos separados por comas')
async def borrar_roles(interaction: discord.Interaction, roles: str):
    print(f"Comando 'borrar_roles' ejecutado por usuario {interaction.user} con roles: {roles}")
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

@tree.command(name='purga', description='Eliminar una cantidad de mensajes en el canal actual')
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def purga(interaction: discord.Interaction, cantidad: int, usuario: discord.Member = None):
    print(f"Comando 'purga' ejecutado por usuario {interaction.user} con cantidad: {cantidad} y usuario: {usuario}")
    if cantidad < 1:
        try:
            await interaction.response.send_message("La cantidad debe ser al menos 1.", ephemeral=True)
        except discord.errors.NotFound:
            pass
        return
    if cantidad > 100:
        try:
            await interaction.response.send_message("La cantidad máxima a eliminar es 100.", ephemeral=True)
        except discord.errors.NotFound:
            pass
        return

    canal = interaction.channel
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.errors.NotFound:
        pass

    try:
        if usuario:
            def filtro(m):
                return m.author.id == usuario.id
            deleted = await canal.purge(limit=cantidad, check=filtro)
        else:
            deleted = await canal.purge(limit=cantidad)
        await interaction.followup.send(f"🧹 Se eliminaron {len(deleted)} mensajes.", ephemeral=True)
    except discord.Forbidden:
        try:
            await interaction.followup.send("No tengo permisos para eliminar mensajes en este canal.", ephemeral=True)
        except discord.errors.NotFound:
            pass
    except Exception as e:
        try:
            await interaction.followup.send(f"Ocurrió un error: {e}", ephemeral=True)
        except discord.errors.NotFound:
            pass

@purga.error
async def purga_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        try:
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
        except discord.errors.NotFound:
            pass
    else:
        try:
            await interaction.response.send_message(f"Ocurrió un error: {error}", ephemeral=True)
        except discord.errors.NotFound:
            pass

@client.event
async def on_raw_reaction_remove(payload):
    if client.verificacion_roles_msg_id and payload.message_id == client.verificacion_roles_msg_id:
        emoji = str(payload.emoji)
        if emoji in client.emoji_rol_map:
            guild = client.get_guild(payload.guild_id)
            if guild is None:
                return
            miembro = guild.get_member(payload.user_id)
            if miembro is None or miembro.bot:
                return
            rol_id = client.emoji_rol_map[emoji]
            rol = guild.get_role(rol_id)
            if rol is None:
                return
            if rol not in miembro.roles:
                return
            try:
                await miembro.remove_roles(rol)
                canal = guild.get_channel(payload.channel_id)
                if canal:
                    await canal.send(f"❌ {miembro.mention} perdió el rol {rol.name} al quitar la reacción.")
            except Exception as e:
                print(f"Error al remover rol por quitar reacción: {e}")

@tree.command(name="dados", description="Tira un número al azar del 1 al 100")
async def dados(interaction: discord.Interaction):
    numero = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 Has sacado un {numero} en el dado.")
