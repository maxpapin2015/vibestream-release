import sys
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from vibestream.ui.main_window import VibeStreamWindow


def _global_exception_handler(exc_type, exc_value, exc_tb):
    err_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        log_path = Path.home() / ".vibestream" / "crash_log.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(err_text, encoding="utf-8")
    except Exception:
        pass
    print(err_text, file=sys.stderr)
    if QApplication.instance():
        QMessageBox.critical(None, "Ошибка VibeStream", f"Произошла ошибка:\n\n{exc_value}\n\nПодробности в ~/.vibestream/crash_log.txt")


def main():
    sys.excepthook = _global_exception_handler
    app = QApplication(sys.argv)
    app.setApplicationName("VibeStream")
    app.setOrganizationName("VibeStream")
    app.setQuitOnLastWindowClosed(True)

    window = VibeStreamWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
