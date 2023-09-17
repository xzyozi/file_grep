import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog
import sys

def read_folder_contents(folder_path):
    if not folder_path:
        return "Please enter a folder path."

    try:
        files = os.listdir(folder_path)
        return "Folder contents:\n" + "\n".join(files)
    except FileNotFoundError:
        return "Folder not found."
    except Exception as e:
        return "Error occurred: " + str(e)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Read Folder Contents")

        # Create widgets
        self.folder_path_input = QLineEdit()
        self.folder_path_input.setPlaceholderText("Enter Folder Path")
        self.folder_browse_button = QPushButton("Browse")
        self.folder_browse_button.clicked.connect(self.browse_folder)
        self.read_folder_button = QPushButton("Read Folder")
        self.read_folder_button.clicked.connect(self.read_folder)
        self.output_label = QLabel()

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.folder_path_input)
        layout.addWidget(self.folder_browse_button)
        layout.addWidget(self.read_folder_button)
        layout.addWidget(self.output_label)

        self.setLayout(layout)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path_input.setText(folder_path)

    def read_folder(self):
        folder_path = self.folder_path_input.text()
        result = read_folder_contents(folder_path)
        self.output_label.setText(result)
        print(result)  # Print the result to the terminal

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
