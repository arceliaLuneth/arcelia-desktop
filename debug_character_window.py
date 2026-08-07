"""
Diagnostik jendela karakter Arcelia.

Jalankan ini langsung (bukan lewat main.py):
    python3 debug_character_window.py

Ini bakal munculin 3 window BERURUTAN (tutup satu, lanjut ke berikutnya
otomatis setelah 4 detik). Perhatikan window mana yang KELIATAN dan mana
yang TIDAK — itu nunjukin persis di step mana masalahnya.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


def make_step1_normal_window() -> QWidget:
    """Window BIASA — ada bingkai, TIDAK transparan, posisi normal.
    Kalau ini aja nggak keliatan, masalahnya bukan soal transparansi/frameless
    sama sekali — kemungkinan besar soal window manager/multi-monitor."""
    w = QWidget()
    w.setWindowTitle("STEP 1 - Window biasa")
    w.resize(300, 200)
    layout = QVBoxLayout(w)
    label = QLabel("STEP 1\n\nKalau kamu lihat window putih ini,\nklik X untuk lanjut ke Step 2.")
    label.setStyleSheet("font-size: 14px; padding: 20px;")
    layout.addWidget(label)
    return w


def make_step2_frameless_ontop() -> QWidget:
    """Frameless + always-on-top, TAPI MASIH OPAQUE (tidak transparan).
    Kalau step 1 keliatan tapi step 2 nggak, masalahnya di FramelessWindowHint
    atau WindowStaysOnTopHint / Qt.Tool -- bukan di transparansinya."""
    w = QWidget()
    w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    w.resize(300, 200)
    w.setStyleSheet("background: red;")
    layout = QVBoxLayout(w)
    label = QLabel("STEP 2\n\nKotak MERAH ini frameless + always-on-top\n(tapi belum transparan).\nTutup lewat Alt+F4 untuk lanjut.")
    label.setStyleSheet("color: white; font-size: 14px; padding: 20px;")
    layout.addWidget(label)
    return w


def make_step3_translucent() -> QWidget:
    """Sama seperti CharacterWindow beneran: frameless + always-on-top +
    WA_TranslucentBackground. Kalau step 2 keliatan tapi step 3 nggak,
    masalahnya di kombinasi transparansi + compositor KDE kamu."""
    w = QWidget()
    w.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    w.setAttribute(Qt.WA_TranslucentBackground)
    w.resize(300, 200)
    layout = QVBoxLayout(w)
    label = QLabel("STEP 3\n\nIni PERSIS setup CharacterWindow asli\n(frameless + always-on-top + transparan).\nBackground-nya sengaja setengah transparan\nbiar kelihatan bedanya.")
    label.setStyleSheet("color: black; font-size: 13px; padding: 20px; background: rgba(255, 200, 0, 180); border-radius: 12px;")
    layout.addWidget(label)
    return w


def main() -> None:
    app = QApplication(sys.argv)

    screen = app.primaryScreen()
    geo = screen.availableGeometry()
    print(f"Info layar: {geo.width()}x{geo.height()}, posisi ({geo.x()}, {geo.y()})")
    print(f"Jumlah layar terdeteksi: {len(app.screens())}")
    print()

    windows = []

    def show_step(step_num: int, factory) -> None:
        w = factory()
        # posisi tengah layar biar gampang ketemu, bukan (0,0) yang bisa
        # ketiban taskbar/panel
        x = geo.x() + (geo.width() - w.width()) // 2
        y = geo.y() + (geo.height() - w.height()) // 2
        w.move(x, y)
        w.show()
        w.raise_()
        w.activateWindow()
        windows.append(w)
        print(f"STEP {step_num}: window.isVisible() = {w.isVisible()}, geometry = {w.geometry()}")

    show_step(1, make_step1_normal_window)
    QTimer.singleShot(4000, lambda: show_step(2, make_step2_frameless_ontop))
    QTimer.singleShot(8000, lambda: show_step(3, make_step3_translucent))
    QTimer.singleShot(13000, app.quit)

    app.exec()
    print()
    print("Selesai. Kabarin: window mana aja yang BENERAN keliatan di layar kamu (1/2/3)?")


if __name__ == "__main__":
    main()
