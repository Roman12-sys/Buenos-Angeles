# Funciones auxiliares comunes para el bot de Discord
import discord

async def crear_categoria(guild, nombre):
    for category in guild.categories:
        if category.name == nombre:
            return category
    return await guild.create_category(nombre)

async def crear_rol(guild, nombre):
    for rol in guild.roles:
        if rol.name == nombre:
            return rol
    return await guild.create_role(name=nombre, mentionable=True)
