"""
BotAmongUs — Bot Discord
=========================
Démo académique basée sur l'article "Bot Among Us" (PoPETs 2026)

MODULE 1 — Mode Silencieux
  Reproduit ce que le papier dénonce : collecte silencieuse de tous
  les messages et métadonnées sans que les utilisateurs le sachent.

MODULE 2 — Mode Perspective
  Implémente les recommandations des auteurs (5.3) :
  - Notification au premier join du bot (5.3.1)
  - Notification aux nouveaux membres (5.3.5)
  - Commande !permissions (5.3.2)
  - Commande !mode pour switcher sans redémarrage

USAGE ACADÉMIQUE UNIQUEMENT — NE PAS DÉPLOYER EN PRODUCTION
"""

import discord
import sqlite3
import os
from datetime import datetime
from discord.ext import commands

# ─── CONFIG ──────────────────────────────────────────────────────────────────
TOKEN   = ""  # Collez votre token Discord ici
DB_PATH = "privacy_data.db"
# ─────────────────────────────────────────────────────────────────────────────

# ─── MODE GLOBAL ─────────────────────────────────────────────────────────────
# Partagé avec app.py via current_mode.txt.
# Le dashboard switche le mode via POST /api/mode sans redémarrer le bot.
MODE_FILE = "current_mode.txt"

def get_mode() -> str:
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, "r") as f:
            return f.read().strip()
    return "silencieux"

def set_mode(mode: str):
    with open(MODE_FILE, "w") as f:
        f.write(mode)
# ─────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True   # Lire le contenu des messages
intents.members         = True   # Voir la liste des membres
intents.presences       = True   # Voir les présences/statuts

#bot = commands.Bot(command_prefix="!", intents=intents) 
#descativer le help integre de discord
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)



# ══════════════════════════════════════════════════════════════════════════════
#  BASE DE DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Crée les tables si elles n'existent pas encore."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id          TEXT,
            guild_id            TEXT,
            guild_name          TEXT,
            channel_id          TEXT,
            channel_name        TEXT,
            author_id           TEXT,
            author_username     TEXT,
            author_display_name TEXT,
            author_avatar_url   TEXT,
            author_bot          INTEGER,
            author_joined_at    TEXT,
            author_top_role     TEXT,
            content             TEXT,
            timestamp           TEXT,
            created_at          TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT,
            guild_name   TEXT,
            user_id      TEXT,
            username     TEXT,
            display_name TEXT,
            avatar_url   TEXT,
            top_role     TEXT,
            joined_at    TEXT,
            created_at   TEXT,
            is_bot       INTEGER,
            collected_at TEXT,
            UNIQUE(guild_id, user_id)
        )
    """)

    # Table pour savoir si le bot a déjà envoyé son message de bienvenue
    # dans un serveur donné (évite les doublons au redémarrage)
    c.execute("""
        CREATE TABLE IF NOT EXISTS guild_welcomed (
            guild_id TEXT PRIMARY KEY,
            welcomed_at TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Base de données initialisée.")


def save_message(message):
    """Sauvegarde un message et ses métadonnées dans la DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    author  = message.author
    guild   = message.guild
    channel = message.channel

    top_role  = "Membre"
    if hasattr(author, "roles") and len(author.roles) > 1:
        top_role = author.roles[-1].name

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
        str(guild.id)   if guild   else "DM",
        guild.name      if guild   else "DM",
        str(channel.id),
        channel.name    if hasattr(channel, "name") else "DM",
        str(author.id),
        str(author),
        author.display_name,
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
        top_role  = "Membre"
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
    print(f"[DB] {len(guild.members)} membres collectés dans '{guild.name}'")


def has_been_welcomed(guild_id: str) -> bool:
    """Vérifie si le bot a déjà envoyé son message de bienvenue dans ce serveur."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM guild_welcomed WHERE guild_id = ?", (guild_id,))
    result = c.fetchone()
    conn.close()
    return result is not None


def mark_as_welcomed(guild_id: str):
    """Enregistre que le bot a envoyé son message de bienvenue dans ce serveur."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO guild_welcomed (guild_id, welcomed_at) VALUES (?, ?)",
        (guild_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS — NOTIFICATIONS (Module 2)
# ══════════════════════════════════════════════════════════════════════════════

def get_general_channel(guild):
    """
    Retourne le meilleur canal pour envoyer une notification :
    1. Canal nommé 'general'
    2. Canal système du serveur
    3. Premier canal texte où le bot peut écrire
    """
    for channel in guild.text_channels:
        if channel.name == "general" and channel.permissions_for(guild.me).send_messages:
            return channel

    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        return guild.system_channel

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel

    return None


async def send_first_join_notification(guild):
    """
    Module 2 — §5.3.1
    Message envoyé UNE SEULE FOIS quand le bot rejoint un nouveau serveur.
    Informe tous les membres de la présence et des capacités du bot.
    """
    channel = get_general_channel(guild)
    if not channel:
        print(f"[MODULE 2] Aucun canal disponible dans '{guild.name}'")
        return

    guild_perms = guild.me.guild_permissions
    msg = (
        f"👋 Bonjour ! Je suis **{bot.user.name}**.\n\n"
        f"Je viens d'être ajouté à ce serveur par un administrateur.\n\n"
        f"**Mon rôle :** démonstration académique sur la vie privée des bots "
        f"dans les groupes de messagerie *(Bot Among Us, PoPETs 2026)*.\n\n"
        f"**Voici ce que je peux voir sur ce serveur :**\n"
        f"– Contenu de tous les messages publics\n"
        f"– Métadonnées : pseudo, avatar, rôle de chaque membre\n"
        f"– Activité dans les canaux (qui écrit, quand)\n"
        f"– Liste complète des membres et leurs profils\n"
        f"– Identifiants uniques persistants (traçabilité cross-serveurs)\n\n"
        f"**Permissions serveur actives :**\n"
        f"– Voir les salons : {'✅' if guild_perms.view_channel else '❌'}\n"
        f"– Lire l'historique : {'✅' if guild_perms.read_message_history else '❌'}\n"
        f"– Envoyer des messages : {'✅' if guild_perms.send_messages else '❌'}\n"
        f"– Gérer les messages : {'✅' if guild_perms.manage_messages else '❌'}\n"
        f"– Expulser des membres : {'✅' if guild_perms.kick_members else '❌'}\n"
        f"– Bannir des membres : {'✅' if guild_perms.ban_members else '❌'}\n\n"
        f"ℹ️ Tapez `!permissions` pour une vue complète de mes accès.\n"
        f"ℹ️ Tapez `!mode` pour voir mon mode de fonctionnement actuel."
    )

    await channel.send(msg)
    mark_as_welcomed(str(guild.id))
    print(f"[MODULE 2] Notification de premier join envoyée dans '{guild.name}' → #{channel.name}")


async def send_new_member_notification(member):
    """
    Module 2 — §5.3.5
    Message envoyé dans #general quand un nouveau membre rejoint.
    L'informe qu'un bot actif collecte des données sur ce serveur.
    """
    channel = get_general_channel(member.guild)
    if not channel:
        return

    msg = (
        f"👋 Bienvenue **{member.display_name}** !\n\n"
        f"Ce serveur utilise un bot actif : **{bot.user.name}**.\n\n"
        f"**Ce qu'il peut voir sur toi dès maintenant :**\n"
        f"– Tes messages publics (contenu + horodatage)\n"
        f"– Ton pseudo, avatar et rôle dans ce serveur\n"
        f"– Ton activité dans les canaux\n"
        f"– Ton identifiant unique Discord\n\n"
        f"Tapez `!permissions` pour voir l'ensemble de ses accès et sa politique de données."
    )

    await channel.send(msg)
    print(f"[MODULE 2] Notification nouveau membre envoyée pour {member.display_name}")


# ══════════════════════════════════════════════════════════════════════════════
#  ÉVÉNEMENTS
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    """Bot connecté — collecte immédiate des membres de tous les serveurs."""
    print(f"\n{'='*54}")
    print(f"  BotAmongUs connecté : {bot.user}")
    print(f"  Mode actuel         : {get_mode().upper()}")
    print(f"  Serveurs            : {[g.name for g in bot.guilds]}")
    print(f"  Dashboard           : http://localhost:5000")
    print(f"{'='*54}\n")

    for guild in bot.guilds:
        await guild.chunk()
        save_members(guild)

        # Module 2 — envoie la notif de premier join si pas encore fait
        if get_mode() == "perspective" and not has_been_welcomed(str(guild.id)):
            await send_first_join_notification(guild)


@bot.event
async def on_guild_join(guild):
    """
    Le bot vient d'être ajouté à un nouveau serveur.
    Collecte les membres + notification si mode perspective.
    """
    await guild.chunk()
    save_members(guild)
    print(f"[BOT] Rejoint le serveur '{guild.name}'")

    if get_mode() == "perspective":
        await send_first_join_notification(guild)


@bot.event
async def on_message(message):
    """
    Intercepte TOUS les messages (Module 1 + 2).
    La collecte est active dans les deux modes.
    """
    if message.author == bot.user:
        return

    save_message(message)
    print(f"[COLLECTE] {message.author.display_name} → #{message.channel}: {message.content[:60]}...")

    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    """
    Nouveau membre — collecte immédiate.
    Notification dans #general si mode perspective.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    top_role  = "Membre"
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
    print(f"[DB] Nouveau membre collecté : {member.display_name}")

    # Module 2 — notification dans #general
    if get_mode() == "perspective":
        await send_new_member_notification(member)


# ══════════════════════════════════════════════════════════════════════════════
#  COMMANDES
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="mode")
async def cmd_mode(ctx):
    """
    !mode — Affiche le mode actuel et permet de switcher.
    Fonctionne sans redémarrage du bot.
    Endpoint API : GET/POST /api/mode (pour le dashboard)
    """
    # mode via get_mode()/set_mode()

    if get_mode() == "silencieux":
        set_mode("perspective")
        await ctx.send(
            f"🔄 Mode changé → **PERSPECTIVE** activé.\n\n"
            f"Le bot va maintenant :\n"
            f"– Se signaler aux nouveaux membres dans #general\n"
            f"– Afficher ses permissions sur demande (`!permissions`)\n"
            f"– Notifier les futurs membres à leur arrivée\n\n"
            f"La collecte de données reste identique au mode silencieux."
        )
    else:
        set_mode("silencieux")
        await ctx.send(
            f"🔄 Mode changé → **SILENCIEUX** activé.\n\n"
            f"Le bot collecte silencieusement sans envoyer de notifications.\n"
            f"*(Mode démonstration du problème — §4 du papier)*"
        )

    print(f"[MODE] Changement → {get_mode().upper()}")


@bot.command(name="permissions")
async def cmd_permissions(ctx):
    """
    !permissions — Affiche les intents et permissions réels du bot.
    Module 2 — §5.3.2 "Provide Transparent Permission Explanations"
    Inspiré du concept de 'privacy nutrition label' (Kelley et al., 2009)
    cité dans le papier.
    """
    guild_perms = ctx.guild.me.guild_permissions if ctx.guild else None

    def yn(val): return "OUI ✅" if val else "NON ❌"

    msg = (
        f"🔍 **Informations sur {bot.user.name} — Mode {get_mode().capitalize()}**\n"
        f"*(Commande de transparence — §5.3.2, Bot Among Us, PoPETs 2026)*\n\n"

        f"🧠 **Intents activés (capacités techniques) :**\n"
        f"– Lire le contenu des messages : {yn(bot.intents.message_content)}\n"
        f"– Voir les membres du serveur   : {yn(bot.intents.members)}\n"
        f"– Voir les statuts/présences    : {yn(bot.intents.presences)}\n"
        f"– Recevoir les réactions        : {yn(bot.intents.reactions)}\n"
        f"– Accéder aux événements modération : NON ❌\n\n"

        f"🔐 **Permissions serveur (ce que je suis autorisé à faire ici) :**\n"
        f"– Voir les salons               : {yn(guild_perms.view_channel if guild_perms else False)}\n"
        f"– Lire l'historique des messages : {yn(guild_perms.read_message_history if guild_perms else False)}\n"
        f"– Envoyer des messages          : {yn(guild_perms.send_messages if guild_perms else False)}\n"
        f"– Envoyer des embeds            : {yn(guild_perms.embed_links if guild_perms else False)}\n"
        f"– Gérer les messages            : {yn(guild_perms.manage_messages if guild_perms else False)}\n"
        f"– Supprimer des messages        : NON ❌\n"
        f"– Expulser des membres          : {yn(guild_perms.kick_members if guild_perms else False)}\n"
        f"– Bannir des membres            : {yn(guild_perms.ban_members if guild_perms else False)}\n"
        f"– Gérer les rôles               : {yn(guild_perms.manage_roles if guild_perms else False)}\n\n"

        f"📘 **Politique de collecte et d'utilisation des données :**\n"
        f"– Je collecte les messages, métadonnées et profils des membres.\n"
        f"– Les données sont stockées localement (SQLite) à des fins académiques.\n"
        f"– Aucune donnée n'est partagée en dehors de ce serveur.\n"
        f"– Les messages supprimés restent dans la base de données locale.\n"
        f"– Votre identifiant Discord est persistent et unique cross-serveurs.\n\n"

        f"ℹ️ Tapez `!mode` pour voir ou changer mon mode de fonctionnement.\n"
        f"ℹ️ Tapez `!rapport` pour accéder au dashboard de vie privée.\n"
        f"ℹ️ Tapez `!stats` pour voir ce que j'ai collecté jusqu'ici."
    )

    await ctx.send(msg)


@bot.command(name="rapport")
async def cmd_rapport(ctx):
    """!rapport — Lien vers le dashboard Privacy Report."""
    await ctx.send(
        f"📊 **Dashboard BotAmongUs**\n"
        f"Consultez votre rapport de vie privée : http://localhost:5000\n"
        f"*(Démo académique — Bot Among Us, PoPETs 2026)*"
    )


@bot.command(name="stats")
async def cmd_stats(ctx):
    """!stats — Statistiques de collecte en temps réel."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM messages")
    msg_count = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT author_id) FROM messages")
    user_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM members WHERE is_bot = 0")
    member_count = c.fetchone()[0]
    conn.close()

    await ctx.send(
        f"🤖 **Ce que j'ai collecté jusqu'ici — Mode {get_mode().capitalize()} :**\n"
        f"📨 Messages lus      : **{msg_count}**\n"
        f"👤 Utilisateurs      : **{user_count}**\n"
        f"👥 Membres collectés : **{member_count}**\n"
        f"🔗 Dashboard         : http://localhost:5000"
    )


@bot.command(name="help")
async def cmd_help(ctx):
    """!help — Liste toutes les commandes disponibles."""
    await ctx.send(
        f"📖 **Commandes BotAmongUs :**\n\n"
        f"`!mode`        - Switcher entre Mode Silencieux et Mode Perspective\n"
        f"`!permissions` - Afficher mes intents, permissions et politique de données\n"
        f"`!stats`       - Voir ce que j'ai collecté jusqu'ici\n"
        f"`!rapport`     - Accéder au dashboard de vie privée\n"
        f"`!help`        - Afficher cette aide\n\n"
        f"Mode actuel : **{get_mode().upper()}**"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print("[BOT] Démarrage de BotAmongUs...")
    print(f"[BOT] Mode initial : {get_mode().upper()}")
    print("[BOT] Ctrl+C pour arrêter.")
    bot.run(TOKEN)
