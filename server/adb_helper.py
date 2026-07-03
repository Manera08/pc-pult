import os, subprocess, shlex, logging

logger = logging.getLogger("adb_helper")

ADB_PORTS = [8789]
LOCAL_PORT = 8789


def find_adb():
    candidates = []

    try:
        androind_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if androind_home:
            candidates.append(os.path.join(androind_home, "platform-tools", "adb.exe"))
            candidates.append(os.path.join(androind_home, "platform-tools", "adb"))
    except KeyError:
        pass

    try:
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        candidates.append(os.path.join(local_appdata, "Android", "Sdk", "platform-tools", "adb.exe"))
    except KeyError:
        pass

    candidates.append("adb.exe")
    candidates.append("adb")

    for exe in candidates:
        try:
            subprocess.run(
                [exe, "version"],
                capture_output=True,
                timeout=3,
                check=True,
            )
            return exe
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue

    for exe in candidates:
        try:
            result = subprocess.run(
                ["where", "adb"] if os.name == "nt" else ["which", "adb"],
                capture_output=True,
                timeout=3,
            )
            if result.returncode == 0:
                path = result.stdout.decode().strip().split("\n")[0].strip()
                if path:
                    return path
        except (subprocess.SubprocessError, FileNotFoundError):
            continue

    return None


def adb_forward(adb_path, local_port=LOCAL_PORT, device_port=LOCAL_PORT):
    try:
        result = subprocess.run(
            [adb_path, "forward", f"tcp:{local_port}", f"tcp:{device_port}"],
            capture_output=True,
            timeout=5,
            text=True,
        )
        if result.returncode == 0:
            logger.info(f"ADB forward: tcp:{local_port} -> tcp:{device_port}")
            return True
        else:
            logger.warning(f"ADB forward failed: {result.stderr.strip()}")
            return False
    except subprocess.SubprocessError as e:
        logger.warning(f"ADB forward error: {e}")
        return False


def adb_forward_list(adb_path, local_port=LOCAL_PORT, device_port=LOCAL_PORT):
    return adb_forward(adb_path, local_port, device_port)


def setup_adb():
    adb = find_adb()
    if adb is None:
        logger.warning("ADB не найден. USB-подключение недоступно.")
        return False

    logger.info(f"ADB найден: {adb}")

    success = adb_forward(adb)
    if success:
        logger.info("ADB port forwarding настроен.")
    else:
        logger.warning("Не удалось настроить ADB forward.")

    return success
