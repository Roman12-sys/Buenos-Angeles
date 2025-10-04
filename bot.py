import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
import sys
from utils.common import load_json

# Cargar variables de entorno desde el archivo .env en el root
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("El token del bot no está configurado en la variable de entorno DISCORD_BOT_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

config = load_json('moderation_config.json')

COGS = [
    "cogs.help",
    "cogs.logs",
    "cogs.games",
    "cogs.admin",
    "cogs.verification",
    "cogs.dados",
    "cogs.info",
    "cogs.tickets",
    "cogs.levels",
    "cogs.utility",
    "cogs.moderation"
]

# Animación de carga amigable
async def loading_animation(text="Iniciando el bot", symbol="Bot", delay=0.5, duration=5):
    end_time = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end_time:
        for dots in range(4):
            sys.stdout.write(f"\r{symbol} {text}{'.' * dots}   ")
            sys.stdout.flush()
            await asyncio.sleep(delay)
    print("\nBot ¡Listo! El bot está en línea y preparado para ayudarte.\n")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"OK Cog cargado: {cog}")
        except Exception as e:
            print(f"ERROR Error al cargar {cog}: {e}")

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    await bot.tree.sync()
    bot.loop.create_task(status_task())

@bot.event
async def on_member_join(member):
    guild_config = config.get(str(member.guild.id), {})
    welcome_channel_id = guild_config.get('welcome_channel_id')
    if welcome_channel_id:
        channel = bot.get_channel(welcome_channel_id)
        if channel:
            message = guild_config.get('welcome_message', 'Bienvenido {user}!')
            message = message.replace('{user}', member.mention)
            embed = discord.Embed(description=message, color=discord.Color.green())
            image_url = guild_config.get('welcome_image')
            if image_url:
                embed.set_image(url=image_url)
            await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    guild_config = config.get(str(member.guild.id), {})
    goodbye_channel_id = guild_config.get('goodbye_channel_id')
    if goodbye_channel_id:
        channel = bot.get_channel(goodbye_channel_id)
        if channel:
            message = guild_config.get('goodbye_message', 'Adiós {user}!')
            message = message.replace('{user}', member.name)
            embed = discord.Embed(description=message, color=discord.Color.red())
            image_url = guild_config.get('goodbye_image')
            if image_url:
                embed.set_image(url=image_url)
            await channel.send(embed=embed)

async def status_task():
    await bot.wait_until_ready()
    statuses = [
        "Usa /help para comandos",
        "Contando miembros del servidor...",
        "Disfruta tu estadía"
    ]
    i = 0
    while not bot.is_closed():
        status = statuses[i % len(statuses)]
        if status == "Contando miembros del servidor...":
            total_members = 0
            for guild in bot.guilds:
                total_members += guild.member_count
            activity = discord.Game(f"Miembros: {total_members}")
        else:
            activity = discord.Game(status)
        await bot.change_presence(activity=activity)
        i += 1
        await asyncio.sleep(15)

async def main():
    await loading_animation()
    await load_cogs()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
