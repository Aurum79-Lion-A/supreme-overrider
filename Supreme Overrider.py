# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 10:39:17 2026

@author: Mr. Cobalt 
"""

import sys
import ctypes
import os
import re
import shutil
import json
import traceback
import pycdlib
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QTextEdit, QFileDialog, QHBoxLayout,
                             QMessageBox, QComboBox, QLabel, QFrame, QStatusBar,
                             QGroupBox, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# --- 1. AdminMode & Translator ---
def request_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        script = os.path.abspath(sys.argv[0])
        params = f'"{script}" ' + " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

DEFAULT_LOCALE = {
    "title": "Supreme Overrider 1.0.3",
    "btn_open": "Open File",
    "btn_save": "Save Hex",
    "btn_delete": "Delete",
    "btn_iso": "Build ISO",
    "hex_label": "Hex Editor",
    "file_ops_label": "File Operations",
    "no_file": "No file selected",
    "ready": "Ready",
    "msg_success": "Success",
    "msg_error": "Error",
    "confirm_title": "Confirm",
    "confirm_delete": "'{path}' will be permanently deleted. Are you sure?",
    "warn_no_file": "Please select a file first.",
    "status_loaded": "Loaded: {name}",
    "status_building_iso": "Building ISO...",
    "placeholder_hex": "Hex data will appear here...",
    "btn_yes": "Yes",
    "btn_no": "No",
    "btn_ok": "OK",
    "filter_iso": "ISO Files (*.iso)",
    "dialog_open_file": "Select File",
    "dialog_select_folder_delete": "Select Folder to Delete",
    "dialog_select_folder_iso": "Select Folder for ISO",
    "dialog_save_iso": "Save As",
    "btn_prev": "◄ Prev Page",
    "btn_next": "Next Page ►",
    "page_info": "Page: {page}"
}

SUPPORTED_LANGUAGES = ["English", "Türkçe", "日本語", "Español", "Nederlands", "Українська"]

class Translator:
    def __init__(self, lang="English"):
        self.lang = lang
        self.data = self.load_lang()

    def load_lang(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "locales", f"{self.lang}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                merged = dict(DEFAULT_LOCALE)
                merged.update(loaded)
                print(f"[locale] Yüklendi: {path} ({len(loaded)} anahtar)")
                return merged
        except Exception as e:
            print(f"[locale] UYARI: {path} yüklenemedi ({e}) -> varsayılan (İngilizce) kullanılıyor")
            return dict(DEFAULT_LOCALE)

    def get(self, key, **kwargs):
        text = self.data.get(key, DEFAULT_LOCALE.get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

# --- 2. Core Engine ---
class SystemEngine:
    PAGE_SIZE = 1048576 # every page is 1 mb, you can change it from here recommended maximum is 500 mb

    @staticmethod
    def read_file_page(file_path, page_index=0):
        try:
            offset = page_index * SystemEngine.PAGE_SIZE
            with open(file_path, "rb") as f:
                f.seek(offset)
                data = f.read(SystemEngine.PAGE_SIZE)
            return True, data
        except Exception as e:
            return False, str(e)

    @staticmethod
    def edit_hex(file_path, hex_string, page_index=0):
        clean_hex = hex_string.replace(" ", "").replace("\n", "")
        if not (re.fullmatch(r'[0-9A-Fa-f]+', clean_hex) and len(clean_hex) % 2 == 0):
            return False, "invalid_hex"
        try:
            new_data = bytes.fromhex(clean_hex)
            offset = page_index * SystemEngine.PAGE_SIZE
            
            with open(file_path, "r+b") as f:
                f.seek(offset)
                f.write(new_data)
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def force_delete(path):
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def build_iso(source_folder, output_iso):
        try:
            iso = pycdlib.PyCdlib()
            iso.new(interchange_level=3, joliet=3, rock_ridge="1.09")

            for root, dirs, files in os.walk(source_folder):
                rel_root = os.path.relpath(root, source_folder)

                if rel_root != ".":
                    iso_dir_path = "/" + rel_root.replace("\\", "/")
                    iso_dir_path_upper = iso_dir_path.upper()
                    rr_dir_name = os.path.basename(root)
                    joliet_dir_path = "/" + rel_root.replace("\\", "/")
                    try:
                        iso.add_directory(
                            iso_path=iso_dir_path_upper,
                            rr_name=rr_dir_name,
                            joliet_path=joliet_dir_path
                        )
                    except Exception:
                        pass

                for i, file in enumerate(files):
                    full_path = os.path.join(root, file)
                    if rel_root == ".":
                        rel_path = file
                    else:
                        rel_path = os.path.join(rel_root, file).replace("\\", "/")

                    short_name = f"F{i:04d}.BIN;1"
                    iso_dir_prefix = "" if rel_root == "." else "/" + rel_root.replace("\\", "/").upper()
                    iso_path = f"{iso_dir_prefix}/{short_name}"
                    rr_name = file
                    joliet_dir_prefix = "" if rel_root == "." else "/" + rel_root.replace("\\", "/")
                    joliet_path = f"{joliet_dir_prefix}/{file}"

                    iso.add_file(
                        full_path,
                        iso_path=iso_path,
                        rr_name=rr_name,
                        joliet_path=joliet_path
                    )

            iso.write(output_iso)
            iso.close()
            return True, None
        except Exception as e:
            return False, str(e)

# --- 3. Stil (QSS) ---
DARK_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
}
QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #89b4fa;
    padding: 4px 0px;
}
QLabel#SubtitleLabel {
    font-size: 11px;
    font-weight: 600;
    color: #6c7086;
    background-color: #313244;
    border-radius: 4px;
    padding: 2px 8px;
    margin-top: 6px;
}
QLabel#StatusLabel {
    color: #a6adc8;
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 10px;
    font-weight: bold;
    color: #89b4fa;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QTextEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', monospace;
    font-size: 13px;
    color: #a6e3a1;
}
QTextEdit:focus {
    border: 1px solid #89b4fa;
}
QPushButton {
    background-color: #313244;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton#DangerBtn:hover {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#PrimaryBtn {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QPushButton#PrimaryBtn:hover {
    background-color: #74a8f8;
}
QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 100px;
}
QComboBox:hover {
    border: 1px solid #89b4fa;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    selection-background-color: #45475a;
    color: #cdd6f4;
}
QStatusBar {
    background-color: #11111b;
    color: #a6adc8;
}
QFrame#Divider {
    background-color: #313244;
    max-height: 1px;
}
"""

# --- 4. UI ---
class SupremeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.t = Translator("English")
        self.current_file = None
        self.current_page = 0
        self.setMinimumSize(720, 680)
        self.setStyleSheet(DARK_STYLE)

        root = QVBoxLayout()
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(12)

        # --- top bar: title + lang box ---
        top_bar = QHBoxLayout()
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title_label = QLabel()
        self.title_label.setObjectName("TitleLabel")
        title_row.addWidget(self.title_label)

        subtitle_label = QLabel("Glory to Ukraine - Free Palestine")
        subtitle_label.setObjectName("SubtitleLabel")
        title_row.addWidget(subtitle_label)

        top_bar.addLayout(title_row)
        top_bar.addStretch()

        lang_label = QLabel("\U0001F310")
        top_bar.addWidget(lang_label)
        self.lang_box = QComboBox()
        self.lang_box.addItems(SUPPORTED_LANGUAGES)
        self.lang_box.currentTextChanged.connect(self.change_lang)
        top_bar.addWidget(self.lang_box)
        root.addLayout(top_bar)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(divider)

        # --- file status ---
        self.file_status = QLabel()
        self.file_status.setObjectName("StatusLabel")
        root.addWidget(self.file_status)

        # --- Hex group ---
        self.hex_group = QGroupBox()
        hex_layout = QVBoxLayout()
        self.text_area = QTextEdit()
        hex_layout.addWidget(self.text_area)

        # navigate
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton()
        self.btn_next = QPushButton()
        self.lbl_page_info = QLabel()
        self.lbl_page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_page_info, stretch=1)
        nav_layout.addWidget(self.btn_next)
        hex_layout.addLayout(nav_layout)

        self.hex_group.setLayout(hex_layout)
        root.addWidget(self.hex_group, stretch=1)

        # --- file menu ---
        self.file_group = QGroupBox()
        file_grid = QGridLayout()
        file_grid.setSpacing(10)

        self.btn_open = QPushButton()
        self.btn_save = QPushButton()
        self.btn_save.setObjectName("PrimaryBtn")
        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("DangerBtn")
        self.btn_iso = QPushButton()

        for b in (self.btn_open, self.btn_save, self.btn_delete, self.btn_iso, self.btn_prev, self.btn_next):
            b.setMinimumHeight(40)
            if b in (self.btn_open, self.btn_save, self.btn_delete, self.btn_iso):
                b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        file_grid.addWidget(self.btn_open, 0, 0)
        file_grid.addWidget(self.btn_save, 0, 1)
        file_grid.addWidget(self.btn_delete, 1, 0)
        file_grid.addWidget(self.btn_iso, 1, 1)
        self.file_group.setLayout(file_grid)
        root.addWidget(self.file_group)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        # --- status bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # connections
        self.btn_open.clicked.connect(self.open_file)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_delete.clicked.connect(self.delete_item)
        self.btn_iso.clicked.connect(self.run_archiver)
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

        self.change_lang("English")

    def update_file_status(self):
        if self.current_file:
            self.file_status.setText(
                f"\U0001F4C4 {os.path.basename(self.current_file)}  \u2014  {self.current_file}"
            )
        else:
            self.file_status.setText(self.t.get("no_file"))
        self.lbl_page_info.setText(self.t.get("page_info", page=self.current_page))

    def change_lang(self, new_lang):
        self.t = Translator(new_lang)
        self.btn_open.setText(self.t.get("btn_open"))
        self.btn_save.setText(self.t.get("btn_save"))
        self.btn_delete.setText(self.t.get("btn_delete"))
        self.btn_iso.setText(self.t.get("btn_iso"))
        self.btn_prev.setText(self.t.get("btn_prev"))
        self.btn_next.setText(self.t.get("btn_next"))
        self.setWindowTitle(self.t.get("title"))
        self.title_label.setText(self.t.get("title"))
        self.hex_group.setTitle(self.t.get("hex_label"))
        self.file_group.setTitle(self.t.get("file_ops_label"))
        self.text_area.setPlaceholderText(self.t.get("placeholder_hex"))
        self.update_file_status()
        self.status_bar.showMessage(self.t.get("ready"))

    def load_current_page_data(self):
        if not self.current_file:
            return
        ok, data = SystemEngine.read_file_page(self.current_file, self.current_page)
        if ok:
            self.text_area.setPlainText(' '.join(f'{b:02x}' for b in data).upper())
            self.update_file_status()
        else:
            self._error_box(self.t.get("msg_error"), f"{self.t.get('msg_error')}: {data}")

    def prev_page(self):
        if not self.current_file:
            return
        if self.current_page > 0:
            self.current_page -= 1
            self.load_current_page_data()

    def next_page(self):
        if not self.current_file:
            return
        file_size = os.path.getsize(self.current_file)
        max_page = max(0, (file_size - 1) // SystemEngine.PAGE_SIZE)
        if self.current_page < max_page:
            self.current_page += 1
            self.load_current_page_data()

    def _info_box(self, title, text):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Information)
        box.setWindowTitle(title)
        box.setText(text)
        box.addButton(self.t.get("btn_ok"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def _error_box(self, title, text):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle(title)
        box.setText(text)
        box.addButton(self.t.get("btn_ok"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def _warn_box(self, title, text):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        box.addButton(self.t.get("btn_ok"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def _confirm_box(self, title, text):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(title)
        box.setText(text)
        yes_btn = box.addButton(self.t.get("btn_yes"), QMessageBox.ButtonRole.YesRole)
        no_btn = box.addButton(self.t.get("btn_no"), QMessageBox.ButtonRole.NoRole)
        box.setDefaultButton(no_btn)
        box.exec()
        return box.clickedButton() == yes_btn

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, self.t.get("dialog_open_file"))
        if path:
            self.current_file = path
            self.current_page = 0 
            self.load_current_page_data()
            self.status_bar.showMessage(self.t.get("status_loaded", name=os.path.basename(path)))

    def save_file(self):
        if not self.current_file:
            self._warn_box(self.t.get("msg_error"), self.t.get("warn_no_file"))
            return
        ok, err = SystemEngine.edit_hex(self.current_file, self.text_area.toPlainText(), self.current_page)
        if ok:
            self.status_bar.showMessage(self.t.get("msg_success"))
            self._info_box(self.t.get("msg_success"), self.t.get("msg_success"))
        else:
            self.status_bar.showMessage(self.t.get("msg_error"))
            self._error_box(self.t.get("msg_error"), f"{self.t.get('msg_error')}: {err}")

    def delete_item(self):
        path = QFileDialog.getExistingDirectory(self, self.t.get("dialog_select_folder_delete"))
        if not path:
            return
        confirmed = self._confirm_box(
            self.t.get("confirm_title"),
            self.t.get("confirm_delete", path=path)
        )
        if confirmed:
            ok, err = SystemEngine.force_delete(path)
            if ok:
                self.status_bar.showMessage(self.t.get("msg_success"))
                self._info_box(self.t.get("msg_success"), self.t.get("msg_success"))
            else:
                self.status_bar.showMessage(self.t.get("msg_error"))
                self._error_box(self.t.get("msg_error"), f"{self.t.get('msg_error')}: {err}")

    def run_archiver(self):
        source = QFileDialog.getExistingDirectory(self, self.t.get("dialog_select_folder_iso"))
        if not source:
            return
        output, _ = QFileDialog.getSaveFileName(
            self, self.t.get("dialog_save_iso"), "output.iso", self.t.get("filter_iso")
        )
        if output:
            self.status_bar.showMessage(self.t.get("status_building_iso"))
            QApplication.processEvents()
            ok, err = SystemEngine.build_iso(source, output)
            if ok:
                self.status_bar.showMessage(self.t.get("msg_success"))
                self._info_box(self.t.get("msg_success"), self.t.get("msg_success"))
            else:
                self.status_bar.showMessage(self.t.get("msg_error"))
                self._error_box(self.t.get("msg_error"), f"{self.t.get('msg_error')}: {err}")

# --- 5. Giriş noktası ---
if __name__ == "__main__":
    try: # by Mr. Cobalt / Lion-A Softwares / github : https://github.com/Aurum79-Lion-A
        request_admin()
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        window = SupremeWindow()
        window.show()
        sys.exit(app.exec())
    except Exception:
        error_text = traceback.format_exc()
        try:
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(error_text)
        except Exception:
            pass
        print(error_text)
        input("Error Occured. error.log for details... Click Enter to close.")