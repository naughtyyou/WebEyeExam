"""启动 GitHub 仓库体检服务。

直接执行 `python run.py` 即可：若当前 Python 缺少依赖，会自动改用项目 .venv。
"""
from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _chdir_root() -> None:
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def _venv_python() -> Path | None:
    if sys.platform == "win32":
        candidate = ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = ROOT / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def _ensure_runtime() -> None:
    """优先使用 .venv；系统 Python 缺包时自动切换。"""
    try:
        import uvicorn  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    vpy = _venv_python()
    if vpy is None:
        print("错误：未安装依赖，且未找到 .venv 虚拟环境。\n")
        print("请在 exam_new 目录执行：")
        print("  py -3.11 -m venv .venv")
        print("  .venv\\Scripts\\pip install -r requirements.txt")
        print("  python run.py")
        sys.exit(1)

    if Path(sys.executable).resolve() != vpy.resolve():
        print(f"当前 Python 缺少依赖，改用虚拟环境：{vpy}")
        os.execv(str(vpy), [str(vpy), str(ROOT / "run.py"), *sys.argv[1:]])

    print("虚拟环境中仍缺少依赖，请执行：")
    print("  .venv\\Scripts\\pip install -r requirements.txt")
    sys.exit(1)


def _find_free_port(start: int, attempts: int = 20) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start


def main() -> None:
    _chdir_root()
    _ensure_runtime()

    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    port = _find_free_port(settings.port)
    if port != settings.port:
        print(f"提示：端口 {settings.port} 已被占用，改用 {port}")

    url = f"http://127.0.0.1:{port}"
    print(f"服务启动中，请在浏览器打开：{url}")
    print("按 Ctrl+C 停止服务\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
