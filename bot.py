"""
Bot Among Us — BotAmongUs Bot
===================================
Démo académique basée sur l'article "Bot Among Us" (PoPETs 2026)
Ce bot collecte les données accessibles par un vrai bot Discord
et les stocke pour générer un Privacy Report Dashboard.

USAGE ACADÉMIQUE UNIQUEMENT - NE PAS DÉPLOYER EN PRODUCTION
"""

import discord
import sqlite3
import json
from datetime import datetime
from discord.ext import commands

# ─── CONFIG ──────────────────────────────────────────────────────────────────
TOKEN = ""   # Remplacez par votre token Discord
DB_PATH = "privacy_data.db"
# ─────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True      # Message Content Intent (activé dans le portal)
intents.members = True              # Server Members Intent
intents.presences = True            # Presence Intent

bot = commands.Bot(command_prefix="!", intents=intents)


# ─── BASE DE DONNÉES ──────────────────────────────────────────────────────────

def init_db():
    """Initialise la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Table des messages collectés
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            guild_id TEXT,
            guild_name TEXT,
            channel_id TEXT,
            channel_name TEXT,
            author_id TEXT,
            author_username TEXT,
            author_display_name TEXT,
            author_avatar_url TEXT,
            author_bot INTEGER,
            author_joined_at TEXT,
            author_top_role TEXT,
            content TEXT,
            timestamp TEXT,
            created_at TEXT
        )
    """)

    # Table des membres collectés (Group Metadata)
    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            guild_name TEXT,
            user_id TEXT,
            username TEXT,
            display_name TEXT,
            avatar_url TEXT,
            top_role TEXT,
            joined_at TEXT,
            created_at TEXT,
            is_bot INTEGER,
            collected_at TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Base de données initialisée.")


def save_message(message):
    """Sauvegarde un message et ses métadonnées dans la DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    author = message.author
    guild = message.guild
    channel = message.channel

    # Récupère le rôle le plus haut de l'auteur
    top_role = "Membre"
    if hasattr(author, "roles") and len(author.roles) > 1:
        top_role = author.roles[-1].name

    # Date d'arrivée dans le serveur
    joined_at = ""
    if hasattr(author, "joined_at") and author.joined_at:
        joined_at = author.joined_at.isoformat()

    c.execute("""
        INSERT INTO messages (
            message_id, guild_id, guild_name, channel_id, channel_name,
            author_id, author_username, author_display_name, author_avatar_url,
            author_bot, author_joined_at, author_top_role,
            content, timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(message.id),
        str(guild.id) if guild else "DM",
        guild.name if guild else "DM",
        str(channel.id),
        channel.name if hasattr(channel, "name") else "DM",
        str(author.id),
        str(author),                          # username#discriminator
        author.display_name,                  # pseudo dans le serveur
        str(author.display_avatar.url) if author.display_avatar else "",
        1 if author.bot else 0,
        joined_at,
        top_role,
        message.content,
        message.created_at.isoformat(),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def save_members(guild):
    """Sauvegarde tous les membres du serveur (Group Metadata)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for member in guild.members:
        top_role = "Membre"
        if len(member.roles) > 1:
            top_role = member.roles[-1].name

        joined_at = member.joined_at.isoformat() if member.joined_at else ""

        c.execute("""
            INSERT OR IGNORE INTO members (
                guild_id, guild_name, user_id, username, display_name,
                avatar_url, top_role, joined_at, created_at, is_bot, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(guild.id),
            guild.name,
            str(member.id),
            str(member),
            member.display_name,
            str(member.display_avatar.url) if member.display_avatar else "",
            top_role,
            joined_at,
            member.created_at.isoformat(),
            1 if member.bot else 0,
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()
    print(f"[BOT] {len(guild.members)} membres collectés dans '{guild.name}'")


# ─── ÉVÉNEMENTS ──────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    """Le bot est connecté et prêt."""
    print(f"\n{'='*50}")
    print(f"  PrivacyReportBot connecté : {bot.user}")
    print(f"  Serveurs : {[g.name for g in bot.guilds]}")
    print(f"  Dashboard : http://localhost:5000")
    print(f"{'='*50}\n")

    # Collecte immédiate des membres de tous les serveurs
    for guild in bot.guilds:
        await guild.chunk()   # Force le chargement de tous les membres
        save_members(guild)

@bot.event
async def on_guild_join(guild):
    """Notification A.1 : Le bot vient d'être ajouté au serveur."""
    await guild.chunk()
    save_members(guild)

    # Sélection du canal (système ou premier canal disponible)
    target_channel = guild.system_channel
    if target_channel is None or not target_channel.permissions_for(guild.me).send_messages:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break

    if target_channel:
        await target_channel.send(
            f"Bonjour ! Je suis **{bot.user.name}**\n"
            "Je viens d'être ajouté à ce serveur. Voici ce que je peux voir :\n"
            "– Messages publics\n"
            "– Métadonnées (pseudo, avatar, rôle)\n"
            "– Activité dans les canaux\n"
            "Pour plus d'informations : tapez `!permissions`."
        )

# NOTE : Modifiez votre fonction on_member_join existante (ligne 213) 
# pour y ajouter ces lignes à la fin :

@bot.event
async def on_message(message):
    """Intercepte TOUS les messages — comme un vrai bot Discord avec Message Content Intent."""
    # Ne collecte pas ses propres messages
    if message.author == bot.user:
        return

    # Sauvegarde silencieuse du message
    save_message(message)

    guild_name = message.guild.name if message.guild else "DM"
    print(f"[COLLECTE] {message.author.display_name} dans #{message.channel}: {message.content[:60]}...")

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    """Collecte + notification A.2"""

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    top_role = "Membre"
    if len(member.roles) > 1:
        top_role = member.roles[-1].name

    joined_at = member.joined_at.isoformat() if member.joined_at else ""

    c.execute("""
        INSERT OR IGNORE INTO members (
            guild_id, guild_name, user_id, username, display_name,
            avatar_url, top_role, joined_at, created_at, is_bot, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(member.guild.id),
        member.guild.name,
        str(member.id),
        str(member),
        member.display_name,
        str(member.display_avatar.url) if member.display_avatar else "",
        top_role,
        joined_at,
        member.created_at.isoformat(),
        1 if member.bot else 0,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    print(f"[BOT] Nouveau membre collecté : {member.display_name}")

    # 🔔 NOTIFICATION (A.2)
    try:
        await member.send(
            f"Rappel : un bot nommé **{bot.user.name}** est présent dans le serveur **{member.guild.name}**.\n"
            "Il a pour rôle : analyse de la vie privée / projet académique.\n"
            "Tapez `!permissions` pour voir ce qu'il peut lire."
        )
    except discord.Forbidden:
        if member.guild.system_channel and member.guild.system_channel.permissions_for(member.guild.me).send_messages:
            await member.guild.system_channel.send(
                f"Bienvenue {member.mention} ! "
                f"Note : le bot {bot.user.name} est présent pour analyse. "
                "Tapez `!permissions`."
            )

# ─── COMMANDES ───────────────────────────────────────────────────────────────

@bot.command(name="rapport")
async def rapport(ctx):
    """!rapport — Le bot répond avec le lien vers le dashboard."""
    await ctx.send(
        f"📊 **BotAmongUs disponible !**\n"
        f"Consultez votre rapport de vie privée ici : http://localhost:5000\n"
        f"*(Démo académique — Bot Among Us, PoPETs 2026)*"
    )


@bot.command(name="stats")
async def stats(ctx):
    """!stats — Affiche les stats de collecte dans le chat."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM messages")
    msg_count = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT author_id) FROM messages")
    user_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM members")
    member_count = c.fetchone()[0]

    conn.close()

    await ctx.send(
        f"🤖 **Ce que j'ai collecté jusqu'ici :**\n"
        f"📨 Messages lus : **{msg_count}**\n"
        f"👤 Utilisateurs profilés : **{user_count}**\n"
        f"👥 Membres du serveur collectés : **{member_count}**\n"
        f"🔗 Rapport complet : http://localhost:5000"
    )


# ─── LANCEMENT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("[BOT] Démarrage du bot Discord...")
    print("[BOT] Appuyez sur Ctrl+C pour arrêter.")
    bot.run(TOKEN)
