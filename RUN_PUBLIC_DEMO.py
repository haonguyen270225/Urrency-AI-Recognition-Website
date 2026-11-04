
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from queue import Empty, Queue
import threading


# ============================================================
# CẤU HÌNH DỰ ÁN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VITE_CONFIG = FRONTEND_DIR / "vite.config.js"

DOCKER_IMAGE = "currency-ai-backend:1.0"
CONTAINER_NAME = "currency-ai-backend"

BACKEND_PORT = 8000
PREVIEW_PORT = 5175

BACKEND_HEALTH_URL = (
    f"http://127.0.0.1:{BACKEND_PORT}/api/health"
)

PREVIEW_HEALTH_URL = (
    f"http://127.0.0.1:{PREVIEW_PORT}/api/health"
)

DOCKER_DESKTOP_PATHS = [
    Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"),
    Path(r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe"),
]

CLOUDFLARED_PATHS = [
    Path(r"C:\Program Files (x86)\cloudflared\cloudflared.exe"),
    Path(r"C:\Program Files\cloudflared\cloudflared.exe"),
]

DOCKER_START_TIMEOUT = 180
API_START_TIMEOUT = 120
PREVIEW_START_TIMEOUT = 60
CLOUDFLARE_START_TIMEOUT = 90
PUBLIC_CHECK_TIMEOUT = 180


# ============================================================
# HIỂN THỊ
# ============================================================

def print_line(char="=", length=72):
    print(char * length)


def info(message):
    print(f"[INFO] {message}", flush=True)


def success(message):
    print(f"[OK]   {message}", flush=True)


def warning(message):
    print(f"[WARN] {message}", flush=True)


def error(message):
    print(f"[ERROR] {message}", flush=True)


def step(number, message):
    print()
    print_line()
    print(f" BƯỚC {number}: {message}")
    print_line()


# ============================================================
# CHẠY LỆNH
# ============================================================

def run_command(command, cwd=None, check=True):
    """
    Chạy lệnh hệ thống.
    Hỗ trợ cả npm.cmd trên Windows.
    """

    command = [str(item) for item in command]

    if (
        os.name == "nt"
        and command[0].lower().endswith((".cmd", ".bat"))
    ):
        return subprocess.run(
            subprocess.list2cmdline(command),
            cwd=str(cwd) if cwd else None,
            shell=True,
            check=check,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


# ============================================================
# TÌM CHƯƠNG TRÌNH
# ============================================================

def find_executable(command_name, fallback_paths):
    found = shutil.which(command_name)

    if found:
        return found

    for path in fallback_paths:
        if path.is_file():
            return str(path)

    return None


def find_docker():
    return find_executable("docker", [])


def find_node():
    return find_executable("node", [])


def find_npm():
    return (
        shutil.which("npm.cmd")
        or shutil.which("npm")
    )


def find_cloudflared():
    return find_executable(
        "cloudflared",
        CLOUDFLARED_PATHS,
    )


# ============================================================
# KIỂM TRA CỔNG
# ============================================================

def port_is_in_use(port):
    """
    Kiểm tra cổng TCP có đang được sử dụng không.
    """

    try:
        with socket.create_connection(
            ("127.0.0.1", port),
            timeout=1,
        ):
            return True

    except OSError:
        return False


# ============================================================
# DOCKER
# ============================================================

def docker_is_ready(docker_exe):
    result = subprocess.run(
        [docker_exe, "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    return result.returncode == 0


def start_docker_desktop():
    for path in DOCKER_DESKTOP_PATHS:
        if path.is_file():
            info("Đang mở Docker Desktop...")

            subprocess.Popen(
                [str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP",
                    0,
                ),
            )

            return True

    return False


def wait_for_docker(docker_exe):
    if docker_is_ready(docker_exe):
        success("Docker Engine đang hoạt động.")
        return

    warning("Docker Engine chưa sẵn sàng.")

    if not start_docker_desktop():
        raise RuntimeError(
            "Không tìm thấy Docker Desktop."
        )

    info(
        f"Đang chờ Docker Engine "
        f"(tối đa {DOCKER_START_TIMEOUT} giây)..."
    )

    started = time.time()

    while time.time() - started < DOCKER_START_TIMEOUT:

        if docker_is_ready(docker_exe):
            success("Docker Engine đã sẵn sàng.")
            return

        time.sleep(3)

    raise TimeoutError(
        "Docker Engine khởi động quá lâu. "
        "Hãy kiểm tra Docker Desktop."
    )


def ensure_backend_container(docker_exe):
    """
    Khởi động container hiện có hoặc tạo container mới.
    Không xóa dữ liệu Docker.
    """

    inspect = subprocess.run(
        [
            docker_exe,
            "inspect",
            "-f",
            "{{.State.Running}}",
            CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if inspect.returncode == 0:

        state = inspect.stdout.strip().lower()

        if state == "true":
            success(
                f"Container {CONTAINER_NAME} đang chạy."
            )
            return

        info(
            f"Đang khởi động container {CONTAINER_NAME}..."
        )

        run_command([
            docker_exe,
            "start",
            CONTAINER_NAME,
        ])

        success("Đã khởi động Backend container.")
        return

    image_check = subprocess.run(
        [
            docker_exe,
            "image",
            "inspect",
            DOCKER_IMAGE,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if image_check.returncode != 0:
        raise RuntimeError(
            f"Không tìm thấy Docker image '{DOCKER_IMAGE}'. "
            "Hãy build Backend image trước."
        )

    info("Đang tạo Backend container...")

    run_command([
        docker_exe,
        "run",
        "-d",
        "--name",
        CONTAINER_NAME,
        "--restart",
        "unless-stopped",
        "-p",
        f"{BACKEND_PORT}:8000",
        DOCKER_IMAGE,
    ])

    success("Đã tạo và khởi động Backend container.")

def stop_backend_container(docker_exe):
    """
    Dừng Backend container khi kết thúc Public Demo.
    Không xóa container, image hoặc dữ liệu.
    """

    if not docker_exe:
        return

    info(f"Đang kiểm tra container {CONTAINER_NAME}...")

    inspect = subprocess.run(
        [
            docker_exe,
            "inspect",
            "-f",
            "{{.State.Running}}",
            CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if inspect.returncode != 0:
        warning("Không tìm thấy Backend container.")
        return

    if inspect.stdout.strip().lower() != "true":
        success("Docker Backend đã dừng từ trước.")
        return

    info("Đang dừng Docker Backend...")

    result = subprocess.run(
        [
            docker_exe,
            "stop",
            "--time",
            "10",
            CONTAINER_NAME,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode == 0:
        success("Đã dừng Docker Backend thành công.")
    else:
        warning(
            f"Không thể dừng Docker Backend: {result.stderr.strip()}"
        )
# ============================================================
# HTTP / API
# ============================================================

def http_get(url, timeout=10):
    """
    Trả về HTTP status và response body.
    Kể cả HTTP 403, 502, 530 cũng đọc được nội dung lỗi.
    """

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Currency-AI-Public-Demo-Launcher"
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            body = response.read().decode(
                "utf-8",
                errors="replace",
            )

            return response.status, body

    except urllib.error.HTTPError as exc:

        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        return exc.code, body


def api_is_healthy(body):
    try:
        data = json.loads(body)

        return (
            data.get("success") is True
            or str(data.get("status", "")).lower() == "online"
            or str(data.get("status", "")).lower() == "healthy"
        )

    except Exception:
        normalized = body.replace(" ", "").lower()

        return (
            '"success":true' in normalized
            or '"status":"online"' in normalized
            or "healthy" in body.lower()
        )


def wait_for_api(url, timeout_seconds, label):
    info(f"Đang kiểm tra {label}...")

    started = time.time()
    last_error = None

    while time.time() - started < timeout_seconds:

        try:
            status, body = http_get(url, timeout=5)

            if status == 200 and api_is_healthy(body):
                success(f"{label} hoạt động bình thường.")
                return

            last_error = (
                f"HTTP {status}: {body[:250]}"
            )

        except Exception as exc:
            last_error = str(exc)

        time.sleep(2)

    raise TimeoutError(
        f"{label} không phản hồi. "
        f"Chi tiết: {last_error}"
    )


# ============================================================
# BUILD FRONTEND
# ============================================================

def build_frontend():
    if not FRONTEND_DIR.is_dir():
        raise FileNotFoundError(
            f"Không tìm thấy Frontend: {FRONTEND_DIR}"
        )

    npm = find_npm()

    if not npm:
        raise RuntimeError(
            "Không tìm thấy npm. "
            "Hãy cài Node.js và mở lại Terminal."
        )

    info("Đang build Frontend production...")

    run_command(
        [npm, "run", "build"],
        cwd=FRONTEND_DIR,
    )

    success("Build Frontend hoàn tất.")


# ============================================================
# VITE CONFIG
# ============================================================

def update_vite_allowed_host(hostname):
    """
    Chỉ thay đổi allowedHosts bên trong preview.
    Giữ nguyên nội dung gốc để khôi phục khi kết thúc.
    """

    if not VITE_CONFIG.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy {VITE_CONFIG}"
        )

    if not re.fullmatch(
        r"[a-zA-Z0-9-]+\.trycloudflare\.com",
        hostname,
    ):
        raise ValueError(
            f"Hostname Cloudflare không hợp lệ: {hostname}"
        )

    original = VITE_CONFIG.read_text(
        encoding="utf-8"
    )

    pattern = re.compile(
        r"(\bpreview\s*:\s*\{[\s\S]*?"
        r"\ballowedHosts\s*:\s*)"
        r"\[[^\]]*\]",
        re.MULTILINE,
    )

    updated, count = pattern.subn(
        lambda match: (
            match.group(1)
            + json.dumps([hostname])
        ),
        original,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "Không tìm thấy preview.allowedHosts "
            "trong vite.config.js. "
            "Hãy kiểm tra cấu hình Vite."
        )

    VITE_CONFIG.write_text(
        updated,
        encoding="utf-8",
    )

    # Kiểm tra nội dung sau khi cập nhật.
    saved = VITE_CONFIG.read_text(
        encoding="utf-8"
    )

    if hostname not in saved:
        VITE_CONFIG.write_text(
            original,
            encoding="utf-8",
        )

        raise RuntimeError(
            "Không thể xác nhận hostname trong vite.config.js."
        )

    success(
        f"Đã cập nhật preview.allowedHosts: {hostname}"
    )

    return original


def restore_vite_config(original):
    if original is None:
        return

    try:
        VITE_CONFIG.write_text(
            original,
            encoding="utf-8",
        )

        success(
            "Đã khôi phục vite.config.js ban đầu."
        )

    except Exception as exc:
        warning(
            f"Không thể khôi phục vite.config.js: {exc}"
        )


# ============================================================
# VITE PREVIEW
# ============================================================

def start_vite_preview():
    node = find_node()

    if not node:
        raise RuntimeError(
            "Không tìm thấy Node.js."
        )

    vite_cli = (
        FRONTEND_DIR
        / "node_modules"
        / "vite"
        / "bin"
        / "vite.js"
    )

    if not vite_cli.is_file():
        raise FileNotFoundError(
            f"Không tìm thấy Vite CLI: {vite_cli}"
        )

    info("Đang khởi động Vite Preview...")

    process = subprocess.Popen(
        [
            node,
            str(vite_cli),
            "preview",
            "--host",
            "127.0.0.1",
            "--port",
            str(PREVIEW_PORT),
            "--strictPort",
        ],
        cwd=str(FRONTEND_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        ),
    )

    return process


def preview_is_healthy():
    try:
        status, body = http_get(
            PREVIEW_HEALTH_URL,
            timeout=5,
        )

        return (
            status == 200
            and api_is_healthy(body)
        )

    except Exception:
        return False


# ============================================================
# CLOUDFLARE QUICK TUNNEL
# ============================================================

def read_process_output(process, output_queue):
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break

            output_queue.put(line.rstrip())

    finally:
        try:
            process.stdout.close()
        except Exception:
            pass


def stop_process(process, label):
    if process is None:
        return

    if process.poll() is not None:
        return

    info(f"Đang dừng {label}...")

    try:
        process.terminate()
        process.wait(timeout=8)

    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)

    except Exception as exc:
        warning(
            f"Không thể dừng {label}: {exc}"
        )


def start_cloudflare_tunnel(cloudflared_exe):
    info("Đang tạo Cloudflare Quick Tunnel...")

    process = subprocess.Popen(
        [
            cloudflared_exe,
            "tunnel",
            "--no-autoupdate",
            "--url",
            f"http://127.0.0.1:{PREVIEW_PORT}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    output_queue = Queue()

    reader = threading.Thread(
        target=read_process_output,
        args=(process, output_queue),
        daemon=True,
    )

    reader.start()

    url_pattern = re.compile(
        r"https://[a-zA-Z0-9-]+\.trycloudflare\.com"
    )

    started = time.time()

    try:
        while (
            time.time() - started
            < CLOUDFLARE_START_TIMEOUT
        ):

            if process.poll() is not None:
                raise RuntimeError(
                    "Cloudflare Tunnel đã dừng trước khi tạo URL."
                )

            try:
                line = output_queue.get(timeout=0.5)

                print(
                    f"[CLOUDFLARE] {line}",
                    flush=True,
                )

                match = url_pattern.search(line)

                if match:
                    public_url = match.group(0)

                    success(
                        f"Đã nhận URL: {public_url}"
                    )

                    return process, public_url

            except Empty:
                pass

        raise TimeoutError(
            "Không nhận được URL trycloudflare.com."
        )

    except Exception:
        stop_process(
            process,
            "Cloudflare Tunnel",
        )
        raise


# ============================================================
# KIỂM TRA WEBSITE CÔNG KHAI
# ============================================================

def wait_for_public_site(public_url, timeout_seconds):
    """
    Kiểm tra:
    1. DNS hostname.
    2. Website công khai.
    3. Backend API qua Cloudflare.
    """

    hostname = public_url.replace(
        "https://",
        "",
    ).strip("/")

    info(
        "Đang kiểm tra DNS và website từ Internet..."
    )

    started = time.time()
    last_error = None
    dns_ready = False

    while time.time() - started < timeout_seconds:

        try:
            # Kiểm tra DNS.
            if not dns_ready:
                socket.getaddrinfo(
                    hostname,
                    443,
                    type=socket.SOCK_STREAM,
                )

                dns_ready = True

                success(
                    "DNS hostname Cloudflare đã hoạt động."
                )

            # Kiểm tra website.
            status, body = http_get(
                public_url + "/",
                timeout=10,
            )

            if status != 200:
                last_error = (
                    f"Website trả về HTTP {status}: "
                    f"{body[:300]}"
                )

                if (
                    status == 403
                    and "not allowed" in body.lower()
                ):
                    raise RuntimeError(
                        "Vite đang chặn hostname Cloudflare. "
                        "Kiểm tra preview.allowedHosts."
                    )

                time.sleep(3)
                continue

            # Kiểm tra Backend qua Tunnel.
            api_status, api_body = http_get(
                public_url + "/api/health",
                timeout=10,
            )

            if (
                api_status == 200
                and api_is_healthy(api_body)
            ):
                success(
                    "Website công khai trả về HTTP 200."
                )

                success(
                    "Backend API công khai hoạt động."
                )

                return

            last_error = (
                f"API công khai trả về HTTP {api_status}: "
                f"{api_body[:300]}"
            )

        except RuntimeError:
            raise

        except Exception as exc:
            last_error = str(exc)

        time.sleep(3)

    raise TimeoutError(
        "Không thể xác nhận website công khai. "
        f"Chi tiết cuối cùng: {last_error}"
    )


# ============================================================
# GIÁM SÁT
# ============================================================

def monitor_services(
    cloudflare_process,
    preview_process,
):
    info("Đang giám sát các dịch vụ...")

    while True:

        if cloudflare_process.poll() is not None:
            raise RuntimeError(
                "Cloudflare Tunnel đã bị dừng."
            )

        if preview_process.poll() is not None:
            raise RuntimeError(
                "Tiến trình Vite Preview đã kết thúc."
            )

        if not preview_is_healthy():
            raise RuntimeError(
                "Vite Preview hoặc Backend proxy không còn phản hồi."
            )

        time.sleep(5)


# ============================================================
# CHƯƠNG TRÌNH CHÍNH
# ============================================================

def main():
    cloudflare_process = None
    preview_process = None
    original_vite_config = None
    docker_exe = None

    print()
    print_line()
    print("       CURRENCY AI RECOGNITION - PUBLIC DEMO")
    print_line()

    print(f"Project: {PROJECT_ROOT}")
    print("Mode: PUBLIC DEMO")

    try:
        if os.name != "nt":
            raise OSError(
                "Launcher này được thiết kế cho Windows."
            )

        if not FRONTEND_DIR.is_dir():
            raise FileNotFoundError(
                "Không tìm thấy thư mục frontend."
            )

        # 1. Kiểm tra môi trường.
        step(1, "KIỂM TRA MÔI TRƯỜNG")

        if port_is_in_use(PREVIEW_PORT):
            raise RuntimeError(
                f"Cổng {PREVIEW_PORT} đang được sử dụng. "
                "Hãy đóng Vite Preview cũ trước khi chạy launcher."
            )

        # 2. Docker.
        step(2, "KIỂM TRA VÀ KHỞI ĐỘNG DOCKER")

        docker_exe = find_docker()

        if not docker_exe:
            raise RuntimeError(
                "Không tìm thấy Docker CLI."
            )

        wait_for_docker(docker_exe)
        ensure_backend_container(docker_exe)

        # 3. Backend API.
        step(3, "KIỂM TRA BACKEND API")

        wait_for_api(
            BACKEND_HEALTH_URL,
            API_START_TIMEOUT,
            "Backend API",
        )

        # 4. Build Frontend.
        step(4, "BUILD FRONTEND")

        build_frontend()

        # 5. Kiểm tra Cloudflare.
        step(5, "KIỂM TRA CLOUDFLARED")

        cloudflared_exe = find_cloudflared()

        if not cloudflared_exe:
            raise RuntimeError(
                "Không tìm thấy cloudflared.exe."
            )

        # 6. Tạo Quick Tunnel.
        step(6, "TẠO CLOUDFLARE QUICK TUNNEL")

        cloudflare_process, public_url = (
            start_cloudflare_tunnel(cloudflared_exe)
        )

        hostname = public_url.replace(
            "https://", ""
        ).strip("/")

        # 7. Cập nhật Vite.
        step(7, "CẬP NHẬT VITE ALLOWED HOSTS")

        original_vite_config = (
            update_vite_allowed_host(hostname)
        )

        # 8. Khởi động Preview.
        step(8, "KHỞI ĐỘNG VITE PREVIEW")

        preview_process = start_vite_preview()

        wait_for_api(
            PREVIEW_HEALTH_URL,
            PREVIEW_START_TIMEOUT,
            "Vite Preview / Backend proxy",
        )

        # 9. Kiểm tra website công khai.
        step(9, "KIỂM TRA WEBSITE CÔNG KHAI")

        wait_for_public_site(
            public_url,
            PUBLIC_CHECK_TIMEOUT,
        )

        # 10. Mở trình duyệt.
        step(10, "MỞ WEBSITE DEMO")

        webbrowser.open(public_url, new=2)

        print()
        print_line()

        print("             DEMO ĐÃ SẴN SÀNG!")

        print_line()

        print(f"  PUBLIC URL : {public_url}")
        print(f"  PREVIEW    : http://127.0.0.1:{PREVIEW_PORT}/")
        print(f"  BACKEND    : {BACKEND_HEALTH_URL}")

        print_line()

        print("  Website đã được kiểm tra qua Cloudflare.")
        print("  Giữ cửa sổ launcher mở trong suốt phiên demo.")
        print("  Nhấn Ctrl + C để kết thúc phiên.")
        print("  Cloudflare, Preview và Docker Backend sẽ được dừng.")
        print("  Docker Desktop vẫn được giữ mở.")

        print_line()

        # 11. Giám sát.
        monitor_services(
            cloudflare_process,
            preview_process,
        )

    except KeyboardInterrupt:
        print()
        warning(
            "Nhận Ctrl + C. Đang kết thúc phiên demo..."
        )

    except Exception as exc:
        print()
        error(str(exc))

        print()
        warning(
            "Không thể hoàn tất phiên Public Demo."
        )

        try:
            input(
                "Nhấn Enter để đóng chương trình..."
            )
        except EOFError:
            pass

    finally:
        print()

        # 1. Dừng Vite Preview.
        stop_process(
            preview_process,
            "Vite Preview",
        )

        # 2. Dừng Cloudflare Tunnel.
        stop_process(
            cloudflare_process,
            "Cloudflare Tunnel",
        )

        # 3. Khôi phục Vite config.
        restore_vite_config(
            original_vite_config
        )

        # 4. Dừng Docker Backend.
        stop_backend_container(docker_exe)

        print()
        print_line()

        print("          ĐÃ KẾT THÚC PUBLIC DEMO")
        print("          Cloudflare Tunnel: ĐÃ DỪNG")
        print("          Vite Preview: ĐÃ DỪNG")
        print("          Docker Backend: ĐÃ DỪNG")
        print("          Docker Desktop: VẪN MỞ")

        print_line()


if __name__ == "__main__":
    try:
        main()

    except Exception as fatal_error:
        print(f"\nLỖI KHỞI CHẠY: {fatal_error}")

        try:
            input("Nhấn Enter để đóng chương trình...")
        except EOFError:
            pass
