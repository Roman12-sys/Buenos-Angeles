# Funciones auxiliares comunes para el bot de Discord
import discord
import json
import os
import re
from datetime import timedelta

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

def load_json(file_path):
    """Carga datos desde un archivo JSON."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    """Guarda datos en un archivo JSON."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def parse_time(time_str):
    """Parsea tiempo como '10m', '2h', '3d' a segundos."""
    match = re.match(r'^(\d+)([mhd])$', time_str.lower())
    if not match:
        raise ValueError("Formato de tiempo inválido. Usa '10m', '2h', '3d'.")
    num, unit = match.groups()
    num = int(num)
    if unit == 'm':
        return num * 60
    elif unit == 'h':
        return num * 3600
    elif unit == 'd':
        return num * 86400

def format_time(seconds):
    """Formatea segundos a string legible."""
    td = timedelta(seconds=seconds)
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"
