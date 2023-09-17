import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        self.output_text = QTextEdit()
        layout.addWidget(self.output_text)

        button1 = QPushButton("Button 1")
        button2 = QPushButton("Button 2")
        button3 = QPushButton("Button 3")

        button1.clicked.connect(lambda: self.on_button_click("Button 1 clicked"))
        button2.clicked.connect(lambda: self.on_button_click("Button 2 clicked"))
        button3.clicked.connect(lambda: self.on_button_click("Button 3 clicked"))

        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)

    def on_button_click(self, message):
        self.output_text.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
