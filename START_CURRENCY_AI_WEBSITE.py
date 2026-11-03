import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


# ============================================================
# CẤU HÌNH ĐƯỜNG DẪN DỰ ÁN
# ============================================================
PROJECT_DIR = Path(r"D:\Urrency-AI-Recognition-Website")
BACKEND_DIR = PROJECT_DIR / "backend"
FRONTEND_DIR = PROJECT_DIR / "frontend"

BACKEND_PYTHON = BACKEND_DIR / ".venv312" / "Scripts" / "python.exe"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000

FRONTEND_HOST = "localhost"
FRONTEND_PORT = 5175

BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"


def port_is_open(host: str, port: int) -> bool:
    """Kiểm tra port đã có chương trình sử dụng hay chưa."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def open_terminal(command: str, working_dir: Path) -> None:
    """Mở một cửa sổ CMD riêng để chạy một thành phần của dự án."""
    subprocess.Popen(
        ["cmd.exe", "/k", command],
        cwd=str(working_dir),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def main() -> None:
    print("=" * 62)
    print("       CURRENCY AI RECOGNITION WEBSITE - START")
    print("=" * 62)

    # Kiểm tra thư mục và môi trường Python.
    if not PROJECT_DIR.is_dir():
        print(f"[ERROR] Không tìm thấy thư mục dự án:\n{PROJECT_DIR}")
        input("\nNhấn Enter để thoát...")
        return

    if not BACKEND_PYTHON.is_file():
        print("[ERROR] Không tìm thấy Python trong môi trường .venv312:")
        print(BACKEND_PYTHON)
        print("\nHãy kiểm tra lại môi trường backend.")
        input("\nNhấn Enter để thoát...")
        return

    if not (BACKEND_DIR / "app" / "main.py").is_file():
        print("[ERROR] Không tìm thấy backend/app/main.py")
        input("\nNhấn Enter để thoát...")
        return

    if not (FRONTEND_DIR / "package.json").is_file():
        print("[ERROR] Không tìm thấy frontend/package.json")
        input("\nNhấn Enter để thoát...")
        return

    # Nếu thiếu node_modules thì tự cài dependencies frontend.
    if not (FRONTEND_DIR / "node_modules").is_dir():
        print("\n[INFO] Chưa có node_modules. Đang chạy npm install...")
        try:
            subprocess.run(
                ["cmd.exe", "/c", "npm install"],
                cwd=str(FRONTEND_DIR),
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] npm install thất bại. Hãy kiểm tra Node.js và npm.")
            input("\nNhấn Enter để thoát...")
            return

    # Khởi chạy backend bằng đúng Python của .venv312.
    # Không cần Activate.ps1 vì gọi trực tiếp python.exe trong virtualenv.
    if port_is_open(BACKEND_HOST, BACKEND_PORT):
        print(f"[INFO] Backend đã có dịch vụ tại {BACKEND_URL}; không mở thêm.")
    else:
        backend_env = os.environ.copy()
        backend_env.update({
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "TF_NUM_INTRAOP_THREADS": "1",
            "TF_NUM_INTEROP_THREADS": "1",
        })

        backend_command = subprocess.list2cmdline([
            str(BACKEND_PYTHON),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            BACKEND_HOST,
            "--port",
            str(BACKEND_PORT),
        ])

        print("\n[INFO] Đang mở Backend...")
        subprocess.Popen(
            ["cmd.exe", "/k", backend_command],
            cwd=str(BACKEND_DIR),
            env=backend_env,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

    # Khởi chạy frontend.
    if port_is_open("127.0.0.1", FRONTEND_PORT):
        print(f"[INFO] Frontend đã có dịch vụ tại {FRONTEND_URL}; không mở thêm.")
    else:
        frontend_command = (
            f"npm run dev -- --host {FRONTEND_HOST} --port {FRONTEND_PORT}"
        )
        print("[INFO] Đang mở Frontend...")
        open_terminal(frontend_command, FRONTEND_DIR)

    print("\n" + "=" * 62)
    print("ĐÃ GỬI LỆNH KHỞI ĐỘNG CÁC DỊCH VỤ")
    print(f"Backend : {BACKEND_URL}/api/health")
    print(f"Frontend: {FRONTEND_URL}")
    print("=" * 62)
    print("\nHai cửa sổ CMD Backend và Frontend sẽ được mở riêng.")
    print("Giữ hai cửa sổ đó mở trong khi sử dụng website.")
    print("Đóng hai cửa sổ CMD để dừng các dịch vụ tương ứng.")

    # Chờ Vite có thời gian khởi động rồi mở trang web.
    time.sleep(4)
    webbrowser.open(FRONTEND_URL)

    input("\nNhấn Enter để đóng trình khởi động (không dừng Backend/Frontend)...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nĐã hủy thao tác khởi động.")
        input("Nhấn Enter để thoát...")