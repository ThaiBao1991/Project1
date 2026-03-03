import sys
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog, QTextBrowser)
from PyQt5.QtCore import Qt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from pathlib import Path
import re

class ComicDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.config_file = "config.json"
        self.load_config()

    def initUI(self):
        self.setWindowTitle("Comic Downloader")
        self.setGeometry(100, 100, 800, 600)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Website URL
        layout.addWidget(QLabel("Website URL (e.g., https://nettruyen3q.net):"))
        self.website_url = QLineEdit()
        layout.addWidget(self.website_url)

        # Comic URL
        layout.addWidget(QLabel("Comic URL (e.g., https://nettruyen3q.net/lop-hoc-bi-mat-secret-class):"))
        self.comic_url = QLineEdit()
        layout.addWidget(self.comic_url)

        # Chapter script
        layout.addWidget(QLabel("JavaScript for Chapter Links:"))
        self.chapter_script = QTextEdit()
        self.chapter_script.setPlaceholderText("Enter JavaScript to extract chapter links...")
        layout.addWidget(self.chapter_script)

        # Image script
        layout.addWidget(QLabel("JavaScript for Image Links:"))
        self.image_script = QTextEdit()
        self.image_script.setPlaceholderText("Enter JavaScript to extract image links...")
        layout.addWidget(self.image_script)

        # Download directory
        dir_layout = QHBoxLayout()
        layout.addWidget(QLabel("Download Directory:"))
        self.download_dir = QLineEdit()
        dir_layout.addWidget(self.download_dir)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        load_btn = QPushButton("Load Config")
        load_btn.clicked.connect(self.load_config)
        btn_layout.addWidget(load_btn)
        download_btn = QPushButton("Download Comic")
        download_btn.clicked.connect(self.download_comic)
        btn_layout.addWidget(download_btn)
        layout.addLayout(btn_layout)

        # Status log
        self.status_log = QTextBrowser()
        self.status_log.setReadOnly(True)
        layout.addWidget(self.status_log)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_dir.setText(directory)

    def save_config(self):
        config = {
            "website_url": self.website_url.text(),
            "comic_url": self.comic_url.text(),
            "chapter_script": self.chapter_script.toPlainText(),
            "image_script": self.image_script.toPlainText(),
            "download_dir": self.download_dir.text()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        self.status_log.append("Configuration saved.")

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.website_url.setText(config.get("website_url", ""))
                self.comic_url.setText(config.get("comic_url", ""))
                self.chapter_script.setPlainText(config.get("chapter_script", ""))
                self.image_script.setPlainText(config.get("image_script", ""))
                self.download_dir.setText(config.get("download_dir", ""))
                self.status_log.append("Configuration loaded.")
        else:
            self.status_log.append("No configuration file found.")

    def get_existing_chapters(self, comic_dir):
        """Return a list of existing chapter folders and the highest chapter number."""
        chapter_dirs = [d for d in comic_dir.iterdir() if d.is_dir()]
        chapter_numbers = []
        for d in chapter_dirs:
            # Extract number from folder name (e.g., Chapter_1 -> 1, chapter-2 -> 2)
            match = re.search(r'(\d+)', d.name)
            if match:
                chapter_numbers.append(int(match.group(1)))
        return chapter_dirs, max(chapter_numbers) if chapter_numbers else 0

    def download_comic(self):
        website_url = self.website_url.text().strip()
        comic_url = self.comic_url.text().strip()
        chapter_script = self.chapter_script.toPlainText().strip()
        image_script = self.image_script.toPlainText().strip()
        download_dir = self.download_dir.text().strip()

        if not all([website_url, comic_url, chapter_script, image_script, download_dir]):
            self.status_log.append("Error: All fields must be filled.")
            return

        # Extract comic title from URL
        comic_title = comic_url.split('/')[-1]
        if not comic_title:
            self.status_log.append("Error: Invalid comic URL.")
            return

        # Create base directory for the comic
        comic_dir = Path(download_dir) / comic_title
        comic_dir.mkdir(parents=True, exist_ok=True)

        # Check existing chapters
        _, last_chapter_num = self.get_existing_chapters(comic_dir)
        start_chapter = max(0, last_chapter_num - 1)  # Start from last chapter - 1
        self.status_log.append(f"Found chapters up to Chapter {last_chapter_num}. Starting from Chapter {start_chapter}.")

        # Set up Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Get chapter links
            self.status_log.append(f"Fetching chapters from {comic_url}...")
            driver.get(comic_url)
            chapter_links = driver.execute_script(chapter_script)
            if not chapter_links:
                self.status_log.append("Error: No chapters found.")
                return

            # Reverse if chapters are newest to oldest
            chapter_links = chapter_links[::-1]  # Adjust based on website order

            # Process chapters from start_chapter onward
            for idx, chapter_url in enumerate(chapter_links):
                # Derive chapter name
                chapter_url = urljoin(website_url, chapter_url)
                chapter_name = re.sub(r'[^\w\-]', '_', chapter_url.split('/')[-1]) or f"Chapter_{idx + 1}"
                chapter_num_match = re.search(r'(\d+)', chapter_name)
                chapter_num = int(chapter_num_match.group(1)) if chapter_num_match else idx + 1

                # Skip chapters before start_chapter
                if chapter_num < start_chapter:
                    self.status_log.append(f"Skipping Chapter {chapter_num} (already processed).")
                    continue

                chapter_dir = comic_dir / chapter_name
                chapter_dir.mkdir(exist_ok=True)

                self.status_log.append(f"Processing {chapter_name}...")
                driver.get(chapter_url)
                image_urls = driver.execute_script(image_script)
                if not image_urls:
                    self.status_log.append(f"No images found for {chapter_name}.")
                    continue

                for img_idx, img_url in enumerate(image_urls):
                    img_url = urljoin(website_url, img_url)
                    img_path = chapter_dir / f"image_{img_idx + 1}.jpg"
                    if img_path.exists():
                        self.status_log.append(f"Skipping existing image: {img_path.name}")
                        continue

                    try:
                        response = requests.get(img_url, stream=True)
                        response.raise_for_status()
                        with open(img_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        self.status_log.append(f"Downloaded {img_path.name}")
                    except Exception as e:
                        self.status_log.append(f"Error downloading {img_url}: {str(e)}")

        except Exception as e:
            self.status_log.append(f"Error: {str(e)}")
        finally:
            driver.quit()
            self.status_log.append("Download completed.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ComicDownloader()
    window.show()
    sys.exit(app.exec_())