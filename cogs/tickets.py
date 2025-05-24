import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import json
import os

TICKETS_FILE = "tickets_config.json"
MOD_ROLE_NAME = "Moderador 👮‍♂️"

class TicketOpenButton(Button):
    def __init__(self):
        super().__init__(label="Abrir Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")

    async def callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("Tickets")
        if cog is None:
            await interaction.response.send_message("El sistema de tickets no está disponible.", ephemeral=True)
            return
        await cog.create_ticket(interaction)

class TicketCloseButton(Button):
    def __init__(self):
        super().__init__(label="Cerrar", style=discord.ButtonStyle.red, custom_id="close_ticket")

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        if channel is None:
            await interaction.response.send_message("No se pudo identificar el canal.", ephemeral=True)
            return
        await channel.send("🔒 El ticket será cerrado y archivado.")
        try:
            await channel.edit(name=f"cerrado-{channel.name}", sync_permissions=True)
            await channel.set_permissions(interaction.user, send_messages=False, read_messages=False)
            await channel.set_permissions(interaction.guild.default_role, read_messages=False)
            archive_category = discord.utils.get(interaction.guild.categories, name="Tickets Archivados")
            if archive_category:
                await channel.edit(category=archive_category)
            else:
                await channel.delete()
        except Exception as e:
            await interaction.response.send_message(f"Error al cerrar el ticket: {e}", ephemeral=True)
            return
        await interaction.response.send_message("Ticket cerrado correctamente.", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_counter = 0
        self.load_tickets()

    def load_tickets(self):
        if os.path.exists(TICKETS_FILE):
            try:
                with open(TICKETS_FILE, "r") as f:
                    data = json.load(f)
                    self.ticket_counter = data.get("ticket_counter", 0)
            except Exception as e:
                print(f"Error cargando tickets: {e}")

    def save_tickets(self):
        try:
            with open(TICKETS_FILE, "w") as f:
                json.dump({"ticket_counter": self.ticket_counter}, f)
        except Exception as e:
            print(f"Error guardando tickets: {e}")

    @app_commands.command(name="tickets", description="Configura la categoría y canal general de tickets con botón para abrir ticket")
    @app_commands.checks.has_permissions(administrator=True)
    async def tickets(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
            return

        # Crear rol Moderador 👮‍♂️ si no existe
        mod_role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        if mod_role is None:
            permissions = discord.Permissions.all()
            permissions.administrator = False
            try:
                mod_role = await guild.create_role(name=MOD_ROLE_NAME, permissions=permissions, reason="Rol de moderador creado automáticamente para tickets")
            except Exception as e:
                await interaction.response.send_message(f"Error al crear el rol Moderador: {e}", ephemeral=True)
                return

        # Crear categoría Tickets si no existe
        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets", reason="Categoría para tickets de soporte")

        # Crear canal general de tickets si no existe
        general_channel = discord.utils.get(guild.text_channels, name="📩-tickets", category=category)
        if general_channel is None:
            general_channel = await guild.create_text_channel(
                "📩-tickets",
                category=category,
                reason="Canal general para instrucciones de tickets"
            )

        # Enviar mensaje con botón para abrir ticket
        view = View()
        view.add_item(TicketOpenButton())

        embed = discord.Embed(
            title="🎫 Bienvenido al sistema de tickets",
            description=(
                f"Presiona el botón para abrir un nuevo ticket de soporte.\n"
                f"Solo los moderadores con el rol {MOD_ROLE_NAME} podrán ver los tickets.\n"
                "Cuando termines, usa el botón 'Cerrar' dentro del canal del ticket para cerrarlo."
            ),
            color=discord.Color.blue()
        )
        await general_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"Categoría, canal general de tickets y rol {MOD_ROLE_NAME} configurados con botón para abrir tickets.",
            ephemeral=True
        )

    async def create_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo puede usarse en un servidor.", ephemeral=True)
            return

        mod_role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        if mod_role is None:
            await interaction.response.send_message(f"No se encontró el rol {MOD_ROLE_NAME}. Usa /tickets para configurarlo.", ephemeral=True)
            return

        user = interaction.user
        self.ticket_counter += 1
        self.save_tickets()

        channel_name = f"{user.name}-{self.ticket_counter}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        category = discord.utils.get(guild.categories, name="Tickets")
        if category is None:
            category = await guild.create_category("Tickets")

        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category, reason="Nuevo ticket de soporte")

        view = View()
        view.add_item(TicketCloseButton())

        embed = discord.Embed(
            title="🎟️ ¡Hola y bienvenid@ a tu ticket de soporte!",
            description=(
                "Gracias por comunicarte con nosotros. Un miembro del equipo te atenderá en breve.\n\n"
                "🔹 Mientras tanto, por favor detallá tu consulta o problema para poder ayudarte lo antes posible.\n"
                "🔹 Si el ticket fue creado por error, podés cerrarlo con el botón correspondiente\n\n"
                "🛠️ Estamos para ayudarte. ¡Gracias por tu paciencia!"
            ),
            color=discord.Color.blue()
        )

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Ticket creado: {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
