import sys
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QPushButton, QSlider, QLabel, QStatusBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from atow import AudioServer
from atow import settings

class AudioReceiverApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("atow")
        self.setGeometry(100, 100, 700, 500)
        self.server = AudioServer()
        self.server.log_signal.connect(self.log)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 10))
        main_layout.addWidget(QLabel("Status & Logs:"))
        main_layout.addWidget(self.log_text)
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(settings.get('volume') * 100))
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.on_volume_change)
        volume_layout.addWidget(self.volume_slider, 1)
        self.volume_label = QLabel(int(settings.get('volume') * 100).__str__() + "%")
        self.volume_label.setMinimumWidth(50)
        volume_layout.addWidget(self.volume_label)
        main_layout.addLayout(volume_layout)
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("▶ Start")
        self.start_button.clicked.connect(self.start_receiving)
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("QPushButton { font-size: 12px; font-weight: bold; }")
        self.stop_button = QPushButton("■ Stop")
        self.stop_button.clicked.connect(self.stop_receiving)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setStyleSheet("QPushButton { font-size: 12px; font-weight: bold; }")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)
        central_widget.setLayout(main_layout)
        self.statusBar().showMessage("Ready")

    def on_volume_change(self, value):
        volume_factor = value / 100.0
        self.server.set_volume(volume_factor)
        self.volume_label.setText(f"{value}%")

    def log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def start_receiving(self):
        if not self.server.running:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.log_text.clear()
            threading.Thread(target=self.server.start, daemon=True).start()
            self.statusBar().showMessage("Running...")

    def stop_receiving(self):
        self.server.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Stopped")

    def closeEvent(self, event):
        new_settings = {
            'volume': self.server.volume_value
        }
        with open('settings.txt', 'w') as f:
            for key, value in new_settings.items():
                f.write(f"{key}={value}\n")
        self.server.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioReceiverApp()
    window.show()
    sys.exit(app.exec())