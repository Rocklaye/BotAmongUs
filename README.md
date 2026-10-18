# BotAmongUs
### Discord Bot Privacy & Transparency Demonstration

**Academic Project — Personal Data Security**

BotAmongUs is an educational Discord bot designed to demonstrate privacy risks associated with automated data collection in online communities.

Inspired by the research paper *Bot Among Us* (PoPETs 2026), this project explores how Discord bots can access user information and how transparency mechanisms can improve awareness of data collection practices.

This project was developed collaboratively as part of a university course. This repository also includes my personal contributions to improving security, administrator authentication, configuration, and documentation.

## Project Objectives

- Demonstrate the privacy implications of Discord bot permissions and data collection.
- Compare silent data collection with transparent user notifications.
- Provide visibility into collected information through a web dashboard.
- Explore privacy awareness, informed consent, and responsible bot development.

## Key Features

### Discord Bot
- Collection of messages and associated metadata in an authorized test environment.
- Collection of server member information.
- Display of bot permissions and capabilities through `!permissions`.
- Two demonstration modes:
  - **Silent Mode:** data collection without automatic notifications.
  - **Perspective Mode:** data collection with transparency notifications.

Both modes collect data; the difference is how users are informed.

### Privacy Dashboard
- Web interface built with HTML, CSS, and JavaScript.
- Administrator authentication.
- Visualization of collected data and activity statistics.
- User and member information.
- Privacy reports.
- Switching between demonstration modes.

### Flask API
- Backend developed with Python and Flask.
- API endpoints for authentication, statistics, user information, and mode management.
- Integration with the SQLite database.

### SQLite Database
- Local storage of collected messages and metadata.
- Server member information.
- Persistent records used for dashboard analysis.

## Technologies

**Python · Pycord · Flask · SQLite · HTML · CSS · JavaScript · REST API · Git**

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Mahaelm25/BotAmongUs.git
cd BotAmongUs
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a Discord application and generate a bot token using the Discord Developer Portal.

Set the token as an environment variable. For Windows CMD:

```cmd
set "DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN"
```

Configure the Flask secret key and administrator password hash as required by `app.py`. Do not commit credentials or secrets to GitHub.

### 4. Start the Flask application

```bash
python app.py
```

### 5. Start the Discord bot

In a separate terminal:

```bash
python bot.py
```

### 6. Access the dashboard

Open:

`http://localhost:5000`

## Discord Commands

| Command | Description |
|---|---|
| `!permissions` | Displays permissions, intents, and data collection information |
| `!mode` | Switches between Silent and Perspective modes (administrator only) |
| `!stats` | Displays collected data statistics |
| `!rapport` | Provides the local dashboard address |
| `!help` | Lists available commands |

## Privacy & Security Considerations

- Intended for academic demonstration in controlled, authorized environments.
- Collected data is stored locally in SQLite and is not anonymized by default.
- The database may contain message content and personally identifiable metadata.
- The dashboard requires administrator authentication.
- Bot credentials are loaded from environment variables.
- Local databases and environment files are excluded through `.gitignore`.
- Demonstrations should use test data and participants informed about collection.

**This project is not intended for deployment on real communities without appropriate consent and privacy safeguards.**

## Academic Context

Developed as part of a personal data security course, this project examines the relationship between Discord bot capabilities, data collection, user awareness, and privacy protection.

**Research reference:** *Bot Among Us*, Proceedings on Privacy Enhancing Technologies (PoPETs), 2026.

## License

Academic demonstration project. No separate open-source license is specified.
