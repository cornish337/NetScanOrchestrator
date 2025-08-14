from __future__ import annotations
import asyncio
import os
import shlex
import signal
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import contextlib

EventCb = Callable[[str, Dict], asyncio.Future | None]

def now_ms() -> int:
    return int(time.time() * 1000)

class NmapRunner:
    def __init__(self, state_dir: str = "/app/data", nmap_path: str = "nmap", event_cb: Optional[EventCb] = None):
        self.state_dir = Path(state_dir)
        self.scans_dir = self.state_dir / "scans"
        self.scans_dir.mkdir(parents=True, exist_ok=True)
        self.nmap_path = nmap_path
        self.event_cb = event_cb or (lambda *_args, **_kwargs: None)
        self._abort: Dict[str, asyncio.Event] = {}
        self._procs: Dict[str, List[asyncio.subprocess.Process]] = {}

    def _get_abort(self, chunk_id: str) -> asyncio.Event:
        ev = self._abort.get(chunk_id)
        if not ev:
            ev = asyncio.Event()
            self._abort[chunk_id] = ev
        return ev

    async def abort_chunk(self, chunk_id: str):
        # Signal abort and attempt to terminate any tracked procs
        ev = self._get_abort(chunk_id)
        ev.set()
        for proc in self._procs.get(chunk_id, []):
            if proc.returncode is None:
                try:
                    proc.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
        # Give them a moment, then SIGKILL any stragglers
        await asyncio.sleep(1.0)
        for proc in self._procs.get(chunk_id, []):
            if proc.returncode is None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass

    async def _emit(self, typ: str, **payload):
        coro = self.event_cb(typ, payload)
        if asyncio.iscoroutine(coro):
            await coro

    def _build_cmd(self, ip: str, settings: Dict) -> List[str]:
        host_timeout = int(settings.get("host_timeout_sec", 60))
        profile = settings.get("profile", "balanced")
        scan_type = settings.get("scan_type", "sT")  # sS needs NET_RAW caps; sT is safe
        ports = settings.get("ports", "top-1000")
        extra_args = settings.get("extra_args", "").strip()

        cmd = [self.nmap_path, "-Pn", "-n", f"-{scan_type}", "--host-timeout", f"{host_timeout}s", "-oX", "-"]
        # timing presets
        if profile == "fast":
            cmd += ["-T4", "--max-retries", "1"]
        elif profile == "thorough":
            cmd += ["-T3", "--max-retries", "2"]
        else:
            cmd += ["-T4", "--max-retries", "1"]

        # ports handling
        if isinstance(ports, str) and ports.startswith("top-"):
            topn = ports.split("-", 1)[1]
            if topn.isdigit():
                cmd += ["--top-ports", topn]
        elif ports:
            cmd += ["-p", str(ports)]

        # any extra args
        if extra_args:
            cmd += shlex.split(extra_args)

        cmd += [ip]
        return cmd

    def build_cmd(self, ip: str, settings: Dict) -> List[str]:
        """Public helper to build the nmap command for an IP."""
        return self._build_cmd(ip, settings)

    async def run_command(self, ip: str, settings: Dict) -> Tuple[List[str], int, str, str]:
        """
        Build and execute an nmap command immediately for the given IP.
        Returns the command list, return code, stdout and stderr (decoded).
        """
        cmd = self._build_cmd(ip, settings)
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return cmd, proc.returncode, stdout.decode(), stderr.decode()

    async def _scan_ip(self, chunk_id: str, ip: str, settings: Dict, abort_event: asyncio.Event) -> Tuple[str, bool, int]:
        started = time.time()
        cmd = self._build_cmd(ip, settings)
        out_dir = self.scans_dir / chunk_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_xml = out_dir / f"{ip}.xml"

        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self._procs.setdefault(chunk_id, []).append(proc)

        try:
            # Outer watchdog in case host_timeout is ignored
            host_timeout = int(settings.get("host_timeout_sec", 60))
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=host_timeout + 15)
            except asyncio.TimeoutError:
                # External kill if nmap didn't respect host-timeout
                with contextlib.suppress(ProcessLookupError):
                    proc.send_signal(signal.SIGTERM)
                try:
                    await asyncio.wait_for(proc.wait(), timeout=3)
                except asyncio.TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        proc.kill()
                stdout = stdout if 'stdout' in locals() else b""
                stderr = b"timeout"

            # Write XML (may be empty on failure)
            try:
                out_xml.write_bytes(stdout or b"")
            except Exception:
                pass

            ok = (proc.returncode == 0) and bool(stdout)
            await self._emit("host_completed", chunk_id=chunk_id, ip=ip, ok=ok, duration_ms=int((time.time() - started) * 1000))
            return ip, ok, int((time.time() - started) * 1000)

        finally:
            # Check abort
            if abort_event.is_set() and proc.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()

    async def scan_chunk(self, chunk_id: str, targets: List[str], settings: Dict):
        abort_event = self._get_abort(chunk_id)
        per_host_workers = int(settings.get("per_host_workers", 8))
        sem = asyncio.Semaphore(per_host_workers)

        completed = 0
        total = len(targets)
        failed_hosts: List[str] = []

        async def worker(ip: str):
            nonlocal completed
            async with sem:
                if abort_event.is_set():
                    return
                _, ok, _ = await self._scan_ip(chunk_id, ip, settings, abort_event)
                completed += 1
                if not ok:
                    failed_hosts.append(ip)
                await self._emit(
                    "chunk_progress",
                    chunk_id=chunk_id,
                    completed_hosts=completed,
                    total_hosts=total,
                    elapsed_ms=0,
                    last_heartbeat_ms=0,
                )

        await asyncio.gather(*[worker(ip) for ip in targets if not abort_event.is_set()])
        # Cleanup tracking
        self._procs.pop(chunk_id, None)
        # Completion event is emitted by caller after status update
        return {"completed": completed, "failed": failed_hosts}
