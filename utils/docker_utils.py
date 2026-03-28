"""Docker container management via the Docker SDK."""

import re
from datetime import datetime, timezone

import docker
import docker.errors


def _client() -> docker.DockerClient | None:
    try:
        return docker.from_env()
    except Exception:
        return None


def _parse_uptime(started_at: str) -> str:
    try:
        # Strip sub-second precision and normalise timezone
        clean = re.sub(r"\.\d+", "", started_at).replace("Z", "+00:00")
        start = datetime.fromisoformat(clean)
        delta = datetime.now(timezone.utc) - start
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if days:
            return f"{days}d {hours}h {minutes}m"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "N/A"


def get_containers() -> list[dict]:
    client = _client()
    if not client:
        return []
    try:
        result = []
        for container in client.containers.list(all=True):
            container.reload()
            attrs = container.attrs
            state = attrs.get("State", {})
            running = state.get("Running", False)
            uptime = _parse_uptime(state.get("StartedAt", "")) if running else state.get("Status", "stopped")
            tags = container.image.tags
            result.append(
                {
                    "name": container.name,
                    "short_id": container.short_id,
                    "status": state.get("Status", "unknown"),
                    "running": running,
                    "uptime": uptime,
                    "restart_count": attrs.get("RestartCount", 0),
                    "image": tags[0] if tags else container.image.short_id,
                }
            )
        return sorted(result, key=lambda c: c["name"])
    except Exception:
        return []
    finally:
        client.close()


def get_container_logs(name: str, lines: int = 50) -> str:
    client = _client()
    if not client:
        return "Could not connect to Docker daemon."
    try:
        container = client.containers.get(name)
        raw = container.logs(tail=lines, timestamps=True)
        return raw.decode("utf-8", errors="replace").strip() or "No logs available."
    except docker.errors.NotFound:
        return f"Container '{name}' not found."
    except Exception as exc:
        return f"Error fetching logs: {exc}"
    finally:
        client.close()


def restart_container(name: str) -> tuple[bool, str]:
    client = _client()
    if not client:
        return False, "Could not connect to Docker daemon."
    try:
        client.containers.get(name).restart()
        return True, f"Container **{name}** restarted successfully."
    except docker.errors.NotFound:
        return False, f"Container **{name}** not found."
    except Exception as exc:
        return False, f"Error restarting container: {exc}"
    finally:
        client.close()
