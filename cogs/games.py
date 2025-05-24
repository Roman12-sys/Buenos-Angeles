import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

class RoleButton(Button):
    def __init__(self, role: discord.Role, emoji: str):
        super().__init__(style=discord.ButtonStyle.secondary, label=role.name, emoji=emoji)
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        if self.role in member.roles:
            await member.remove_roles(self.role)
            await interaction.response.send_message(f"❌ Rol '{self.role.name}' removido.", ephemeral=True)
        else:
            await member.add_roles(self.role)
            await interaction.response.send_message(f"✅ Rol '{self.role.name}' asignado.", ephemeral=True)

class SetupGameView(View):
    def __init__(self, roles_emojis):
        super().__init__(timeout=None)
        for role, emoji in roles_emojis.items():
            self.add_item(RoleButton(role, emoji))

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_game", description="Configura roles de juegos con botones")
    async def setup_game(self, interaction: discord.Interaction):
        guild = interaction.guild
        category_name = "🎮 Roles de juegos"
        channel_name = "🎮 Roles de juegos"
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name)
        channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
        if channel is None:
            channel = await guild.create_text_channel(channel_name, category=category)
        roles_emojis_names = {
            "Fortnite": "🎮",
            "Rocket League": "⚽",
            "Squad": "🪖",
            "Counter Strike 2": "🔫",
            "R.E.P.O": "🚓",
            "Minecraft": "⛏️",
            "League Of Legends": "🧠",
            "World of Warcraft": "🐉",
            "Albion Online": "🛡️"
        }
        roles_emojis = {}
        for role_name, emoji in roles_emojis_names.items():
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                role = await guild.create_role(name=role_name, mentionable=True)
            roles_emojis[role] = emoji
        embed = discord.Embed(
            title="🎮 Roles de juegos",
            description="Selecciona tus juegos favoritos para obtener los roles correspondientes",
            color=discord.Color.blue()
        )
        view = SetupGameView(roles_emojis)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Configuración completada en {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Games(bot))
