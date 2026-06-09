import argparse
import ctypes
import os, sys
import re
import requests
from pathlib import Path
import traceback
from datetime import datetime
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QThread, QEvent
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QProgressBar,
    QLabel, QTextEdit, QListWidget, QPushButton,
    QCheckBox, QTabWidget, QMenu, QInputDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
)
from pyutils.movewoker import clean_path, MoveWorker
from pyutils.folder_move import YearPickerDialog, FolderMoveWorker
from pyutils.verbose_folders import VerboseRenameDialog, split_prefixed_name

APP_DIR = Path(__file__).resolve().parent.as_posix()

TXT_RUTAS = r"C:\Users\miche\OneDrive\foobar2000\profile\foobar_selection.txt"
BASE_ROOT = r"E:\_Internal"
ICON_WIN = f"{APP_DIR}/assets/mpc.ico"

YEAR_PANEL_WIDTH = 120
SUB_PANEL_WIDTH = 260

BEERWEB = "http://localhost:8880"

myappid = 'etudetools.files_mgr.move_dialog.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def read_paths_from_default():
    p = Path(TXT_RUTAS)
    if p.exists() and p.is_file():
        text = p.read_text(encoding="utf-8", errors="ignore")
        lines = [clean_path(ln) for ln in text.splitlines() if ln.strip()]
        return lines, str(p)
    return [], str(p)

def archivo_en_uso(ruta):
    import msvcrt
    try:
        with open(ruta, "rb") as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        return False
    except (PermissionError, OSError):
        return True

def is_dir_empty(p: Path) -> bool:
    try:
        return not any(p.iterdir())
    except Exception:
        return False

def split_prefixed_subfolder(name: str):
    m = re.match(r"^(\d+\.\s*)(.*)$", name)
    if m:
        return m.group(1), m.group(2)
    return "", name

class MoverWindow(QtWidgets.QDialog):
    def __init__(self, paths, txt_path):
        super().__init__()
        self.setWindowTitle("Move Files - foobar2000")
        self.setWindowIcon(QIcon(ICON_WIN))
        self.setMinimumSize(700, 300)
        self.resize(1100, 420)

        self.paths = paths
        self.txt_path = txt_path
        self.move_thread = None
        self.move_worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_panel = QHBoxLayout()

        year_layout = QVBoxLayout()
        year_layout.addWidget(QLabel("Año"))

        years = [str(y) for y in range(2004, datetime.now().year + 1)]
        rows = (len(years) + 1) // 2

        self.list_year = QTableWidget(rows, 2)
        self.list_year.setFixedWidth(100)
        self.list_year.horizontalHeader().setVisible(False)
        self.list_year.verticalHeader().setVisible(False)
        self.list_year.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_year.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_year.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.list_year.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_year.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_year.setShowGrid(False)

        for index, year in enumerate(years):
            row = index // 2
            col = index % 2
            item = QTableWidgetItem(year)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_year.setItem(row, col, item)

        self.list_year.setColumnWidth(0, 90 // 2)
        self.list_year.setColumnWidth(1, 90 // 2)

        year_layout.addWidget(self.list_year)
        left_panel.addLayout(year_layout)

        current_year = datetime.now().year
        for r in range(self.list_year.rowCount()):
            for c in range(self.list_year.columnCount()):
                item = self.list_year.item(r, c)
                if item and item.text() == str(current_year):
                    self.list_year.setCurrentCell(r, c)
                    break

        sub_layout = QVBoxLayout()
        sub_layout.addWidget(QLabel("Subcarpeta"))

        self.list_sub = QListWidget()
        self.list_sub.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_sub.customContextMenuRequested.connect(self.on_sub_context_menu)
        self.list_sub.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_sub.setFixedWidth(200)
        sub_layout.addWidget(self.list_sub)

        left_panel.addLayout(sub_layout)

        self.tabs = QTabWidget()

        self.tab_main = QWidget()
        t1_layout = QVBoxLayout()

        t1_layout.addWidget(QLabel("Archivos seleccionados:"))
        self.text_paths = QTextEdit()
        self.text_paths.setReadOnly(True)
        self.text_paths.setAcceptRichText(False)
        self.text_paths.setText("\n".join(self.paths))
        t1_layout.addWidget(self.text_paths, stretch=3)

        hb = QHBoxLayout()
        v1 = QVBoxLayout()

        v1.addWidget(QLabel("Destino calculado:"))
        self.preview_label = QLabel("")
        self.preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v1.addWidget(self.preview_label)
        v1.addStretch()

        hb.addLayout(v1, stretch=2)
        t1_layout.addLayout(hb)

        self.tab_main.setLayout(t1_layout)
        self.tabs.addTab(self.tab_main, "Main")

        self.tab_results = QWidget()
        t2_layout = QVBoxLayout()
        t2_layout.addWidget(QLabel("Resultados:"))
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        self.text_results.setAcceptRichText(False)
        t2_layout.addWidget(self.text_results, stretch=1)
        self.tab_results.setLayout(t2_layout)
        self.tabs.addTab(self.tab_results, "Resultados")

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.tabs)

        buttons_h = QHBoxLayout()
        self.checkbox_top = QCheckBox("Siempre Visible")
        self.checkbox_top.setChecked(True)
        self.checkbox_top.stateChanged.connect(self.toggle_always_on_top)
        buttons_h.addWidget(self.checkbox_top)

        buttons_h.addStretch()

        self.btn_move = QPushButton("Mover")
        buttons_h.addWidget(self.btn_move)

        self.btn_close = QPushButton("Cerrar")
        buttons_h.addWidget(self.btn_close)
        
        # progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        right_panel.addWidget(self.progress_bar)

        right_panel.addLayout(buttons_h)

        main_layout.addLayout(left_panel)
        main_layout.addLayout(right_panel, stretch=1)
        self.setLayout(main_layout)

        self.list_year.itemSelectionChanged.connect(
            lambda: self.update_subfolders(
                self.list_year.currentItem().text() if self.list_year.currentItem() else ""
            )
        )
        self.list_sub.currentItemChanged.connect(lambda cur, _: self.update_preview())

        self.btn_move.clicked.connect(self.on_move)
        self.btn_close.clicked.connect(self.close)

        self.update_subfolders(datetime.now().year)
        
        self.list_sub.installEventFilter(self)

    def build_music_ahead_path(self, year):
        try:
            y = int(year)
        except ValueError:
            y = datetime.now().year
        prefix_num = y - 2003
        prefix = f"{prefix_num:02d}."
        folder_name = f"{prefix} music"
        return Path(BASE_ROOT) / str(y) / folder_name

    def update_subfolders(self, year):
        self.list_sub.clear()
        base = self.build_music_ahead_path(year)

        if base.exists() and base.is_dir():
            subs = sorted(p.name for p in base.iterdir() if p.is_dir())
            if not subs:
                self.list_sub.addItem("(no hay subcarpetas)")
            else:
                self.list_sub.addItems(subs)
                self.list_sub.setCurrentRow(0)
        else:
            self.list_sub.addItem("(no existe music para ese año)")

        self.update_preview()

    def update_preview(self):
        year_item = self.list_year.currentItem()
        sub_item = self.list_sub.currentItem()

        if not year_item:
            self.preview_label.setText("")
            return

        year = year_item.text()
        sub = sub_item.text() if sub_item else ""

        base = self.build_music_ahead_path(year)
        dest = Path(base) / sub if sub and not sub.startswith("(") else base
        self.preview_label.setText(str(dest))

    def on_move(self):
        self.text_results.clear()

        if not self.paths:
            self.text_results.append("Nada para mover.\n")
            self.tabs.setCurrentWidget(self.tab_results)
            return

        year_item = self.list_year.currentItem()
        sub_item = self.list_sub.currentItem()

        if not year_item or not sub_item:
            self.text_results.append("Selección incompleta.\n")
            self.tabs.setCurrentWidget(self.tab_results)
            return

        year = year_item.text()
        sub = sub_item.text()

        if not sub or sub.startswith("("):
            self.text_results.append("Subcarpeta no válida.\n")
            self.tabs.setCurrentWidget(self.tab_results)
            return

        base = self.build_music_ahead_path(year)
        dest_dir = Path(base) / sub

        current = self.foobar_current_path()

        if current and current in self.paths:
            if len(self.paths) == 1:
                self.text_results.append("▶ Archivo en reproducción → NEXT\n")
                self.foobar_next()
            else:
                self.text_results.append("⏹ Archivo en reproducción → STOP\n")
                self.foobar_stop()
        
        self.text_results.append(f"Iniciando movimiento a: {dest_dir}\n\n")

        self.set_busy(True)

        self.move_thread = QThread(self)
        self.move_worker = MoveWorker(self.paths, dest_dir)
        self.move_worker.moveToThread(self.move_thread)

        self.move_thread.started.connect(self.move_worker.run)
        self.move_worker.progress.connect(self.on_move_progress)
        self.move_worker.log.connect(self.text_results.append)
        self.move_worker.error.connect(self.on_move_error)
        self.move_worker.finished.connect(self.on_move_finished)

        self.move_worker.finished.connect(self.move_thread.quit)
        self.move_worker.finished.connect(self.move_worker.deleteLater)
        self.move_thread.finished.connect(self.move_thread.deleteLater)

        self.move_thread.start()
        return

    def foobar_next(self):
        try:
            requests.post(f"{BEERWEB}/api/player/next", timeout=1)
        except Exception as e:
            self.text_results.append(f"⚠ Error enviando NEXT a foobar: {e}\n")

    def foobar_stop(self):
        try:
            requests.post(f"{BEERWEB}/api/player/stop", timeout=1)
        except Exception as e:
            self.text_results.append(f"⚠ Error enviando STOP a foobar: {e}\n")

    def foobar_current_path(self):
        try:
            r = requests.get(f"{BEERWEB}/api/player", timeout=1).json()
            player = r.get("player", {})
            item = player.get("activeItem")

            if not item:
                return None

            playlist_id = item.get("playlistId")
            index = item.get("index")

            if playlist_id is None or index is None:
                return None

            url = f"{BEERWEB}/api/playlists/{playlist_id}/items/{index}:{index+1}"
            params = {"columns": ["%path%"]}

            resp = requests.get(url, params=params, timeout=1).json()
            items = resp.get("playlistItems", {}).get("items", [])

            if not items:
                return None

            cols = items[0].get("columns", [])
            if cols:
                return cols[0]

        except Exception:
            pass

        return None

    def limpiar_dead_items(self):
        try:
            playlists_resp = requests.get(f"{BEERWEB}/api/playlists").json()

            target_id = None
            target_title = "Unknown"

            if "playlists" in playlists_resp:
                for pl in playlists_resp["playlists"]:
                    if pl.get("isCurrent"):
                        target_id = pl["id"]
                        target_title = pl.get("title", "Unknown")
                        break

            if not target_id:
                self.text_results.append("⚠ No 'Current' playlist found (is Foobar open?)")
                return

            self.text_results.append(f"Scanning playlist: '{target_title}' [{target_id}]...")

            url = f"{BEERWEB}/api/playlists/{target_id}/items/0:20000"
            params = {"columns": ["%path%"]}

            resp = requests.get(url, params=params).json()

            if "error" in resp:
                self.text_results.append(f"⚠ API Error: {resp['error'].get('message')}")
                return

            items = []
            if "playlistItems" in resp and "items" in resp["playlistItems"]:
                items = resp["playlistItems"]["items"]
            elif "items" in resp:
                items = resp["items"]

            indices_to_remove = []

            for index, item in enumerate(items):
                path = None
                if "columns" in item and len(item["columns"]) > 0:
                    path = item["columns"][0]

                if path and not os.path.exists(path):
                    indices_to_remove.append(index)

            if not indices_to_remove:
                self.text_results.append("✔ No dead items found in current playlist.")
                return

            payload = {"items": indices_to_remove}
            del_url = f"{BEERWEB}/api/playlists/{target_id}/items/remove"
            del_resp = requests.post(del_url, json=payload)

            if del_resp.status_code in [200, 204]:
                self.text_results.append(f"✔ Cleaned {len(indices_to_remove)} dead items.")
            else:
                self.text_results.append(f"⚠ Delete failed. Code: {del_resp.status_code}")

        except Exception:
            self.text_results.append(f"FAIL cleaning dead items: {traceback.format_exc()}")

    def toggle_always_on_top(self, state):
        flags = self.windowFlags()

        if state == Qt.CheckState.Checked.value:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)

        self.show()

    def on_sub_context_menu(self, pos):
        item = self.list_sub.itemAt(pos)
        if not item:
            return

        sub_name = item.text()
        if sub_name.startswith("("):
            return

        year_item = self.list_year.currentItem()
        if not year_item:
            return

        year = year_item.text()
        base = self.build_music_ahead_path(year)
        target_dir = Path(base) / sub_name

        menu = QMenu(self)
        act_new = menu.addAction("Crear subcarpeta nueva")
        act_rename = menu.addAction("Renombrar esta subcarpeta")
        act_del = menu.addAction("Eliminar esta subcarpeta")
        act_move = menu.addAction("Mover carpeta")

        action = menu.exec(self.list_sub.mapToGlobal(pos))
        if not action:
            return

        if action == act_new:
            dlg = VerboseRenameDialog("", "", self, title="Crear subcarpeta nueva")
            if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return

            raw = dlg.selected_raw()
            suffix = dlg.selected_suffix()

            if not raw:
                return

            prefix_num = int(year) - 2003
            final_name = f"{prefix_num:02d}. {raw}"
            if suffix:
                final_name = f"{final_name}.{suffix}"

            new_dir = Path(base) / final_name
            try:
                new_dir.mkdir(parents=True, exist_ok=False)
                self.update_subfolders(year)
            except FileExistsError:
                QMessageBox.warning(self, "Ya existe", "La carpeta ya existe.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la carpeta:\n{e}")

        elif action == act_del:
            if not target_dir.exists():
                return

            if not is_dir_empty(target_dir):
                QMessageBox.warning(
                    self,
                    "No está vacía",
                    "La carpeta no está vacía.\nNo se puede eliminar."
                )
                return

            confirm = QMessageBox.question(
                self,
                "Eliminar carpeta",
                f"¿Eliminar la carpeta?\n\n{target_dir}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    target_dir.rmdir()
                    self.update_subfolders(year)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar:\n{e}")

        elif action == act_rename:
            self.rename_selected_subfolder()
        elif action == act_move:
            self.move_selected_subfolder()
            
    def eventFilter(self, obj, event):
        if obj is self.list_sub and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_F2:
                self.rename_selected_subfolder()
                return True
        return super().eventFilter(obj, event)

    def rename_selected_subfolder(self):
        item = self.list_sub.currentItem()
        if not item:
            return

        sub_name = item.text()
        if sub_name.startswith("("):
            return

        year_item = self.list_year.currentItem()
        if not year_item:
            return

        year = year_item.text()
        base = self.build_music_ahead_path(year)
        target_dir = Path(base) / sub_name

        if not target_dir.exists():
            return
        
        # new name keeping prefix
        prefix, raw_value, suffix_value = split_prefixed_name(sub_name)

        dlg = VerboseRenameDialog(raw_value, suffix_value, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        new_raw = dlg.selected_raw()
        new_suffix = dlg.selected_suffix()

        if not new_raw:
            return

        final_name = new_raw
        if new_suffix:
            final_name = f"{final_name}.{new_suffix}"

        if prefix:
            final_name = f"{prefix}{final_name}"

        if final_name == sub_name:
            return

        new_dir = target_dir.parent / final_name

        # final steps rename
        if new_dir.exists():
            QMessageBox.warning(self, "Ya existe", "Ya existe una carpeta con ese nombre.")
            return

        try:
            target_dir.rename(new_dir)
            self.update_subfolders(year)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo renombrar:\n{e}")

    def move_selected_subfolder(self):
        item = self.list_sub.currentItem()
        if not item or item.text().startswith("("):
            return

        year_item = self.list_year.currentItem()
        if not year_item:
            return

        src_year = year_item.text()
        src_base = self.build_music_ahead_path(src_year)
        src_dir = Path(src_base) / item.text()

        dlg = YearPickerDialog(self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        dest_year = dlg.selected_year()
        if not dest_year:
            return

        self.set_busy(True)
        self.move_thread = QThread(self)
        self.move_worker = FolderMoveWorker(src_dir, dest_year, BASE_ROOT)
        self.move_worker.moveToThread(self.move_thread)

        self.move_thread.started.connect(self.move_worker.run)
        self.move_worker.progress.connect(self.on_move_progress)
        self.move_worker.log.connect(self.text_results.append)
        self.move_worker.error.connect(self.on_move_error)
        self.move_worker.finished.connect(self.on_folder_move_finished)

        self.move_worker.finished.connect(self.move_thread.quit)
        self.move_worker.finished.connect(self.move_worker.deleteLater)
        self.move_thread.finished.connect(self.move_thread.deleteLater)

        self.move_thread.start()

    def on_folder_move_finished(self, source_year, dest_year):
        self.update_subfolders(source_year)
        self.set_busy(False)
        self.tabs.setCurrentWidget(self.tab_results)

    def set_busy(self, busy: bool):
        self.btn_move.setEnabled(not busy)
        self.btn_close.setEnabled(not busy)
        self.checkbox_top.setEnabled(not busy)
        self.list_year.setEnabled(not busy)
        self.list_sub.setEnabled(not busy)
        self.progress_bar.setVisible(busy)
        if busy:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("0%")

    def on_move_progress(self, done, total, current_path):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(done)
            self.progress_bar.setFormat(f"{done}/{total}")

    def on_move_error(self, tb):
        self.text_results.append(f"ERROR EN EL HILO:\n{tb}")
        self.set_busy(False)

    def on_move_finished(self, moved, failed, origin_dirs):
        deleted_dirs = []
        failed_dir_deletes = []

        candidate_dirs = []
        for d in origin_dirs:
            pd = Path(d)
            if pd.exists() and pd.is_dir() and is_dir_empty(pd):
                candidate_dirs.append(pd)

        if candidate_dirs:
            yes_all = False
            no_all = False

            for pd in candidate_dirs:
                if yes_all:
                    try:
                        if pd.exists() and pd.is_dir() and is_dir_empty(pd):
                            pd.rmdir()
                            deleted_dirs.append(str(pd))
                            self.text_results.append(f"DIR BORRADO (auto): {pd}\n")
                        continue
                    except Exception as e:
                        failed_dir_deletes.append((str(pd), str(e)))
                        self.text_results.append(f"ERROR BORRANDO (auto): {pd} -> {e}\n")
                        continue

                if no_all:
                    self.text_results.append(f"SKIP (auto): {pd}\n")
                    continue

                dlg = QMessageBox(self)
                dlg.setWindowTitle("Eliminar carpeta vacía?")
                dlg.setText(f"La carpeta parece estar vacía:\n{pd}\n\n¿Deseas eliminarla?")
                btn_yes = dlg.addButton("Sí", QMessageBox.ButtonRole.YesRole)
                btn_yes_all = dlg.addButton("Sí a todo", QMessageBox.ButtonRole.YesRole)
                btn_no = dlg.addButton("No", QMessageBox.ButtonRole.NoRole)
                btn_no_all = dlg.addButton("No a todo", QMessageBox.ButtonRole.NoRole)
                dlg.exec()

                chosen = dlg.clickedButton()

                if chosen == btn_yes:
                    try:
                        if pd.exists() and pd.is_dir() and is_dir_empty(pd):
                            pd.rmdir()
                            deleted_dirs.append(str(pd))
                            self.text_results.append(f"DIR BORRADO: {pd}\n")
                    except Exception as e:
                        failed_dir_deletes.append((str(pd), str(e)))
                        self.text_results.append(f"ERROR BORRANDO: {pd} -> {e}\n")

                elif chosen == btn_yes_all:
                    yes_all = True
                    try:
                        if pd.exists() and pd.is_dir() and is_dir_empty(pd):
                            pd.rmdir()
                            deleted_dirs.append(str(pd))
                            self.text_results.append(f"DIR BORRADO: {pd}\n")
                    except Exception as e:
                        failed_dir_deletes.append((str(pd), str(e)))
                        self.text_results.append(f"ERROR BORRANDO: {pd} -> {e}\n")

                elif chosen == btn_no:
                    self.text_results.append(f"SKIP: {pd}\n")
                elif chosen == btn_no_all:
                    no_all = True
                    self.text_results.append(f"SKIP (auto): {pd}\n")

        self.text_results.append("\n--- Resumen ---\n")
        self.text_results.append(f"Movidos: {len(moved)}")
        self.text_results.append(f"Fallidos: {len(failed)}")
        self.text_results.append(f"Carpetas eliminadas: {len(deleted_dirs)}")

        if failed_dir_deletes:
            self.text_results.append("Errores al eliminar carpetas:")
            for d, e in failed_dir_deletes[:20]:
                self.text_results.append(f"{d} -> {e}")

        remaining = [f[0] for f in failed if f[1]]
        self.paths = remaining
        self.text_paths.setText("\n".join(self.paths))

        if self.txt_path:
            try:
                Path(self.txt_path).write_text("\n".join(self.paths), encoding="utf-8")
            except Exception as e:
                self.text_results.append(f"No se pudo sobrescribir el TXT fuente: {e}\n")

        self.tabs.setCurrentWidget(self.tab_results)
        self.set_busy(False)

        if not failed:
            self.limpiar_dead_items()
            QTimer.singleShot(10, self.close)

def main():
    parser = argparse.ArgumentParser(description="Guardar una ruta en un archivo txt")
    parser.add_argument("ruta", help="Ruta a guardar")
    args = parser.parse_args()

    if not args.ruta.endswith(".txt"):
        with open(TXT_RUTAS, "w", encoding="utf-8") as f:
            f.write(args.ruta)

    paths, txt_path = read_paths_from_default()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_WIN))

    w = MoverWindow(paths, txt_path)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()