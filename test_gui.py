#!/usr/bin/env python3
"""
최소한의 PySide6 GUI 테스트
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

def test_gui():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Test")
    window.setFixedSize(300, 200)

    layout = QVBoxLayout()

    label = QLabel("Test Label")
    button = QPushButton("Test Button")

    layout.addWidget(label)
    layout.addWidget(button)

    window.setLayout(layout)
    window.show()

    return app.exec()

if __name__ == "__main__":
    test_gui()