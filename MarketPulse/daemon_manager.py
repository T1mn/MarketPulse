import logging
import os
import signal
import sys
import time
from contextlib import contextmanager

import daemon
from daemon import pidfile
from lockfile.pidlockfile import PIDLockFile

from MarketPulse import config
from MarketPulse.logger_setup import setup_daemon_logging, setup_logging
from MarketPulse.main import run_service


def get_pid():
    """获取当前运行的守护进程PID（如果存在）"""
    try:
        with open(config.PID_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def is_running():
    """检查服务是否正在运行"""
    pid = get_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@contextmanager
def daemon_context():
    """创建守护进程上下文"""
    daemon_logger = setup_daemon_logging()
    pid_lock = PIDLockFile(str(config.PID_FILE))

    daemon_context = daemon.DaemonContext(
        pidfile=pid_lock,
        working_directory=str(config.BASE_DIR),
        umask=0o002,
        signal_map={
            signal.SIGTERM: "terminate",
            signal.SIGINT: "terminate",
        },
    )

    try:
        with daemon_context:
            daemon_logger.info("守护进程启动")
            setup_logging(to_console=False)  # 守护进程模式下不需要控制台输出
            yield
            daemon_logger.info("守护进程正常退出")
    except Exception as e:
        daemon_logger.error(f"守护进程发生错误: {e}")
        raise


def start():
    """启动服务"""
    if is_running():
        print("服务已经在运行中")
        sys.exit(1)

    print("正在启动服务...")
    with daemon_context():
        run_service()


def stop():
    """停止服务"""
    pid = get_pid()
    if not pid:
        print("服务未在运行")
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"已发送停止信号到进程 {pid}，等待进程退出...")
        # 等待最多10秒，直到进程停止
        for _ in range(10):
            if not is_running():
                print("服务已成功停止。")
                return True
            time.sleep(1)
        
        print("停止服务超时。请手动检查进程。")
        return False
    except ProcessLookupError:
        print("服务未在运行 (进程不存在)。")
        if os.path.exists(config.PID_FILE):
            os.remove(config.PID_FILE)
        return True # 进程已经不在了，也算成功
    except Exception as e:
        print(f"停止服务时发生错误: {e}")
        return False


def restart():
    """重启服务"""
    print("正在重启服务...")
    if stop():
        start()


def status():
    """检查服务状态"""
    if is_running():
        pid = get_pid()
        print(f"服务正在运行 (PID: {pid})")
    else:
        print("服务未在运行")


def main():
    """命令行入口"""
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop", "status", "restart"]:
        print("用法: python -m MarketPulse.daemon_manager [start|stop|status|restart]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        start()
    elif command == "stop":
        stop()
    elif command == "restart":
        restart()
    elif command == "status":
        status()


if __name__ == "__main__":
    main()
