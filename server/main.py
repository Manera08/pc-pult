import os, sys, ctypes, logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def check_admin():
    if not is_admin():
        logger.warning("=" * 60)
        logger.warning("ПРОГРАММА НЕ ЗАПУЩЕНА С ПРАВАМИ АДМИНИСТРАТОРА!")
        logger.warning("Глобальный захват клавиш (keyboard) может не работать.")
        logger.warning("Рекомендуется перезапустить приложение от имени Администратора.")
        logger.warning("=" * 60)
        return False
    logger.info("Права администратора: OK")
    return True


def try_elevate():
    if is_admin():
        return True
    try:
        script = os.path.abspath(__file__)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, script, None, 1
        )
        sys.exit(0)
    except Exception as e:
        logger.warning(f"Не удалось запросить повышение прав: {e}")
        return False


def main():
    logger.info("ПК-Пульт Сервер v1.0.0")
    logger.info("=" * 40)

    check_admin()

    logger.info("Запуск API-сервера...")
    from api_server import run_api
    api_thread = run_api()
    logger.info("API-сервер запущен на порту 8789")

    logger.info("Настройка ADB...")
    from adb_helper import setup_adb
    setup_adb()

    logger.info("Запуск GUI-редактора...")
    from gui_editor import run_gui
    run_gui()


if __name__ == "__main__":
    main()
