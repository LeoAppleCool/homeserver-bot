"""System statistics via psutil."""

import os
import time
from datetime import datetime, timedelta

import psutil


def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=1)


def get_ram_stats() -> dict:
    mem = psutil.virtual_memory()
    return {
        "used_gb": mem.used / 1024**3,
        "total_gb": mem.total / 1024**3,
        "percent": mem.percent,
    }


def get_disk_stats(path: str = "/") -> dict:
    disk = psutil.disk_usage(path)
    return {
        "used_gb": disk.used / 1024**3,
        "total_gb": disk.total / 1024**3,
        "free_gb": disk.free / 1024**3,
        "percent": disk.percent,
    }


def get_cpu_temperature() -> float | None:
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        for key in ("coretemp", "cpu-thermal", "k10temp", "cpu_thermal", "acpitz"):
            if key in temps and temps[key]:
                return temps[key][0].current
        # Fallback: first available sensor
        for entries in temps.values():
            if entries:
                return entries[0].current
    except (AttributeError, OSError):
        pass
    return None


def get_system_load() -> tuple[float, float, float]:
    try:
        return os.getloadavg()
    except AttributeError:
        return (0.0, 0.0, 0.0)


def get_uptime() -> str:
    delta = timedelta(seconds=int(time.time() - psutil.boot_time()))
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def get_process_count() -> int:
    return len(psutil.pids())


def get_logged_users() -> list[str]:
    try:
        return [f"{u.name}@{u.terminal or 'console'}" for u in psutil.users()]
    except Exception:
        return []


def get_all_stats() -> dict:
    return {
        "cpu": get_cpu_usage(),
        "ram": get_ram_stats(),
        "disk": get_disk_stats(),
        "temperature": get_cpu_temperature(),
        "load": get_system_load(),
        "uptime": get_uptime(),
        "processes": get_process_count(),
        "users": get_logged_users(),
    }
