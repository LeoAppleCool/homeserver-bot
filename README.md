# 🖥️ HomeServer Bot

A Discord bot for monitoring your Linux homeserver in real time — system stats, Docker containers, threshold alerts, and slash commands. Built with [discord.py 2.x](https://discordpy.readthedocs.io/) and deployable as a Docker container.

---

## Features

### Live Dashboards (auto-update every 30 seconds)
- **System Stats** — CPU usage, RAM, disk, CPU temperature, load average, uptime, process count, logged-in users
- **Docker Status** — all containers with ✅/❌ running state, uptime, and restart count

### Alerts (no spam — fires once, resolves when back to normal)
| Trigger | Threshold |
|---|---|
| CPU usage | > 80 % |
| RAM usage | > 85 % |
| Disk usage | > 90 % |
| CPU temperature | > 75 °C |
| Container goes down | any container |
| Container restarts unexpectedly | restart count increases |

### Slash Commands
| Command | Description | Permission |
|---|---|---|
| `/status` | Full server stats embed on demand | Everyone |
| `/containers` | All Docker containers with status | Everyone |
| `/logs <container> [lines]` | Last N lines of container logs (max 200) | Everyone |
| `/restart <container>` | Restart a Docker container | Administrator |
| `/uptime` | System uptime and boot time | Everyone |

---

## Screenshots

> Dashboard and alert embeds use color-coded status: 🟢 green = healthy · 🟡 yellow = warning · 🔴 red = critical

---

## Requirements

- Docker + Docker Compose on the host
- A Discord bot token ([create one here](https://discord.com/developers/applications))
- Python 3.11+ (only needed if running without Docker)

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/LeoAppleCool/homeserver-bot.git
cd homeserver-bot
```

### 2. Configure environment
```bash
cp .env.example .env
nano .env
```

Fill in your values:
```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here
STATUS_CHANNEL_ID=channel_id_for_system_stats
DOCKER_CHANNEL_ID=channel_id_for_docker_status
ALERTS_CHANNEL_ID=channel_id_for_system_alerts
DOCKER_ALERTS_CHANNEL_ID=channel_id_for_docker_alerts
```

### 3. Deploy
```bash
docker-compose up -d --build
```

### 4. Check logs
```bash
docker-compose logs -f
```

---

## Project Structure

```
homeserver-bot/
├── bot.py                   # Entry point — loads cogs, syncs slash commands
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── data/                    # Persisted message IDs (auto-created)
├── cogs/
│   ├── dashboard.py         # 30s loop → edits system stats embed
│   ├── docker_monitor.py    # 30s loop → edits Docker status embed
│   ├── alerts.py            # 30s loop → threshold & container alerts
│   └── commands.py          # All slash commands
└── utils/
    ├── system_stats.py      # psutil helpers
    ├── docker_utils.py      # Docker SDK helpers
    └── storage.py           # JSON persistence for Discord message IDs
```

---

## How It Works

- The bot edits a **single persistent message** in each dashboard channel on every update cycle — no channel spam.
- Message IDs are stored in `data/message_ids.json` so they survive container restarts.
- Alert state is tracked in memory. Each alert fires **once** when the threshold is crossed and sends a **resolution message** when it drops back to normal.
- `network_mode: host` in the compose file ensures psutil reads actual **host** metrics, not the bot container's.
- `/var/run/docker.sock` is mounted so the bot can inspect and manage all containers on the host.

---

## Tech Stack

| Library | Purpose |
|---|---|
| [discord.py 2.x](https://github.com/Rapptz/discord.py) | Discord API + slash commands |
| [psutil](https://github.com/giampaolo/psutil) | System metrics |
| [docker SDK](https://docker-py.readthedocs.io/) | Container management |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable loading |

---

## License

MIT
