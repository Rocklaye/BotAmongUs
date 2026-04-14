"""
BotAmongUs — API Flask
=======================
Expose les données collectées par bot.py via une API REST.
Inclut l'endpoint /api/mode pour lire et switcher le mode
depuis le dashboard sans redémarrer le bot.

CORS activé : le dashboard.html peut appeler depuis file:// ou tout autre port.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import sys

app = Flask(__name__)
CORS(app)

DB_PATH = "privacy_data.db"

# ─── MODE PARTAGÉ ─────────────────────────────────────────────────────────────
# Ce dictionnaire est partagé en mémoire.
# bot.py importe app.py via "from app import shared_state" si besoin,
# mais ici on utilise un fichier mode.txt pour la communication inter-process.
MODE_FILE = "current_mode.txt"

def get_mode():
    """Lit le mode actuel depuis le fichier partagé."""
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, "r") as f:
            return f.read().strip()
    return "silencieux"

def set_mode(mode):
    """Écrit le nouveau mode dans le fichier partagé."""
    with open(MODE_FILE, "w") as f:
        f.write(mode)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_risk_score(msg_count, has_role, has_avatar, cross_channel):
    score = 0
    score += min(msg_count * 2, 30)
    score += 20                          # username + display_name toujours collectés
    score += 10 if has_role    else 0
    score += 10 if has_avatar  else 0
    score += 15 if cross_channel else 0
    return min(score, 100)


def risk_label(score):
    if score < 30:
        return {"label": "Faible",  "color": "#22c55e", "icon": "🟢"}
    elif score < 60:
        return {"label": "Modéré",  "color": "#f59e0b", "icon": "🟡"}
    else:
        return {"label": "Élevé",   "color": "#ff4757", "icon": "🔴"}


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINT MODE — switch sans redémarrage
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/mode", methods=["GET"])
def api_get_mode():
    """Retourne le mode actuel."""
    return jsonify({"mode": get_mode()})


@app.route("/api/mode", methods=["POST"])
def api_set_mode():
    """
    Change le mode (silencieux ↔ perspective).
    Le bot lit ce fichier à chaque événement Discord.
    Body JSON : { "mode": "perspective" } ou { "mode": "silencieux" }
    Ou sans body : toggle automatique.
    """
    data = request.get_json(silent=True) or {}
    if "mode" in data and data["mode"] in ("silencieux", "perspective"):
        new_mode = data["mode"]
    else:
        # Toggle
        new_mode = "perspective" if get_mode() == "silencieux" else "silencieux"

    set_mode(new_mode)
    print(f"[API] Mode changé → {new_mode.upper()}")
    return jsonify({"mode": new_mode, "changed": True})


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/overview")
def api_overview():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM messages")
    total_messages = c.fetchone()["total"]

    c.execute("SELECT COUNT(DISTINCT author_id) as total FROM messages WHERE author_bot = 0")
    unique_users = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as total FROM members WHERE is_bot = 0")
    total_members = c.fetchone()["total"]

    c.execute("SELECT COUNT(DISTINCT channel_name) as total FROM messages")
    channels = c.fetchone()["total"]

    c.execute("SELECT guild_name FROM messages LIMIT 1")
    row = c.fetchone()
    guild_name = row["guild_name"] if row else "Serveur inconnu"

    c.execute("""
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
        FROM messages GROUP BY hour ORDER BY hour
    """)
    hourly = {row["hour"]: row["count"] for row in c.fetchall()}
    hourly_data = [hourly.get(f"{h:02d}", 0) for h in range(24)]

    c.execute("""
        SELECT author_display_name, author_username, COUNT(*) as msg_count
        FROM messages WHERE author_bot = 0
        GROUP BY author_id ORDER BY msg_count DESC LIMIT 5
    """)
    top_users = [dict(r) for r in c.fetchall()]

    conn.close()
    return jsonify({
        "guild_name":        guild_name,
        "total_messages":    total_messages,
        "unique_users":      unique_users,
        "total_members":     total_members,
        "channels_monitored":channels,
        "hourly_activity":   hourly_data,
        "top_users":         top_users,
        "current_mode":      get_mode(),
    })


@app.route("/api/users")
def api_users():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT
            author_id, author_username, author_display_name,
            author_avatar_url, author_top_role, author_joined_at,
            COUNT(*) as message_count,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen,
            COUNT(DISTINCT channel_name) as channels_used
        FROM messages
        WHERE author_bot = 0
        GROUP BY author_id
        ORDER BY message_count DESC
    """)

    users = []
    for row in c.fetchall():
        u = dict(row)
        score = calculate_risk_score(
            u["message_count"],
            bool(u["author_top_role"] and u["author_top_role"] != "Membre"),
            bool(u["author_avatar_url"]),
            u["channels_used"] > 1
        )
        u["risk_score"] = score
        u["risk"]       = risk_label(score)
        users.append(u)

    conn.close()
    return jsonify(users)


@app.route("/api/user/<user_id>")
def api_user_detail(user_id):
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT author_id, author_username, author_display_name,
               author_avatar_url, author_top_role, author_joined_at,
               COUNT(*) as message_count,
               COUNT(DISTINCT channel_name) as channels_used,
               MIN(timestamp) as first_seen,
               MAX(timestamp) as last_seen
        FROM messages WHERE author_id = ? AND author_bot = 0
        GROUP BY author_id
    """, (user_id,))

    row = c.fetchone()
    if not row:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    user = dict(row)

    c.execute("""
        SELECT content, channel_name, timestamp
        FROM messages WHERE author_id = ?
        ORDER BY timestamp ASC
    """, (user_id,))
    messages = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT channel_name, COUNT(*) as count
        FROM messages WHERE author_id = ?
        GROUP BY channel_name ORDER BY count DESC
    """, (user_id,))
    channel_activity = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
        FROM messages WHERE author_id = ?
        GROUP BY hour ORDER BY hour
    """, (user_id,))
    hourly_raw  = {r["hour"]: r["count"] for r in c.fetchall()}
    hourly_data = [hourly_raw.get(f"{h:02d}", 0) for h in range(24)]

    score = calculate_risk_score(
        user["message_count"],
        bool(user["author_top_role"] and user["author_top_role"] != "Membre"),
        bool(user["author_avatar_url"]),
        user["channels_used"] > 1
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
            "Contenu des messages":   f"{user['message_count']} messages complets lus",
            "Username global":        user["author_username"],
            "Pseudonyme serveur":     user["author_display_name"],
            "Photo de profil":        "Oui" if user["author_avatar_url"] else "Non",
            "Rôle dans le serveur":   user["author_top_role"] or "Membre",
            "Date d'arrivée":         (user["author_joined_at"] or "—")[:10],
            "Canaux fréquentés":      f"{user['channels_used']} canal(aux)",
            "Première activité":      (user["first_seen"] or "—")[:19],
            "Dernière activité":      (user["last_seen"]  or "—")[:19],
            "Identifiant unique":     user["author_id"] + " (persistent cross-serveurs)",
        },
        "mismatches": [
            {
                "type": "Scope",
                "severity": "high",
                "expectation": "Le bot lit seulement les messages qui le mentionnent",
                "reality": f"Le bot a lu {user['message_count']} messages, y compris ceux qui ne le mentionnent pas"
            },
            {
                "type": "Identity Exposure",
                "severity": "high",
                "expectation": "Le bot voit le contenu mais pas l'identité de l'expéditeur",
                "reality": f"Username: {user['author_username']}, Pseudo: {user['author_display_name']}, Rôle: {user['author_top_role']}"
            },
            {
                "type": "Data Retention",
                "severity": "medium",
                "expectation": "Les messages supprimés disparaissent pour le bot",
                "reality": "Une fois collectés, les messages restent dans la DB même après suppression"
            },
            {
                "type": "Cross-Context Identity",
                "severity": "medium",
                "expectation": "Le bot ne peut pas suivre l'utilisateur entre les serveurs",
                "reality": f"L'identifiant {user['author_id']} est identique dans tous les serveurs Discord"
            },
            {
                "type": "Consent Model",
                "severity": "high",
                "expectation": "Tous les membres ont consenti à la présence du bot",
                "reality": "L'admin peut ajouter ce bot sans demander l'accord des autres membres"
            },
            {
                "type": "Visibility",
                "severity": "high",
                "expectation": "Le bot n'est actif que quand il répond",
                "reality": "Le bot collecte silencieusement TOUS les messages, même sans répondre"
            }
        ]
    })


@app.route("/api/members")
def api_members():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT user_id, username, display_name, avatar_url,
               top_role, joined_at, created_at, is_bot, collected_at
        FROM members WHERE is_bot = 0 ORDER BY collected_at ASC
    """)
    members = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(members)


@app.route("/api/stats")
def api_stats():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT channel_name, COUNT(*) as count
        FROM messages GROUP BY channel_name ORDER BY count DESC
    """)
    by_channel = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as count
        FROM messages GROUP BY day ORDER BY day ASC LIMIT 30
    """)
    by_day = [dict(r) for r in c.fetchall()]

    conn.close()
    return jsonify({"by_channel": by_channel, "by_day": by_day})


# ══════════════════════════════════════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*54)
    print("  BotAmongUs — API Flask")
    print("  http://localhost:5000")
    print("  CORS activé — dashboard.html peut appeler librement")
    print("="*54)
    app.run(debug=True, port=5000)
