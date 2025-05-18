from PySide6.QtCore import QThread, Signal
import requests

class FileDownloadThread(QThread):
    """
    FileDownloadThread
    ------------------
    A reusable QThread for downloading any file in the background.
    Emits the 'finished' signal with (file_path, success, error_msg) when done.

    Usage:
        thread = FileDownloadThread(url, save_path)
        thread.finished.connect(your_callback)
        thread.start()
    """
    finished = Signal(str, bool, str)  # file_path, success, error_msg

    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            r = requests.get(self.url, timeout=15)
            r.raise_for_status()
            with open(self.save_path, "wb") as f:
                f.write(r.content)
            self.finished.emit(self.save_path, True, "")
        except Exception as e:
            self.finished.emit(self.save_path, False, str(e)) 