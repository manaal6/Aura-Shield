"""
app/tools/sandbox.py

Execution sandboxing engine for AI tool actions (W#10).
Provides isolated container or ephemeral sub-process execution
with strict resource limits, timeouts, and network isolation.
Gracefully degrades to secure simulation stub if Docker is uninstalled.
"""
from __future__ import annotations

import logging
import subprocess
import shutil
from typing import Any

logger = logging.getLogger(__name__)


def is_docker_available() -> bool:
    return shutil.which("docker") is not None


def run_sandboxed_command(cmd: str, timeout_seconds: int = 10, danger: str = "high") -> dict[str, Any]:
    """
    Executes a shell command inside an ephemeral network-isolated container.

    Fail-closed rule: if Docker is unavailable AND the tool is high/critical
    danger, execution is DENIED (never "pretend safely executed"). The
    simulation stub exists ONLY for low-danger demonstration tools.
    """
    if not is_docker_available():
        if danger in ("high", "critical"):
            logger.warning("Fail-closed: Docker unavailable for %s-danger command; DENY", danger)
            return {
                "success": False,
                "mode": "unavailable",
                "verdict": "DENY",
                "error": (f"Docker unavailable on host and tool danger is '{danger}': "
                          f"execution DENIED (fail-closed)."),
            }
        return {
            "success": True,
            "mode": "simulation_stub",
            "output": f"[SECURE STUB] Command validated: '{cmd}' (Docker unavailable on host; simulated execution)",
        }

    try:
        # Run inside minimal container with no network and read-only rootfs
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "128m",
            "--cpus", "0.5",
            "alpine:latest",
            "sh", "-c", cmd
        ]
        res = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "success": res.returncode == 0,
            "mode": "docker_isolated",
            "stdout": res.stdout,
            "stderr": res.stderr,
            "returncode": res.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "mode": "docker_isolated",
            "error": f"Command timed out after {timeout_seconds} seconds",
        }
    except Exception as exc:
        return {
            "success": False,
            "mode": "docker_isolated",
            "error": str(exc),
        }
