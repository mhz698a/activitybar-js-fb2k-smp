import re
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, 
    QDialogButtonBox
)

PREFIX_RE = re.compile(r"^(\d+\.\s*)(.*)$")

VERBOSE_MAP = {
    "_b.r": "_base.registry",
    "_b.t": "_base.theme",
    "_b.rt": "_base.registrytheme",
    "_d.r": "_domainbase.registry",
    "_d.t": "_domainbase.theme",
    "_d.rt": "_domainbase.registrytheme",
    "_s.r": "_superdomainbase.registry",
    "_s.t": "_superdomainbase.theme",
    "_s.rt": "_superdomainbase.registrytheme",
    "b.r": "base.registry",
    "b.t": "base.theme",
    "b.rt": "base.registrytheme",
    "d.r": "domainbase.registry",
    "d.t": "domainbase.theme",
    "d.rt": "domainbase.registrytheme",
    "s.r": "superdomainbase.registry",
    "s.t": "superdomainbase.theme",
    "s.rt": "superdomainbase.registrytheme",
}

DISPLAY_TO_RAW = {v: k for k, v in VERBOSE_MAP.items()}
RAW_KEYS = sorted(VERBOSE_MAP.keys(), key=len, reverse=True)

def split_prefixed_name(name: str):
    name = str(name or "").strip()

    prefix = ""
    body = name

    m = PREFIX_RE.match(name)
    if m:
        prefix = m.group(1)
        body = m.group(2).strip()

    raw = ""
    suffix = ""

    for candidate in RAW_KEYS:
        if body == candidate:
            raw = candidate
            break
        if body.startswith(candidate + "."):
            raw = candidate
            suffix = body[len(candidate) + 1:].strip()
            break

    if not raw:
        if "." in body:
            raw, suffix = body.rsplit(".", 1)
            raw = raw.strip()
            suffix = suffix.strip()
        else:
            raw = body

    return prefix, raw, suffix

class VerboseRenameDialog(QtWidgets.QDialog):
    def __init__(self, raw_value="", suffix_value="", parent=None, title="Renombrar subcarpeta"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(450, 80)

        layout = QVBoxLayout(self)

        row = QHBoxLayout()

        self.combo = QComboBox()
        for display, raw in DISPLAY_TO_RAW.items():
            self.combo.addItem(display, raw)

        idx = self.combo.findData(raw_value)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

        self.edit_suffix = QLineEdit()
        self.edit_suffix.setText(suffix_value)
        self.edit_suffix.setPlaceholderText("Nombre final opcional")

        row.addWidget(self.combo, stretch=2)
        row.addWidget(self.edit_suffix, stretch=3)

        layout.addLayout(row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_raw(self):
        return self.combo.currentData()

    def selected_suffix(self):
        return self.edit_suffix.text().strip()