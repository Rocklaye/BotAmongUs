"""
Bot Among Us - BotAmongUs Dashboard Server
================================================
Serveur Flask qui expose les données collectées par le bot
via une API REST consommée par le dashboard HTML.

USAGE ACADÉMIQUE UNIQUEMENT
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)   # Permet au dashboard.html (file:// ou autre port) d'appeler l'API
DB_PATH = "privacy_data.db"


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_risk_score(msg_count, metadata_fields, has_role, has_avatar, cross_channel):
    """
    Calcule un score de risque de 0 à 100 basé sur les données collectées.
    Inspiré des 6 mismatches du Tableau 2 du papier.
    """
    score = 0
    score += min(msg_count * 2, 30)          # Jusqu'à 30 pts selon le nb de messages
    score += metadata_fields * 5              # 5 pts par type de métadonnée exposée
    score += 10 if has_role else 0            # Rôle exposé
    score += 10 if has_avatar else 0          # Avatar exposé (profil)
    score += 15 if cross_channel else 0       # Messages dans plusieurs canaux
    return min(score, 100)


def risk_label(score):
    if score < 30:
        return {"label": "Faible", "color": "#22c55e", "icon": "🟢"}
    elif score < 60:
        return {"label": "Modéré", "color": "#f59e0b", "icon": "🟡"}
    else:
        return {"label": "Élevé", "color": "#ef4444", "icon": "🔴"}


# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.route("/api/overview")
def api_overview():
    """Vue d'ensemble globale du serveur."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM messages")
    total_messages = c.fetchone()["total"]

    c.execute("SELECT COUNT(DISTINCT author_id) as total FROM messages")
    unique_users = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as total FROM members WHERE is_bot = 0")
    total_members = c.fetchone()["total"]

    c.execute("SELECT COUNT(DISTINCT channel_name) as total FROM messages")
    channels = c.fetchone()["total"]

    c.execute("SELECT guild_name FROM messages LIMIT 1")
    row = c.fetchone()
    guild_name = row["guild_name"] if row else "Serveur inconnu"

    # Activité par heure (dernières 24h)
    c.execute("""
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
        FROM messages
        GROUP BY hour
        ORDER BY hour
    """)
    hourly = {row["hour"]: row["count"] for row in c.fetchall()}
    hourly_data = [hourly.get(f"{h:02d}", 0) for h in range(24)]

    # Top 5 utilisateurs les plus actifs
    c.execute("""
        SELECT author_display_name, author_username, COUNT(*) as msg_count
        FROM messages WHERE author_bot = 0
        GROUP BY author_id
        ORDER BY msg_count DESC
        LIMIT 5
    """)
    top_users = [dict(row) for row in c.fetchall()]

    conn.close()

    return jsonify({
        "guild_name": guild_name,
        "total_messages": total_messages,
        "unique_users": unique_users,
        "total_members": total_members,
        "channels_monitored": channels,
        "hourly_activity": hourly_data,
        "top_users": top_users,
        "collection_start": "Depuis que le bot a rejoint le serveur",
    })


@app.route("/api/users")
def api_users():
    """Liste de tous les utilisateurs profilés."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT
            m.author_id,
            m.author_username,
            m.author_display_name,
            m.author_avatar_url,
            m.author_top_role,
            m.author_joined_at,
            COUNT(*) as message_count,
            MIN(m.timestamp) as first_seen,
            MAX(m.timestamp) as last_seen,
            COUNT(DISTINCT m.channel_name) as channels_used
        FROM messages m
        WHERE m.author_bot = 0
        GROUP BY m.author_id
        ORDER BY message_count DESC
    """)

    users = []
    for row in c.fetchall():
        user = dict(row)

        # Calcul du score de risque
        metadata_fields = 4  # username, display_name, avatar, role (toujours collectés)
        cross_channel = user["channels_used"] > 1
        score = calculate_risk_score(
            user["message_count"],
            metadata_fields,
            bool(user["author_top_role"] and user["author_top_role"] != "Membre"),
            bool(user["author_avatar_url"]),
            cross_channel
        )
        user["risk_score"] = score
        user["risk"] = risk_label(score)

        # Données collectées (pour illustrer les mismatches)
        user["collected_data"] = {
            "content": f"{user['message_count']} messages lus",
            "username": user["author_username"],
            "display_name": user["author_display_name"],
            "avatar": bool(user["author_avatar_url"]),
            "role": user["author_top_role"],
            "joined_server": user["author_joined_at"],
            "channels": user["channels_used"],
            "first_seen": user["first_seen"],
            "last_seen": user["last_seen"],
        }

        users.append(user)

    conn.close()
    return jsonify(users)


@app.route("/api/user/<user_id>")
def api_user_detail(user_id):
    """Détail complet pour un utilisateur — son rapport de vie privée personnel."""
    conn = get_db()
    c = conn.cursor()

    # Infos de base
    c.execute("""
        SELECT
            author_id, author_username, author_display_name,
            author_avatar_url, author_top_role, author_joined_at,
            COUNT(*) as message_count,
            COUNT(DISTINCT channel_name) as channels_used,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen
        FROM messages
        WHERE author_id = ? AND author_bot = 0
        GROUP BY author_id
    """, (user_id,))

    row = c.fetchone()
    if not row:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    user = dict(row)

    # Tous ses messages (timeline)
    c.execute("""
        SELECT content, channel_name, timestamp
        FROM messages
        WHERE author_id = ?
        ORDER BY timestamp ASC
    """, (user_id,))
    messages = [dict(r) for r in c.fetchall()]

    # Activité par canal
    c.execute("""
        SELECT channel_name, COUNT(*) as count
        FROM messages
        WHERE author_id = ?
        GROUP BY channel_name
        ORDER BY count DESC
    """, (user_id,))
    channel_activity = [dict(r) for r in c.fetchall()]

    # Activité par heure
    c.execute("""
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
        FROM messages
        WHERE author_id = ?
        GROUP BY hour
        ORDER BY hour
    """, (user_id,))
    hourly_raw = {row["hour"]: row["count"] for row in c.fetchall()}
    hourly_data = [hourly_raw.get(f"{h:02d}", 0) for h in range(24)]

    # Score de risque
    cross_channel = user["channels_used"] > 1
    score = calculate_risk_score(
        user["message_count"],
        4,  # 4 types de métadonnées toujours collectées
        bool(user["author_top_role"] and user["author_top_role"] != "Membre"),
        bool(user["author_avatar_url"]),
        cross_channel
    )

    conn.close()

    return jsonify({
        "user": user,
        "messages": messages,
        "channel_activity": channel_activity,
        "hourly_activity": hourly_data,
        "risk_score": score,
        "risk": risk_label(score),
        "metadata_collected": {
            "Message Content": f"{user['message_count']} messages complets lus",
            "Username global": user["author_username"],
            "Pseudonyme serveur": user["author_display_name"],
            "Photo de profil": "Oui" if user["author_avatar_url"] else "Non",
            "Rôle dans le serveur": user["author_top_role"] or "Membre",
            "Date d'arrivée": user["author_joined_at"] or "Inconnue",
            "Canaux fréquentés": f"{user['channels_used']} canal(aux)",
            "Première activité": user["first_seen"],
            "Dernière activité": user["last_seen"],
        },
        # Les 6 mismatches du Tableau 2 illustrés avec les vraies données
        "mismatches": [
            {
                "type": "Scope",
                "expectation": "Le bot lit seulement les messages qui le mentionnent",
                "reality": f"Le bot a lu {user['message_count']} messages, y compris ceux qui ne le mentionnent pas",
                "severity": "high"
            },
            {
                "type": "Identity Exposure",
                "expectation": "Le bot voit le contenu mais pas l'identité de l'expéditeur",
                "reality": f"Username: {user['author_username']}, Pseudo: {user['author_display_name']}, Rôle: {user['author_top_role']}",
                "severity": "high"
            },
            {
                "type": "Data Retention",
                "expectation": "Les messages supprimés disparaissent pour le bot",
                "reality": "Une fois collectés, les messages restent dans la base de données même après suppression",
                "severity": "medium"
            },
            {
                "type": "Cross-Context Identity",
                "expectation": "Le bot ne peut pas suivre l'utilisateur entre les serveurs",
                "reality": f"L'identifiant unique {user['author_id']} est le même dans tous les serveurs Discord",
                "severity": "medium"
            },
            {
                "type": "Consent Model",
                "expectation": "Tous les membres ont consenti à la présence du bot",
                "reality": "L'admin peut ajouter ce bot sans demander l'accord des membres",
                "severity": "high"
            },
            {
                "type": "Visibility",
                "expectation": "Le bot n'est actif que quand il répond",
                "reality": "Le bot collecte silencieusement TOUS les messages, même quand il ne répond pas",
                "severity": "high"
            }
        ]
    })


@app.route("/api/members")
def api_members():
    """Liste des membres du serveur collectés (Group Metadata)."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT user_id, username, display_name, avatar_url,
               top_role, joined_at, created_at, is_bot, collected_at
        FROM members
        WHERE is_bot = 0
        ORDER BY collected_at ASC
    """)

    members = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(members)


@app.route("/api/stats")
def api_stats():
    """Statistiques globales pour les graphiques."""
    conn = get_db()
    c = conn.cursor()

    # Messages par canal
    c.execute("""
        SELECT channel_name, COUNT(*) as count
        FROM messages
        GROUP BY channel_name
        ORDER BY count DESC
    """)
    by_channel = [dict(r) for r in c.fetchall()]

    # Messages par jour
    c.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as count
        FROM messages
        GROUP BY day
        ORDER BY day ASC
        LIMIT 30
    """)
    by_day = [dict(r) for r in c.fetchall()]

    conn.close()
    return jsonify({
        "by_channel": by_channel,
        "by_day": by_day,
    })

@app.route("/api/permissions")
def api_permissions():
    """Expose les intents et permissions du bot pour le dashboard."""

    data = {
        "bot_name": "BotAmongUs",
        "intents": {
            "message_content": {
                "label": "Lire le contenu des messages",
                "value": True
            },
            "members": {
                "label": "Voir les membres",
                "value": True
            },
            "presences": {
                "label": "Voir les présences",
                "value": True
            }
        },
        "server_permissions": {
            "view_channel": {
                "label": "Voir les salons",
                "value": True
            },
            "read_message_history": {
                "label": "Lire l’historique",
                "value": True
            },
            "send_messages": {
                "label": "Envoyer des messages",
                "value": True
            },
            "manage_messages": {
                "label": "Gérer les messages",
                "value": False
            },
            "ban_members": {
                "label": "Bannir des membres",
                "value": False
            }
        }
    }

    return jsonify(data)


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("="*50)
    print("  BotAmongUs Dashboard")
    print("  http://localhost:5000")
    print("  Bot Among Us - PoPETs 2026")
    print("="*50)
    app.run(debug=True, port=5000)
