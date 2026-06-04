from __future__ import annotations

import asyncio
import ctypes
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import wave
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from PyQt6.QtCore import QObject, QThread, Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

import pyaudiowpatch as pyaudio
from shazamio import Shazam

NOFOUND_URL = "https://github.com/mhz698a/NoFound"
RECOGNITION_SECONDS = 10
CHUNK = 1024
AUDIO_FORMAT = pyaudio.paInt16

myappid = 'etudetools.shazam.recognition.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
APP_DIR = Path(__file__).resolve().parent.as_posix()

@dataclass(frozen=True)
class RecognitionResult:
    found: bool
    query: Optional[str] = None
    google_url: Optional[str] = None


def _build_google_search_url(title: str, artist: str) -> str:
    query = f"{title} {artist}".strip()
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _extract_track_info(payload: object) -> tuple[Optional[str], Optional[str]]:
    """
    Try to extract a title/artist pair from ShazamIO output.
    ShazamIO returns a dict; the track info is usually inside payload['track'].
    """
    if not isinstance(payload, dict):
        return None, None

    track = payload.get("track") if isinstance(payload.get("track"), dict) else payload

    title = None
    artist = None

    if isinstance(track, dict):
        title = track.get("title") or track.get("name")
        artist = track.get("subtitle") or track.get("artist")

        # Fallbacks for edge cases.
        if not artist:
            share = track.get("share")
            if isinstance(share, dict):
                artist = share.get("subject")

    title = str(title).strip() if title else None
    artist = str(artist).strip() if artist else None

    return title, artist


async def _recognize_file_async(path: str) -> RecognitionResult:
    shazam = Shazam()
    output = await shazam.recognize(path)
    title, artist = _extract_track_info(output)

    if not title or not artist:
        return RecognitionResult(found=False)

    google_url = _build_google_search_url(title, artist)
    return RecognitionResult(found=True, query=f"{artist} - {title}", google_url=google_url)


class RecognitionWorker(QObject):
    finished = pyqtSignal(object)
    status = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, duration_seconds: int = RECOGNITION_SECONDS) -> None:
        super().__init__()
        self.duration_seconds = duration_seconds
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    def _record_desktop_audio(self, wav_path: str) -> None:
        with pyaudio.PyAudio() as p:
            loopback = p.get_default_wasapi_loopback()
            if not loopback:
                raise RuntimeError("No se encontró un dispositivo WASAPI loopback.")

            rate = int(loopback.get("defaultSampleRate") or 44100)
            channels = int(loopback.get("maxInputChannels") or 2)
            channels = max(1, min(channels, 2))
            device_index = int(loopback["index"])

            self.status.emit(
                f"Escuchando audio del escritorio... ({self.duration_seconds}s)"
            )

            stream = p.open(
                format=AUDIO_FORMAT,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK,
            )

            frames: list[bytes] = []
            start = time.monotonic()

            try:
                while not self._cancel_event.is_set():
                    elapsed = time.monotonic() - start
                    if elapsed >= self.duration_seconds:
                        break
                    frames.append(stream.read(CHUNK, exception_on_overflow=False))
            finally:
                stream.stop_stream()
                stream.close()

            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(AUDIO_FORMAT))
                wf.setframerate(rate)
                wf.writeframes(b"".join(frames))

    @pyqtSlot()
    def run(self) -> None:
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="shazam_desktop_")
            os.close(fd)

            self._record_desktop_audio(temp_path)

            if self._cancel_event.is_set():
                self.finished.emit(RecognitionResult(found=False))
                return

            self.status.emit("Analizando con Shazam...")
            result = asyncio.run(_recognize_file_async(temp_path))
            self.finished.emit(result)

        except Exception:
            self.failed.emit("")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


class ListenDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shazam Recognition Songs")
        self.resize(320, 100)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setModal(True)

        self.label = QLabel("Escuchando la canción del escritorio...")
        self.label.setWordWrap(True)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self._cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.cancel_button)

        self.thread: Optional[QThread] = None
        self.worker: Optional[RecognitionWorker] = None
        self._cancelled_by_user = False

    def start(self) -> None:
        self.thread = QThread(self)
        self.worker = RecognitionWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.status.connect(self.label.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._cleanup_worker)

        self.thread.start()

    @pyqtSlot()
    def _cancel(self) -> None:
        self._cancelled_by_user = True
        self.cancel_button.setEnabled(False)
        self.label.setText("Cancelando...")
        if self.worker is not None:
            self.worker.cancel()

    def _close_dialog(self, accepted: bool) -> None:
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(2000)

        if accepted:
            self.accept()
        else:
            self.reject()

    @pyqtSlot(object)
    def _on_finished(self, result: object) -> None:
        if self._cancelled_by_user:
            self._close_dialog(accepted=False)
            return

        if isinstance(result, RecognitionResult) and result.found and result.google_url:
            QDesktopServices.openUrl(QUrl(result.google_url))
        else:
            QDesktopServices.openUrl(QUrl(NOFOUND_URL))

        self._close_dialog(accepted=True)

    @pyqtSlot(str)
    def _on_failed(self, _: str) -> None:
        if self._cancelled_by_user:
            self._close_dialog(accepted=False)
            return
        QDesktopServices.openUrl(QUrl(NOFOUND_URL))
        self._close_dialog(accepted=True)

    def _cleanup_worker(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()
            self.worker = None


def main() -> int:
    icon_path = f"{APP_DIR}/assets/shazam.ico"
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path)) 
    dlg = ListenDialog()
    dlg.setWindowIcon(QIcon(icon_path))
    dlg.start()
    dlg.open()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
