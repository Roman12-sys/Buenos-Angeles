import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import requests
from googletrans import Translator
from utils.common import load_json, save_json, parse_time, format_time
import yt_dlp
import os

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        self.reminders = load_json('reminders.json')
        self.profiles = load_json('profiles.json')
        self.bot.loop.create_task(self.check_reminders())

    async def check_reminders(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            current_time = asyncio.get_event_loop().time()
            to_remove = []
            for user_id, reminders in self.reminders.items():
                for reminder in reminders[:]:
                    if current_time >= reminder['time']:
                        user = self.bot.get_user(int(user_id))
                        if user:
                            try:
                                await user.send(f"🔔 Recordatorio: {reminder['message']}")
                            except:
                                pass  # DM failed
                        to_remove.append((user_id, reminder))
            for user_id, reminder in to_remove:
                self.reminders[user_id].remove(reminder)
                if not self.reminders[user_id]:
                    del self.reminders[user_id]
            save_json('reminders.json', self.reminders)
            await asyncio.sleep(60)  # Check every minute

    @app_commands.command(name="recordatorio", description="Crea un recordatorio (ej: 10m, 2h, 3d)")
    async def recordatorio(self, interaction: discord.Interaction, tiempo: str, mensaje: str):
        try:
            seconds = parse_time(tiempo)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return
        reminder_time = asyncio.get_event_loop().time() + seconds
        user_id = str(interaction.user.id)
        if user_id not in self.reminders:
            self.reminders[user_id] = []
        self.reminders[user_id].append({'time': reminder_time, 'message': mensaje})
        save_json('reminders.json', self.reminders)
        await interaction.response.send_message(f"✅ Recordatorio creado para {format_time(seconds)}.", ephemeral=True)

    @app_commands.command(name="encuesta", description="Crea una encuesta con opciones")
    async def encuesta(self, interaction: discord.Interaction, pregunta: str, opcion1: str, opcion2: str, opcion3: str = None, opcion4: str = None):
        options = [opcion1, opcion2]
        if opcion3:
            options.append(opcion3)
        if opcion4:
            options.append(opcion4)
        embed = discord.Embed(title="📊 Encuesta", description=pregunta, color=discord.Color.blue())
        for i, opt in enumerate(options, 1):
            embed.add_field(name=f"Opción {i}", value=opt, inline=False)
        msg = await interaction.channel.send(embed=embed)
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])
        await interaction.response.send_message("✅ Encuesta creada.", ephemeral=True)

    @app_commands.command(name="traducir", description="Traduce texto a un idioma")
    async def traducir(self, interaction: discord.Interaction, idioma_destino: str, texto: str):
        try:
            translated = self.translator.translate(texto, dest=idioma_destino)
            embed = discord.Embed(title="🌐 Traducción", color=discord.Color.green())
            embed.add_field(name="Original", value=texto, inline=False)
            embed.add_field(name=f"Traducido a {idioma_destino}", value=translated.text, inline=False)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error al traducir: {e}", ephemeral=True)

    @app_commands.command(name="clima", description="Obtiene el clima de una ciudad")
    async def clima(self, interaction: discord.Interaction, ciudad: str):
        api_key = os.getenv('OPENWEATHER_API_KEY')  # Asume que está en .env
        if not api_key:
            await interaction.response.send_message("API key no configurada.", ephemeral=True)
            return
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            embed = discord.Embed(title=f"🌤️ Clima en {ciudad}", color=discord.Color.blue())
            embed.add_field(name="Temperatura", value=f"{temp}°C", inline=True)
            embed.add_field(name="Descripción", value=desc.capitalize(), inline=True)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Ciudad no encontrada.", ephemeral=True)

    @app_commands.command(name="meme", description="Envía un meme aleatorio")
    async def meme(self, interaction: discord.Interaction):
        response = requests.get("https://meme-api.herokuapp.com/gimme")
        if response.status_code == 200:
            data = response.json()
            embed = discord.Embed(title=data['title'], color=discord.Color.purple())
            embed.set_image(url=data['url'])
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No se pudo obtener un meme.", ephemeral=True)

    @app_commands.command(name="8ball", description="Pregunta a la bola 8 mágica")
    async def eightball(self, interaction: discord.Interaction, pregunta: str):
        responses = [
            "Sí", "No", "Tal vez", "Definitivamente", "No cuentes con ello",
            "Pregunta de nuevo", "Sin duda", "Muy dudoso"
        ]
        answer = random.choice(responses)
        embed = discord.Embed(title="🎱 Bola 8 Mágica", color=discord.Color.orange())
        embed.add_field(name="Pregunta", value=pregunta, inline=False)
        embed.add_field(name="Respuesta", value=answer, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="perfil", description="Muestra o crea tu perfil")
    async def perfil(self, interaction: discord.Interaction, edad: int = None, juegos: str = None):
        user_id = str(interaction.user.id)
        if user_id not in self.profiles:
            self.profiles[user_id] = {}
        if edad:
            self.profiles[user_id]['edad'] = edad
        if juegos:
            self.profiles[user_id]['juegos'] = juegos
        save_json('profiles.json', self.profiles)
        embed = discord.Embed(title=f"Perfil de {interaction.user.name}", color=discord.Color.teal())
        embed.add_field(name="Edad", value=self.profiles[user_id].get('edad', 'No especificada'), inline=True)
        embed.add_field(name="Juegos", value=self.profiles[user_id].get('juegos', 'No especificados'), inline=True)
        await interaction.response.send_message(embed=embed)

    # Música básica
    @app_commands.command(name="play", description="Reproduce música de YouTube")
    async def play(self, interaction: discord.Interaction, url: str):
        if not interaction.user.voice:
            await interaction.response.send_message("Debes estar en un canal de voz.", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        vc = await channel.connect()
        ydl_opts = {'format': 'bestaudio', 'outtmpl': 'temp.%(ext)s'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
        vc.play(discord.FFmpegPCMAudio(url2))
        await interaction.response.send_message(f"🎵 Reproduciendo: {info['title']}")

async def setup(bot):
    await bot.add_cog(Utility(bot))