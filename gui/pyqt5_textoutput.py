import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel

class AutoExpandGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("日本語対応の自動拡張GUI")
        self.setGeometry(100, 100, 500, 400)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.text_input_label = QLabel("ここにテキストを入力してください：", self)
        layout.addWidget(self.text_input_label)

        self.text_input = QTextEdit("これは複数行の入力です。", self)
        layout.addWidget(self.text_input)

        submit_button = QPushButton("送信", self)
        submit_button.clicked.connect(self.on_submit)
        layout.addWidget(submit_button)

        self.output_label = QLabel("出力：", self)
        layout.addWidget(self.output_label)

        self.output = QTextEdit(self)
        layout.addWidget(self.output)

    def on_submit(self):
        input_text = self.text_input.toPlainText()
        self.output.append("入力内容：")
        self.output.append(input_text)
        self.output.append("-" * 40)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoExpandGUI()
    window.show()
    sys.exit(app.exec_())

