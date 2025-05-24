import discord
from discord.ext import commands

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
