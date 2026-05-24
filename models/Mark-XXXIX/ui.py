from __future__ import annotations
import json, math, os, platform, subprocess, sys, threading, time
from pathlib import Path
import psutil
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout

C = type('Colors', (), {
    'BG': "#00060a", 'PANEL': "#010d14", 'BORDER': "#0d3347",
    'PRI': "#00d4ff", 'ACC': "#ff6b00", 'ACC2': "#ffcc00",
    'GREEN': "#00ff88", 'RED': "#ff3355", 'TEXT': "#8ffcff", 'TEXT_DIM': "#3a8a9a"
})()

def qcol(h, a=255): c = QColor(h); c.setAlpha(a); return c

class HudCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.muted = False
        self.speaking = False
        self.state = "INITIALISING"
        self._tick = 0
        self._halo = 55
        self._scale = 1.0
        self._last_t = time.time()
        self._blink = True
        self._blink_tick = 0
        self._rings = [0.0, 120.0, 240.0]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(50)

    def _step(self):
        self._tick += 1
        now = time.time()
        if now - self._last_t > 0.4:
            if self.speaking:
                self._scale = 1.08
                self._halo = 160
            elif self.muted:
                self._scale = 1.0
                self._halo = 20
            else:
                self._scale = 1.02
                self._halo = 60
            self._last_t = now

        for i, spd in enumerate([0.5, -0.35, 0.9]):
            self._rings[i] = (self._rings[i] + spd) % 360

        self._blink_tick += 1
        if self._blink_tick >= 40:
            self._blink = not self._blink
            self._blink_tick = 0
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), qcol(C.BG))
        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        fw = min(W, H)
        r_face = fw * 0.35

        for i in range(10):
            r = r_face * (1.8 - i * 0.08)
            frc = 1.0 - i / 10
            a = max(0, min(255, int(self._halo * 0.085 * frc)))
            p.setPen(QPen(qcol(C.RED if self.muted else C.PRI, a)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        for idx, (r_frac, w_r) in enumerate([(0.48, 3), (0.40, 2), (0.32, 1)]):
            ring_r = fw * r_frac
            a_val = max(0, min(255, int(self._halo * (1.0 - idx * 0.18))))
            p.setPen(QPen(qcol(C.RED if self.muted else C.PRI, a_val), w_r))
            p.setBrush(Qt.BrushStyle.NoBrush)
            for deg in range(int(self._rings[idx]), int(self._rings[idx]) + 270, 30):
                rad = math.radians(deg)
                p.drawPoint(cx + ring_r * math.cos(rad), cy - ring_r * math.sin(rad))

        orb_r = int(fw * 0.22 * self._scale)
        oc = (200, 0, 50) if self.muted else (0, 60, 110)
        for i in range(8, 0, -1):
            r2 = int(orb_r * i / 8)
            frc = i / 8
            a = max(0, min(255, int(self._halo * 1.1 * frc)))
            p.setBrush(QBrush(QColor(int(oc[0]*frc), int(oc[1]*frc), int(oc[2]*frc), a)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(cx - r2, cy - r2, r2 * 2, r2 * 2)
        p.setPen(QPen(qcol(C.PRI, min(255, int(self._halo * 2))), 1))
        p.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        p.drawText(int(cx - 60), int(cy - 10), 120, 20, Qt.AlignmentFlag.AlignCenter, "J.A.R.V.I.S")

        sy = cy + fw * 0.42
        if self.muted:
            txt, col = "MUTED", C.RED
        elif self.speaking:
            txt, col = "SPEAKING", C.ACC
        else:
            sym = "O" if self._blink else "o"
            txt, col = f"{sym} {self.state}", C.GREEN

        p.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        p.setPen(QPen(col, 1))
        p.drawText(0, int(sy), W, 20, Qt.AlignmentFlag.AlignCenter, txt)

        wy = sy + 28
        N, bw = 36, 8
        wx0 = (W - N * bw) / 2
        for i in range(N):
            if self.muted:
                hgt = 2
            elif self.speaking:
                hgt = 15 if i % 3 == 0 else 8
            else:
                hgt = int(4 + 3 * math.sin(self._tick * 0.08 + i * 0.5))
            p.fillRect(int(wx0 + i * bw), int(wy + 20 - hgt), bw - 1, hgt, qcol(C.PRI if hgt > 8 else C.TEXT_DIM))

class SetupOverlay(QWidget):
    done = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(f"background: rgba(0, 6, 10, 245); border: 1px solid {C.BORDER}; border-radius: 6px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 22)
        layout.setSpacing(10)

        lbl = QLabel("INITIALISATION REQUIRED")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {C.PRI};")
        layout.addWidget(lbl)

        lbl2 = QLabel("Configure JARVIS before first boot.")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl2.setFont(QFont("Courier New", 9))
        lbl2.setStyleSheet(f"color: {C.TEXT_DIM};")
        layout.addWidget(lbl2)

        lbl3 = QLabel("GEMINI API KEY")
        lbl3.setFont(QFont("Courier New", 8))
        lbl3.setStyleSheet(f"color: {C.TEXT_DIM};")
        layout.addWidget(lbl3)

        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("Enter your Gemini API key...")
        self._key_input.setFont(QFont("Courier New", 10))
        self._key_input.setFixedHeight(32)
        self._key_input.setStyleSheet(f"background: #000d12; color: {C.TEXT}; border: 1px solid {C.BORDER}; border-radius: 3px; padding: 4px 8px;")
        layout.addWidget(self._key_input)

        btn = QPushButton("INITIALISE")
        btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"background: transparent; color: {C.PRI}; border: 1px solid {C.BORDER}; border-radius: 3px;")
        btn.clicked.connect(self._submit)
        layout.addWidget(btn)

    def _submit(self):
        key = self._key_input.text().strip()
        if not key:
            self._key_input.setStyleSheet(f"background: #000d12; color: {C.TEXT}; border: 1px solid {C.RED}; border-radius: 3px; padding: 4px 8px;")
            return
        config_dir = Path(__file__).parent / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "api_keys.json").write_text(json.dumps({"gemini_api_key": key}, indent=2))
        self.hide()
        if self.done:
            self.done(key)

class JarvisUI:
    def __init__(self, face_path=None):
        self.app = QApplication(sys.argv)
        self.root = QWidget()
        self.root.setWindowTitle("J.A.R.V.I.S - MARK XXXIX")
        self.root.setMinimumSize(900, 600)
        self.root.setStyleSheet(f"background: {C.BG};")

        layout = QVBoxLayout(self.root)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("J.A.R.V.I.S")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Courier New", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {C.PRI}; background: #000d14; padding: 12px;")
        header.setFixedHeight(50)
        layout.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)

        self.hud = HudCanvas()
        self.hud.setMinimumHeight(350)
        body_layout.addWidget(self.hud)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 9))
        self._log.setStyleSheet(f"background: {C.PANEL}; color: {C.TEXT}; border: 1px solid {C.BORDER}; padding: 8px;")
        body_layout.addWidget(self._log, stretch=1)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command...")
        self._input.setFont(QFont("Courier New", 10))
        self._input.setStyleSheet(f"background: #000d14; color: {C.TEXT}; border: 1px solid {C.BORDER}; border-radius: 3px; padding: 6px;")
        self._input.returnPressed.connect(self._send)
        input_row.addWidget(self._input)

        send_btn = QPushButton("SEND")
        send_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        send_btn.setStyleSheet(f"background: {C.PANEL}; color: {C.PRI}; border: 1px solid {C.BORDER};")
        send_btn.clicked.connect(self._send)
        input_row.addWidget(send_btn)
        body_layout.addLayout(input_row)

        self._mute_btn = QPushButton("MUTE")
        self._mute_btn.setFont(QFont("Courier New", 8))
        self._mute_btn.setStyleSheet(f"background: {C.PANEL}; color: {C.TEXT}; border: 1px solid {C.BORDER};")
        self._mute_btn.clicked.connect(self._toggle_mute)
        body_layout.addWidget(self._mute_btn)

        layout.addWidget(body, stretch=1)

        footer = QLabel("MARK XXXIX - FatihMakes Industries")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Courier New", 7))
        footer.setStyleSheet(f"color: {C.TEXT_DIM}; background: #000d14; padding: 6px;")
        footer.setFixedHeight(24)
        layout.addWidget(footer)

        self._overlay = None
        self._muted = False
        self.muted = False
        self.on_text_command = None

        self._check_config()
        self._clock = QTimer()
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)

    def _tick_clock(self):
        pass

    def _check_config(self):
        config_path = Path(__file__).parent / "config" / "api_keys.json"
        if not config_path.exists() or "YOUR_API_KEY" in config_path.read_text():
            self._show_setup()
            return False
        return True

    def _show_setup(self):
        self._overlay = SetupOverlay()
        self._overlay.done = lambda key: self.write_log(f"SYS: API key configured")
        self._overlay.setFixedSize(420, 300)
        self._overlay.move(
            (self.root.width() - 420) // 2,
            (self.root.height() - 300) // 2
        )
        self._overlay.show()

    def wait_for_api_key(self):
        if self._overlay and self._overlay.isVisible():
            self.app.exec()

    def write_log(self, text):
        self._log.append(text)
        self._log.ensureCursorVisible()

    def set_state(self, state):
        self.hud.state = state
        if state == "SPEAKING":
            self.hud.speaking = True
        elif state == "LISTENING":
            self.hud.speaking = False
            self.hud.muted = self._muted

    def _send(self):
        text = self._input.text().strip()
        if text and self.on_text_command:
            self.write_log(f"You: {text}")
            self.on_text_command(text)
            self._input.clear()

    def _toggle_mute(self):
        self._muted = not self._muted
        self.muted = self._muted
        self.hud.muted = self._muted
        self._mute_btn.setText("UNMUTE" if self._muted else "MUTE")
        self.write_log(f"SYS: {'Muted' if self._muted else 'Unmuted'}")

    def start(self):
        self.root.show()
        self.app.exec()