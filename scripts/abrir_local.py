"""Inicializador Windows: uma instalação, identidade do servidor e atualização local.

Ao abrir, traz a versão principal publicada no GitHub, mas só por avanço rápido e só
quando nada local pode ser perdido (D91). Sem rede, sem git ou com alteração local não
salva, abre a versão instalada e mostra o motivo. Uma mudança nos arquivos instalados
reinicia somente o servidor criado por este inicializador, identificado por PID,
criação e executável.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".euler-local"
PORT = 8501
URL = f"http://127.0.0.1:{PORT}"
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SERVER_PYTHON = Path(sys.executable).with_name("pythonw.exe")
if not SERVER_PYTHON.is_file():
    SERVER_PYTHON = Path(sys.executable)
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def fingerprint(root: Path = ROOT) -> str:
    """Assinatura do código, configuração e dados distribuídos, incluindo edições locais."""
    digest = hashlib.sha256()
    files = [root / "pyproject.toml", root / "requirements-lock.txt"]
    for folder in ("app", "euler", "templates", "demo", ".streamlit", "scripts"):
        files.extend(
            p
            for p in (root / folder).rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix.lower()
            in {".py", ".toml", ".csv", ".json", ".xlsx", ".svg", ".css", ".png", ".html", ".js"}
        )
    for path in sorted(set(files)):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def build_label() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            creationflags=HIDDEN,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "local"


def git(args: list[str], root: Path = ROOT, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=HIDDEN,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},  # nunca esperar senha no terminal
    )


def update_from_remote(root: Path = ROOT, remote: str = "origin") -> str:
    """Atualiza a instalação para a versão principal do GitHub, sem nunca descartar nada.

    Só avança (fast-forward) quando: é um repositório git; não há alteração não salva em
    arquivo versionado; e os commits locais já estão na versão principal. Se a pasta
    estiver numa branch antiga cujos commits já estão na principal, passa para a
    principal. Qualquer outra situação (sem rede, divergência, arquivos que seriam
    sobrescritos) mantém a versão instalada. Devolve uma frase para a barra lateral.
    """
    try:
        topo = git(["rev-parse", "--show-toplevel"], root)
        # Git procura também em diretórios ancestrais; só atualizamos a instalação pedida.
        if topo.returncode != 0 or Path(topo.stdout.strip()).resolve() != root.resolve():
            return "Versão instalada (pasta sem git: atualização automática indisponível)."
        if git(["status", "--porcelain", "--untracked-files=no"], root).stdout.strip():
            return (
                "Versão instalada: há alterações locais não salvas, então a atualização "
                "automática não foi aplicada."
            )
        ref = git(["ls-remote", "--symref", remote, "HEAD"], root)
        principal = next(
            (
                linha.split()[1].removeprefix("refs/heads/")
                for linha in ref.stdout.splitlines()
                if linha.startswith("ref:")
            ),
            None,
        )
        if ref.returncode != 0 or not principal:
            return "Versão instalada (sem conexão com o GitHub agora)."
        if git(["fetch", "--quiet", remote, principal], root).returncode != 0:
            return "Versão instalada (sem conexão com o GitHub agora)."
        alvo = f"{remote}/{principal}"
        antes = git(["rev-parse", "--short", "HEAD"], root).stdout.strip()
        atual = git(["rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip()
        if atual != principal:
            # só troca de branch quando todos os commits locais já estão na principal
            if git(["merge-base", "--is-ancestor", "HEAD", alvo], root).returncode != 0:
                return (
                    f"Versão instalada: a pasta está na branch {atual}, com commits que não "
                    "estão na versão principal; nada foi alterado."
                )
            existe = git(["rev-parse", "--verify", "--quiet", principal], root).returncode == 0
            if existe and git(["merge-base", "--is-ancestor", principal, alvo], root).returncode:
                return (
                    f"Versão instalada: a branch local {principal} tem commits próprios; "
                    "nada foi alterado."
                )
            troca = ["checkout", principal] if existe else ["checkout", "-b", principal, alvo]
            if git(troca, root).returncode != 0:
                return "Versão instalada: a troca para a versão principal não foi possível."
        if git(["merge", "--ff-only", "--quiet", alvo], root).returncode != 0:
            return (
                "Versão instalada: a versão local tem commits próprios que divergem da "
                "principal; nada foi alterado."
            )
        depois = git(["rev-parse", "--short", "HEAD"], root).stdout.strip()
        if depois == antes:
            return f"Versão principal em dia ({depois})."
        return f"Versão principal ({depois}), atualizada a partir de {antes}."
    except (OSError, subprocess.SubprocessError):
        return "Versão instalada (atualização automática indisponível neste computador)."


def process_identity(pid: int) -> dict | None:
    """Identidade Win32; horário de criação evita encerrar um PID reaproveitado."""
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        exit_code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) or exit_code.value != 259:
            return None
        times = [wintypes.FILETIME() for _ in range(4)]
        length = wintypes.DWORD(32768)
        name = ctypes.create_unicode_buffer(length.value)
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            return None
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(length)):
            return None
        return {
            "pid": pid,
            "created": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
            "executable": os.path.normcase(name.value),
        }
    finally:
        kernel.CloseHandle(handle)


def listener_pid(port: int = PORT) -> int | None:
    """PID do listener IPv4 local; health de outro servidor não confirma esta EULER."""
    from ctypes import wintypes

    class Row(ctypes.Structure):
        _fields_ = [
            (key, wintypes.DWORD)
            for key in ("state", "address", "port", "remote", "remote_port", "pid")
        ]

    api = ctypes.WinDLL("iphlpapi").GetExtendedTcpTable
    size = wintypes.DWORD()
    api(None, ctypes.byref(size), False, socket.AF_INET, 5, 0)
    buffer = ctypes.create_string_buffer(size.value)
    if api(buffer, ctypes.byref(size), False, socket.AF_INET, 5, 0) != 0:
        return None
    count = wintypes.DWORD.from_buffer(buffer).value
    rows = (Row * count).from_buffer(buffer, ctypes.sizeof(wintypes.DWORD))
    for row in rows:
        if row.state == 2 and socket.ntohs(row.port & 0xFFFF) == port:
            return int(row.pid)
    return None


def healthy() -> bool:
    try:
        with OPENER.open(URL + "/_stcore/health", timeout=2) as response:
            return response.status == 200 and response.read() == b"ok"
    except OSError:
        return False


def owned(record: dict) -> bool:
    identity = record.get("identity")
    return bool(
        identity
        and record.get("repository") == str(ROOT)
        and identity == process_identity(identity["pid"])
        and identity["executable"] == os.path.normcase(str(SERVER_PYTHON))
    )


def stop_owned(record: dict) -> None:
    """Encerra somente a identidade persistida deste inicializador."""
    from ctypes import wintypes

    if not owned(record):
        raise RuntimeError("O servidor mudou de identidade; nenhum outro processo foi encerrado.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x0001, False, record["identity"]["pid"])
    if not handle:
        raise RuntimeError("Não foi possível reiniciar o servidor local da EULER.")
    try:
        if not owned(record) or not kernel.TerminateProcess(handle, 0):
            raise RuntimeError("Não foi possível reiniciar o servidor local da EULER.")
    finally:
        kernel.CloseHandle(handle)
    for _ in range(50):
        if process_identity(record["identity"]["pid"]) is None:
            return
        time.sleep(0.1)
    raise RuntimeError("O servidor anterior ainda está encerrando. Abra a EULER novamente.")


@contextmanager
def startup_lock():
    import msvcrt

    STATE.mkdir(exist_ok=True)
    with (STATE / "startup.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        for attempt in range(180):
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if attempt == 179:
                    raise RuntimeError(
                        "A EULER ainda está iniciando. Tente abrir novamente."
                    ) from None
                time.sleep(0.5)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def serve() -> None:
    sys.path.insert(0, str(ROOT))
    auxiliary = ROOT.parent / "tmp/audit-python-deps"
    if auxiliary.exists():
        sys.path.append(str(auxiliary))
    os.chdir(ROOT)
    from streamlit.web import cli

    sys.argv = [
        "streamlit",
        "run",
        str(ROOT / "app/main.py"),
        "--global.developmentMode=false",
        "--server.address=127.0.0.1",
        f"--server.port={PORT}",
        "--server.headless=true",
        "--server.fileWatcherType=poll",
        "--server.runOnSave=true",
        "--browser.gatherUsageStats=false",
    ]
    raise SystemExit(cli.main())


def launch(open_browser: bool = True) -> dict:
    with startup_lock():
        situacao = update_from_remote()
        signature = fingerprint()
        state_file = STATE / "server.json"
        try:
            record = json.loads(state_file.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            record = {}
        if owned(record):
            if (
                record.get("fingerprint") == signature
                and listener_pid() == record["identity"]["pid"]
                and healthy()
            ):
                if open_browser:
                    webbrowser.open(URL + "/?atualizacao=" + signature[:12])
                return record
            stop_owned(record)
        if listener_pid() is not None:
            raise RuntimeError(
                "A porta da EULER está ocupada por outro servidor. "
                "Feche a janela antiga de inicialização antes de tentar novamente."
            )
        env = os.environ.copy()
        env["EULER_BUILD_ID"] = build_label() + " · " + signature[:8]
        env["EULER_BUILD_LABEL"] = situacao
        with (
            (STATE / "server.out.log").open("a") as out,
            (STATE / "server.err.log").open("a") as err,
        ):
            process = subprocess.Popen(
                [str(SERVER_PYTHON), str(Path(__file__).resolve()), "--serve"],
                cwd=ROOT,
                stdout=out,
                stderr=err,
                env=env,
                creationflags=HIDDEN | getattr(subprocess, "DETACHED_PROCESS", 0),
            )
        record = {
            "identity": process_identity(process.pid),
            "repository": str(ROOT),
            "fingerprint": signature,
            "build": env["EULER_BUILD_ID"],
            "url": URL,
        }
        if record["identity"] is None:
            raise RuntimeError("O servidor não iniciou. Consulte o registro de inicialização.")
        state_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        for _ in range(120):
            if process.poll() is not None:
                raise RuntimeError(
                    "A EULER encerrou ao iniciar. Consulte .euler-local/server.err.log."
                )
            if listener_pid() == process.pid and healthy():
                if open_browser:
                    webbrowser.open(URL + "/?atualizacao=" + signature[:12])
                return record
            time.sleep(0.5)
        raise RuntimeError("A EULER demorou para iniciar. Abra novamente em instantes.")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    try:
        launch(open_browser="--no-browser" not in sys.argv)
    except Exception as error:
        STATE.mkdir(exist_ok=True)
        (STATE / "erro-inicializacao.txt").write_text(str(error), encoding="utf-8")
        if Path(sys.executable).stem.lower() == "pythonw":
            ctypes.windll.user32.MessageBoxW(None, str(error), "EULER — inicialização", 0x10)
        else:
            print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
