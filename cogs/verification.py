import discord
from discord.ext import commands

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup_rules")
    @commands.has_permissions(administrator=True)
    async def setup_rules(self, ctx):
        """Setup the Reglas message, verificado role, and reaction for verification."""
        guild = ctx.guild

        # Delete existing "verificado" role if exists
        existing_role = discord.utils.get(guild.roles, name="verificado")
        if existing_role:
            try:
                await existing_role.delete(reason="Recreating verificado role for verification setup")
            except Exception as e:
                await ctx.send(f"Error al eliminar el rol existente: {e}")
                return

        # Create new "verificado" role
        try:
            verificado_role = await guild.create_role(name="verificado", reason="Rol para usuarios verificados")
        except Exception as e:
            await ctx.send(f"Error al crear el rol verificado: {e}")
            return

        # Find or create "Reglas" channel
        reglas_channel = discord.utils.get(guild.text_channels, name="reglas")
        if reglas_channel is None:
            try:
                reglas_channel = await guild.create_text_channel("reglas", reason="Canal para reglas y verificación")
            except Exception as e:
                await ctx.send(f"Error al crear el canal reglas: {e}")
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
            "Para acceder al resto de los canales, reacciona con ✅ a este mensaje para obtener el rol **verificado**."
        )

        # Send rules message
        try:
            message = await reglas_channel.send(rules_text)
            await message.add_reaction("✅")
        except Exception as e:
            await ctx.send(f"Error al enviar el mensaje de reglas o agregar la reacción: {e}")
            return

        # Save verification info in bot
        self.bot.verificacion = {
            "mensaje_id": message.id,
            "rol_id": verificado_role.id,
            "canal_id": reglas_channel.id
        }

        await ctx.send(f"Configuración completada. Mensaje de reglas enviado en {reglas_channel.mention} y rol verificado creado.")

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
            if rol is None:
                return
            if rol in miembro.roles:
                return
            try:
                await miembro.add_roles(rol)
                canal = guild.get_channel(self.bot.verificacion["canal_id"])
                if canal:
                    await canal.send(f"✅ {miembro.mention} fue verificado correctamente.")
            except Exception as e:
                print(f"Error al asignar rol o enviar mensaje de verificación: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if hasattr(self.bot, "verificacion_roles_msg_id") and self.bot.verificacion_roles_msg_id and payload.message_id == self.bot.verificacion_roles_msg_id:
            emoji = str(payload.emoji)
            if emoji in self.bot.emoji_rol_map:
                guild = self.bot.get_guild(payload.guild_id)
                if guild is None:
                    return
                miembro = guild.get_member(payload.user_id)
                if miembro is None or miembro.bot:
                    return
                rol_id = self.bot.emoji_rol_map[emoji]
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

async def setup(bot):
    await bot.add_cog(Verification(bot))
