import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CONFIG_FILE = "verification_config.json"

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificacion = None
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.verificacion = json.load(f)
                self.bot.verificacion = self.verificacion
            except Exception as e:
                print(f"Error loading verification config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.verificacion, f)
        except Exception as e:
            print(f"Error saving verification config: {e}")

    @app_commands.command(name="reglas", description="Configura el mensaje de reglas y el rol verificado")
    @app_commands.checks.has_permissions(administrator=True)
    async def reglas(self, interaction: discord.Interaction):
        """Setup the Reglas message, verificado role, and reaction for verification."""
        guild = interaction.guild

        # Delete existing "verificado" or "✅ Verificado" role if exists
        existing_role = discord.utils.get(guild.roles, name="verificado")
        if existing_role:
            try:
                await existing_role.delete(reason="Recreating verificado role for verification setup")
            except Exception as e:
                await interaction.response.send_message(f"Error al eliminar el rol existente: {e}", ephemeral=True)
                return
        existing_role_emoji = discord.utils.get(guild.roles, name="✅ Verificado")
        if existing_role_emoji:
            try:
                await existing_role_emoji.delete(reason="Recreating verificado role for verification setup")
            except Exception as e:
                await interaction.response.send_message(f"Error al eliminar el rol existente: {e}", ephemeral=True)
                return

        # Create new "✅ Verificado" role
        try:
            verificado_role = await guild.create_role(name="✅ Verificado", reason="Rol para usuarios verificados")
        except Exception as e:
            await interaction.response.send_message(f"Error al crear el rol verificado: {e}", ephemeral=True)
            return

        # Create or get "no verificado" role
        no_verificado_role = discord.utils.get(guild.roles, name="no verificado")
        if no_verificado_role is None:
            try:
                no_verificado_role = await guild.create_role(name="no verificado", reason="Rol para usuarios no verificados")
            except Exception as e:
                await interaction.response.send_message(f"Error al crear el rol no verificado: {e}", ephemeral=True)
                return

        # Deny view_channel permission for "no verificado" role in all channels
        for channel in guild.channels:
            try:
                overwrite = channel.overwrites_for(no_verificado_role)
                if overwrite.view_channel is not False:
                    overwrite.view_channel = False
                    await channel.set_permissions(no_verificado_role, overwrite=overwrite)
            except Exception as e:
                print(f"Error setting permissions for channel {channel.name}: {e}")

        # Find or create "📜 Reglas" category
        reglas_category = discord.utils.get(guild.categories, name="📜 Reglas")
        if reglas_category is None:
            try:
                reglas_category = await guild.create_category("📜 Reglas", reason="Categoría para reglas y verificación")
            except Exception as e:
                await interaction.response.send_message(f"Error al crear la categoría Reglas: {e}", ephemeral=True)
                return

        # Find or create "📄 reglas" text channel inside the "📜 Reglas" category
        reglas_channel = discord.utils.get(guild.text_channels, name="📄 reglas")
        if reglas_channel is None or reglas_channel.category != reglas_category:
            try:
                reglas_channel = await guild.create_text_channel("📄 reglas", category=reglas_category, reason="Canal para reglas y verificación")
            except Exception as e:
                await interaction.response.send_message(f"Error al crear el canal reglas: {e}", ephemeral=True)
                return

        # Prepare rules message with at least 10 rules
        rules_text = (
            "**Reglas del servidor:**\n"
            "1. Respeta a todos los miembros.\n"
            "2. No spam ni flood en los canales.\n"
            "3. No lenguaje ofensivo ni discriminatorio.\n"
            "4. Usa los canales adecuados para cada tema.\n"
            "5. No compartir contenido ilegal o inapropiado.\n"
            "6. Prohibido el acoso o bullying.\n"
            "7. No publicidad sin permiso.\n"
            "8. Mantén la privacidad de los demás.\n"
            "9. Sigue las indicaciones del staff.\n"
            "10. Diviértete y sé amable con todos.\n\n"
            "Para acceder al resto de los canales, reacciona con ✅ a este mensaje para obtener el rol **✅ Verificado**."
        )

        # Send rules message
        try:
            message = await reglas_channel.send(rules_text)
            await message.add_reaction("✅")
        except Exception as e:
            await interaction.response.send_message(f"Error al enviar el mensaje de reglas o agregar la reacción: {e}", ephemeral=True)
            return

        # Save verification info in bot and file
        self.verificacion = {
            "mensaje_id": message.id,
            "rol_id": verificado_role.id,
            "canal_id": reglas_channel.id,
            "no_verificado_role_id": no_verificado_role.id
        }
        self.bot.verificacion = self.verificacion
        self.save_config()

        await interaction.response.send_message(
            f"Configuración completada. Mensaje de reglas enviado en {reglas_channel.mention} y rol verificado creado.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not hasattr(self.bot, "verificacion") or not self.bot.verificacion:
            return
        guild = member.guild
        no_verificado_role_id = self.bot.verificacion.get("no_verificado_role_id")
        if no_verificado_role_id is None:
            return
        no_verificado_role = guild.get_role(no_verificado_role_id)
        if no_verificado_role is None:
            return
        try:
            await member.add_roles(no_verificado_role)
        except Exception as e:
            print(f"Error al asignar rol no verificado a nuevo miembro: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not hasattr(self.bot, "verificacion") or not self.bot.verificacion:
            return
        if payload.message_id == self.bot.verificacion["mensaje_id"] and str(payload.emoji) == "✅":
            guild = self.bot.get_guild(payload.guild_id)
            if guild is None:
                return
            miembro = guild.get_member(payload.user_id)
            if miembro is None or miembro.bot:
                return
            rol = guild.get_role(self.bot.verificacion["rol_id"])
            no_verificado_role = guild.get_role(self.bot.verificacion.get("no_verificado_role_id"))
            if rol is None or no_verificado_role is None:
                return
            if rol in miembro.roles:
                return
            try:
                await miembro.add_roles(rol)
                if no_verificado_role in miembro.roles:
                    await miembro.remove_roles(no_verificado_role)
                try:
                    await miembro.send("✅ Has sido verificado correctamente y se te ha asignado el rol **✅ Verificado**.")
                except Exception:
                    pass
            except Exception as e:
                print(f"Error al asignar rol o enviar mensaje de verificación: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not hasattr(self.bot, "verificacion") or not self.bot.verificacion:
            return
        if payload.message_id == self.bot.verificacion["mensaje_id"] and str(payload.emoji) == "✅":
            guild = self.bot.get_guild(payload.guild_id)
            if guild is None:
                return
            miembro = guild.get_member(payload.user_id)
            if miembro is None or miembro.bot:
                return
            rol = guild.get_role(self.bot.verificacion["rol_id"])
            no_verificado_role = guild.get_role(self.bot.verificacion.get("no_verificado_role_id"))
            if rol is None or no_verificado_role is None:
                return
            if rol not in miembro.roles:
                return
            try:
                await miembro.remove_roles(rol)
                if no_verificado_role not in miembro.roles:
                    await miembro.add_roles(no_verificado_role)
                try:
                    await miembro.send(f"❌ Has perdido el rol {rol.name} al quitar la reacción.")
                except Exception:
                    pass
            except Exception as e:
                print(f"Error al remover rol por quitar reacción: {e}")

async def setup(bot):
    await bot.add_cog(Verification(bot))
