import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import asyncio
import json
import os
from typing import Dict

DATA_FILE = "levels_data.json"
COOLDOWN_SECONDS = 60

def xp_for_next_level(level: int) -> int:
    # Example formula: 100 * level^2
    return 100 * (level ** 2)

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data: Dict[int, Dict[str, int]] = {}
        self.cooldowns: Dict[int, float] = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    self.user_data = json.load(f)
                    # Convert keys back to int
                    self.user_data = {int(k): v for k, v in self.user_data.items()}
            except Exception as e:
                print(f"Error loading levels data: {e}")

    def save_data(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.user_data, f)
        except Exception as e:
            print(f"Error saving levels data: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = message.author.id
        now = asyncio.get_event_loop().time()

        last_time = self.cooldowns.get(user_id, 0)
        if now - last_time < COOLDOWN_SECONDS:
            return

        self.cooldowns[user_id] = now

        xp_gain = random.randint(5, 15)
        user_stats = self.user_data.get(user_id, {"xp": 0, "level": 1})
        user_stats["xp"] += xp_gain

        # Check level up
        next_level_xp = xp_for_next_level(user_stats["level"])
        leveled_up = False
        while user_stats["xp"] >= next_level_xp:
            user_stats["level"] += 1
            leveled_up = True
            next_level_xp = xp_for_next_level(user_stats["level"])

        self.user_data[user_id] = user_stats
        self.save_data()

        if leveled_up:
            try:
                await message.channel.send(
                    f"🎉 ¡Felicidades {message.author.mention}! Subiste al nivel {user_stats['level']}."
                )
            except Exception as e:
                print(f"Error sending level up message: {e}")

    @app_commands.command(name="nivel", description="Muestra tu nivel y XP actual")
    async def nivel(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_stats = self.user_data.get(user_id, {"xp": 0, "level": 1})
        current_xp = user_stats["xp"]
        level = user_stats["level"]
        next_level_xp = xp_for_next_level(level)
        xp_to_next = next_level_xp - current_xp

        embed = discord.Embed(title=f"Nivel de {interaction.user.display_name}", color=discord.Color.green())
        embed.add_field(name="Nivel", value=str(level), inline=True)
        embed.add_field(name="XP actual", value=str(current_xp), inline=True)
        embed.add_field(name="XP para el próximo nivel", value=str(xp_to_next), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ranking", description="Muestra el top 10 de usuarios con más XP")
    async def ranking(self, interaction: discord.Interaction):
        sorted_users = sorted(self.user_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
        top_10 = sorted_users[:10]

        lines = []
        for rank, (user_id, stats) in enumerate(top_10, start=1):
            user = self.bot.get_user(user_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(user_id)
                except Exception:
                    user = None
            if user is None:
                user_display = f"Usuario ID {user_id}"
            else:
                user_display = user.mention
            lines.append(f"{rank}. {user_display} - Nivel: {stats['level']} - XP: {stats['xp']}")

        message_content = "**Top 10 de usuarios por nivel y XP**\n" + "\n".join(lines)

        await interaction.response.send_message(message_content, ephemeral=False, allowed_mentions=discord.AllowedMentions(users=True))

async def setup(bot):
    await bot.add_cog(Levels(bot))
