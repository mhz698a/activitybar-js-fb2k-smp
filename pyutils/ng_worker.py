# ng_worker.py
import os
import re
import traceback
import requests
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from pyutils.ng_extract import extract_ng, NGError
from pyutils.wctime import setctime_blocking

_ID_RE = re.compile(r"\(ID:\s*\d+\)$")


def _sanitize_filename(name: str) -> str:
    return "".join(c for c in name if c not in r'<>:"/\|?*').strip()


def ensure_ng_id_in_title(title: str, song_id: str) -> str:
    if not title:
        return f"(ID: {song_id})"
    title = title.rstrip()
    if _ID_RE.search(title):
        return title
    return f"{title} (ID: {song_id})"


def add_eta_suffix(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    name = name.rstrip()
    if name.endswith(" (η)"):
        return filename
    return f"{name} (η){ext}"


def apply_ng_metadata(mp3_path: str, title: str, artist: str | None, song_id: str) -> None:
    try:
        try:
            audio = EasyID3(mp3_path)
        except ID3NoHeaderError:
            audio = MP3(mp3_path, ID3=EasyID3)
            audio.add_tags()

        changed = False

        current_title = audio.get("title", [""])[0].strip()
        if not current_title or f"(ID: {song_id})" not in current_title:
            audio["title"] = title
            changed = True

        current_artist = audio.get("artist", [""])[0].strip()
        if artist and not current_artist:
            audio["artist"] = artist
            changed = True

        if changed:
            audio.save()

    except Exception:
        pass


class NGDownloadWorker(QObject):
    started = pyqtSignal()
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, task_id, song_id, dest_path):
        super().__init__()
        self.task_id = int(task_id)
        self.song_id = str(song_id)
        self.dest_path = dest_path
        self._cancel = False

    def cancel(self):
        self.failed.emit("cancelled")

    stop = cancel
    
    @pyqtSlot()
    def run(self):
        self.started.emit()

        try:
            meta = extract_ng(self.song_id)
        except NGError as e:
            self.failed.emit(str(e))
            return
        except Exception as e:
            self.log.emit(traceback.format_exc())
            return

        mp3_url = meta.get("mp3_url")
        if not mp3_url:
            self.failed.emit("mp3_url no encontrado")
            return

        raw_title = meta.get("title") or f"ng_{self.song_id}"
        artist = meta.get("artist")
        tag_title = ensure_ng_id_in_title(raw_title, self.song_id)
        file_title = raw_title.rstrip()

        filename = add_eta_suffix(_sanitize_filename(file_title) + ".mp3")

        if self.dest_path:
            if os.path.isdir(self.dest_path) or self.dest_path.endswith(os.sep):
                dest = os.path.join(self.dest_path, filename)
            else:
                dest = self.dest_path
        else:
            dest = os.path.join(os.getcwd(), filename)

        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        tmp_path = dest + ".part"

        try:
            with requests.get(mp3_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length") or 0) or None
                downloaded = 0
                chunk_size = 64 * 1024

                with open(tmp_path, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if self._cancel:
                            try:
                                fh.close()
                            except Exception:
                                pass
                            try:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                            except Exception:
                                pass
                            self.failed.emit("cancelled")
                            return

                        if not chunk:
                            continue

                        fh.write(chunk)
                        downloaded += len(chunk)

                        self.progress.emit(downloaded, total or 0)

            if os.path.exists(dest):
                os.remove(dest)

            os.replace(tmp_path, dest)
            apply_ng_metadata(dest, tag_title, artist, self.song_id)

            ts = meta.get("last_modified_ts")
            if ts:
                try:
                    os.utime(dest, (ts, ts))
                    setctime_blocking(dest, ts)
                except Exception:
                    pass

            self.finished.emit({
                "task_id": self.task_id,
                "filepath": dest
            })
            self.log.emit("Finalizado con exito")

        except Exception as e:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

            self.log.emit(traceback.format_exc())
            self.failed.emit(str(e))