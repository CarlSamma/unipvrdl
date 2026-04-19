"""
Panopto Video Downloader - CLI and GUI Application
--------------------------------------------------
- Requires: yt-dlp and PyQt6 installed
- CLI Usage: python app.py --url VIDEO_URL --cookies COOKIES_PATH
- GUI Usage: python app.py (no arguments)
- Audio Extraction: Extract audio from MP4 files

Install dependencies:
- pip install yt-dlp PyQt6
"""
import argparse
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

# GUI imports
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QCheckBox,
                                 QHBoxLayout, QLabel, QLineEdit, QPushButton,
                                 QFileDialog, QProgressBar, QTextEdit, QMessageBox, QTabWidget, QGroupBox, QFrame)
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QPalette, QColor
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Subtitle extractor import
try:
    from sottotitoliextractor.panopto_extractor import PanoptoSubtitleExtractor
    SUBTITLE_EXTRACTOR_AVAILABLE = True
except ImportError:
    SUBTITLE_EXTRACTOR_AVAILABLE = False

class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, cookies_path, output_name, yt_dlp_path, download_location=None):
        super().__init__()
        self.url = url
        self.cookies_path = cookies_path
        self.output_name = output_name
        self.yt_dlp_path = yt_dlp_path
        self.download_location = download_location

    def run(self):
        try:
            yt_dlp_cmd = self.yt_dlp_path or self.find_yt_dlp()
            if not yt_dlp_cmd:
                self.finished.emit(False, 'yt-dlp not found. Install with "pip install yt-dlp"')
                return

            out_tpl = self.output_name or '%(title)s.%(ext)s'
            
            # Build command with download location if specified
            command = [yt_dlp_cmd, '--cookies', self.cookies_path]
            
            # Add download location if specified
            if self.download_location:
                command.extend(['-P', self.download_location])
                self.progress.emit(f'Downloading to: {self.download_location}')
            
            command.extend([self.url, '-o', out_tpl])

            self.progress.emit(f'Running: {" ".join(map(str, command))}')

            # Run the command and capture output
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress.emit(output.strip())

            rc = process.poll()
            if rc == 0:
                success_message = 'Download completed successfully!'
                if self.download_location:
                    success_message += f' File saved to: {self.download_location}'
                self.finished.emit(True, success_message)
            else:
                self.finished.emit(False, f'Download failed with exit code {rc}')

        except Exception as e:
            self.finished.emit(False, f'Error: {str(e)}')

    def find_yt_dlp(self):
        # Try to find yt-dlp in PATH
        yt_dlp_cmd = shutil.which('yt-dlp')
        if yt_dlp_cmd:
            return yt_dlp_cmd

        # On Windows, try same dir as script
        dlp_exe = os.path.join(os.path.dirname(__file__), 'yt-dlp.exe')
        if os.path.exists(dlp_exe):
            return dlp_exe

        # Try user local packages Scripts directory
        try:
            import site
            user_site = site.getusersitepackages()
            scripts_dir = os.path.join(os.path.dirname(user_site), 'Scripts')
            dlp_exe = os.path.join(scripts_dir, 'yt-dlp.exe')
            if os.path.exists(dlp_exe):
                return dlp_exe
        except:
            pass

        return None


class AudioExtractionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, video_path, output_path=None):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path

    def run(self):
        try:
            if not os.path.exists(self.video_path):
                self.finished.emit(False, f'Video file not found: {self.video_path}')
                return

            # Generate output filename if not provided
            if not self.output_path:
                base_name = os.path.splitext(self.video_path)[0]
                self.output_path = f"{base_name}_audio.mp3"
            else:
                # If output path is provided but doesn't include directory, use video file's directory
                if not os.path.dirname(self.output_path):
                    video_dir = os.path.dirname(self.video_path)
                    self.output_path = os.path.join(video_dir, self.output_path)

            self.progress.emit(f'Loading video file: {self.video_path}')
            
            # Import moviepy here to avoid GUI import issues
            try:
                from moviepy import VideoFileClip
            except ImportError:
                self.finished.emit(False, 'moviepy not installed. Install with: pip install moviepy')
                return

            # Extract audio using moviepy
            self.progress.emit('Extracting audio from video...')
            video_clip = VideoFileClip(self.video_path)
            audio_clip = video_clip.audio
            
            self.progress.emit(f'Saving audio to: {self.output_path}')
            audio_clip.write_audiofile(
                self.output_path
            )
            
            # Close the clips to free resources
            audio_clip.close()
            video_clip.close()
            
            self.finished.emit(True, f'Audio extracted successfully to: {self.output_path}')

        except Exception as e:
            self.finished.emit(False, f'Error during audio extraction: {str(e)}')

class SharepointDownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, cookies_path, output_path, progress_callback=None):
        super().__init__()
        self.url = url
        self.cookies_path = cookies_path
        self.output_path = output_path
        self.progress_callback = progress_callback

    def run(self):
        try:
            self.progress.emit(f'Starting SharePoint download with yt-dlp...')
            self.progress.emit(f'URL: {self.url}')
            self.progress.emit(f'Output: {self.output_path}')
            
            # Use yt-dlp for SharePoint downloads - it's more robust for authentication
            yt_dlp_cmd = self.find_yt_dlp()
            if not yt_dlp_cmd:
                raise Exception('yt-dlp not found. Install with "pip install yt-dlp"')
            
            out_tpl = self.output_path
            
            command = [
                yt_dlp_cmd,
                '--cookies', self.cookies_path,
                '--no-check-certificates',
                '--format', 'dash-v720p/dash-v480p/dash-v240p/best',
                self.url,
                '-o', out_tpl
            ]
            
            self.progress.emit(f'Running: {" ".join(command)}')
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress.emit(output.strip())
            
            rc = process.poll()
            if rc == 0:
                self.finished.emit(True, f'Download completed: {self.output_path}')
            else:
                self.finished.emit(False, f'Download failed with exit code {rc}')
                
        except Exception as e:
            self.finished.emit(False, f'Error: {str(e)}')

    def find_yt_dlp(self):
        yt_dlp_cmd = shutil.which('yt-dlp')
        if yt_dlp_cmd:
            return yt_dlp_cmd
        dlp_exe = os.path.join(os.path.dirname(__file__), 'yt-dlp.exe')
        if os.path.exists(dlp_exe):
            return dlp_exe
        try:
            import site
            user_site = site.getusersitepackages()
            scripts_dir = os.path.join(os.path.dirname(user_site), 'Scripts')
            dlp_exe = os.path.join(scripts_dir, 'yt-dlp.exe')
            if os.path.exists(dlp_exe):
                return dlp_exe
        except:
            pass
        return None


class SubtitleExtractionWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, output_dir, formats, cookies_path=None, headless=True):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.formats = formats
        self.cookies_path = cookies_path
        self.headless = headless

    def run(self):
        try:
            if not SUBTITLE_EXTRACTOR_AVAILABLE:
                self.finished.emit(False, 'Subtitle extractor module not found.')
                return
            
            if not self.formats:
                self.finished.emit(False, 'No output format selected for subtitles.')
                return

            extractor = PanoptoSubtitleExtractor(
                url=self.url,
                output_dir=self.output_dir,
                headless=self.headless,
                cookies_path=self.cookies_path,
                progress_callback=self.progress.emit
            )

            if extractor.extract():
                if 'json' in self.formats:
                    extractor.save_json()
                if 'csv' in self.formats:
                    extractor.save_csv()
                if 'txt' in self.formats:
                    extractor.save_txt()
                if 'srt' in self.formats:
                    extractor.save_srt()
                self.finished.emit(True, f'Subtitle extraction complete! Files saved in: {self.output_dir}')
            else:
                self.finished.emit(False, 'Subtitle extraction failed. See status for details.')
        except Exception as e:
            self.finished.emit(False, f'Error during subtitle extraction: {str(e)}')

class PanoptoDownloaderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Panoptoextractor_CC')
        self.setGeometry(100, 100, 700, 750)

        # Set modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 12px 24px;
                margin-right: 4px;
                background-color: #e0e0e0;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #45a049;
                color: white;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton#browseBtn {
                background-color: #2196F3;
            }
            QPushButton#browseBtn:hover {
                background-color: #1976D2;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: #fafafa;
            }
            QGroupBox {
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Create Tab Widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create Panopto Tab
        self.create_panopto_tab()

        # Create SharePoint Tab
        self.create_sharepoint_tab()

        # Common status text area (at bottom)
        status_label = QLabel('Status:')
        status_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        main_layout.addWidget(status_label)
        self.status_text = QTextEdit()
        self.status_text.setMinimumHeight(100)
        self.status_text.setReadOnly(True)
        main_layout.addWidget(self.status_text)

        # Initial status
        self.status_text.append('Ready. Select a tab and enter your details.')

    def create_panopto_tab(self):
        """Create the Panopto Download tab content"""
        panopto_widget = QWidget()
        layout = QVBoxLayout(panopto_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # URL input
        url_layout = QVBoxLayout()
        url_label = QLabel('Panopto Viewer URL:')
        url_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('https://unimi.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=...')
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Cookies file selection
        cookies_layout = QVBoxLayout()
        cookies_label = QLabel('Cookies File (Netscape format):')
        cookies_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        cookies_file_layout = QHBoxLayout()
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText('Select cookies.txt file...')
        self.cookies_input.setReadOnly(True)
        browse_btn = QPushButton('Browse...')
        browse_btn.setObjectName('browseBtn')
        browse_btn.clicked.connect(self.browse_cookies)
        cookies_file_layout.addWidget(self.cookies_input)
        cookies_file_layout.addWidget(browse_btn)
        cookies_layout.addWidget(cookies_label)
        cookies_layout.addLayout(cookies_file_layout)
        layout.addLayout(cookies_layout)

        # Download location selection
        download_location_layout = QVBoxLayout()
        download_location_label = QLabel('Download Location:')
        download_location_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        download_location_file_layout = QHBoxLayout()
        self.download_location_input = QLineEdit()
        self.download_location_input.setPlaceholderText('Select download directory...')
        self.download_location_input.setReadOnly(True)
        download_location_browse_btn = QPushButton('Browse...')
        download_location_browse_btn.setObjectName('browseBtn')
        download_location_browse_btn.clicked.connect(self.browse_download_location)
        download_location_file_layout.addWidget(self.download_location_input)
        download_location_file_layout.addWidget(download_location_browse_btn)
        download_location_layout.addWidget(download_location_label)
        download_location_layout.addLayout(download_location_file_layout)
        layout.addLayout(download_location_layout)

        # Output filename (optional)
        output_layout = QVBoxLayout()
        output_label = QLabel('Output Filename (optional):')
        output_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText('Leave empty for auto-generated name')
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_input)
        layout.addLayout(output_layout)

        # Download button
        self.download_btn = QPushButton('⬇ Download Video')
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setMinimumHeight(45)
        layout.addWidget(self.download_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Add separator
        layout.addWidget(HSeparator())

        # Audio extraction section
        audio_group = QGroupBox('Audio Extraction')
        audio_layout = QVBoxLayout(audio_group)

        video_file_layout = QHBoxLayout()
        video_label = QLabel('Video File:')
        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText('Select video file for audio extraction...')
        self.video_input.setReadOnly(True)
        video_browse_btn = QPushButton('Browse...')
        video_browse_btn.setObjectName('browseBtn')
        video_browse_btn.clicked.connect(self.browse_video)
        video_file_layout.addWidget(video_label)
        video_file_layout.addWidget(self.video_input)
        video_file_layout.addWidget(video_browse_btn)
        audio_layout.addLayout(video_file_layout)

        audio_output_layout = QVBoxLayout()
        audio_output_label = QLabel('Audio Output Filename (optional):')
        self.audio_output_input = QLineEdit()
        self.audio_output_input.setPlaceholderText('Leave empty for auto-generated name')
        audio_output_layout.addWidget(audio_output_label)
        audio_output_layout.addWidget(self.audio_output_input)
        audio_layout.addLayout(audio_output_layout)

        self.extract_audio_btn = QPushButton('🎵 Extract Audio')
        self.extract_audio_btn.clicked.connect(self.start_audio_extraction)
        self.extract_audio_btn.setMinimumHeight(40)
        audio_layout.addWidget(self.extract_audio_btn)

        layout.addWidget(audio_group)

        # Subtitle Extraction Section
        if SUBTITLE_EXTRACTOR_AVAILABLE:
            subtitle_group = QGroupBox('Subtitle Extraction')
            subtitle_layout = QVBoxLayout(subtitle_group)

            info_label = QLabel("Extract subtitles into <b>.srt</b> file.")
            info_label.setFont(QFont('Arial', 9))
            subtitle_layout.addWidget(info_label)

            self.extract_subtitle_btn = QPushButton('📝 Extract Subtitles')
            self.extract_subtitle_btn.clicked.connect(self.start_subtitle_extraction)
            self.extract_subtitle_btn.setMinimumHeight(40)
            subtitle_layout.addWidget(self.extract_subtitle_btn)

            layout.addWidget(subtitle_group)
        else:
            subtitle_warning = QLabel('⚠ Subtitle extractor module not found.')
            layout.addWidget(subtitle_warning)

        layout.addStretch()
        self.tab_widget.addTab(panopto_widget, '🎬 Panopto Download')

    def create_sharepoint_tab(self):
        """Create the SharePoint UniPR tab content"""
        sharepoint_widget = QWidget()
        layout = QVBoxLayout(sharepoint_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Info label
        info_label = QLabel('Download videos directly from SharePoint UniPR. Use the cookies exported from your Microsoft 365 session.')
        info_label.setFont(QFont('Arial', 9))
        info_label.setStyleSheet('color: #666; background-color: #fffde7; padding: 8px; border-radius: 5px;')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # SharePoint URL input
        sp_url_layout = QVBoxLayout()
        sp_url_label = QLabel('SharePoint Video URL:')
        sp_url_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.sp_url_input = QLineEdit()
        self.sp_url_input.setPlaceholderText('https://univpr.sharepoint.com/.../video.mp4')
        sp_url_layout.addWidget(sp_url_label)
        sp_url_layout.addWidget(self.sp_url_input)
        layout.addLayout(sp_url_layout)

        # SharePoint cookie file
        sp_cookie_layout = QVBoxLayout()
        sp_cookie_label = QLabel('Cookies File (Microsoft 365):')
        sp_cookie_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        sp_cookie_row = QHBoxLayout()
        self.sp_cookie_input = QLineEdit()
        self.sp_cookie_input.setPlaceholderText('Select cookies.txt file...')
        self.sp_cookie_input.setReadOnly(True)
        sp_cookie_browse_btn = QPushButton('Browse...')
        sp_cookie_browse_btn.setObjectName('browseBtn')
        sp_cookie_browse_btn.clicked.connect(self.browse_sp_cookie)
        sp_cookie_row.addWidget(self.sp_cookie_input)
        sp_cookie_row.addWidget(sp_cookie_browse_btn)
        sp_cookie_layout.addWidget(sp_cookie_label)
        sp_cookie_layout.addLayout(sp_cookie_row)
        layout.addLayout(sp_cookie_layout)

        # SharePoint output directory
        sp_out_layout = QVBoxLayout()
        sp_out_label = QLabel('Output Directory:')
        sp_out_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        sp_out_row = QHBoxLayout()
        self.sp_out_input = QLineEdit()
        self.sp_out_input.setPlaceholderText('Select output directory...')
        self.sp_out_input.setReadOnly(True)
        sp_out_browse_btn = QPushButton('Browse...')
        sp_out_browse_btn.setObjectName('browseBtn')
        sp_out_browse_btn.clicked.connect(self.browse_sp_output)
        sp_out_row.addWidget(self.sp_out_input)
        sp_out_row.addWidget(sp_out_browse_btn)
        sp_out_layout.addWidget(sp_out_label)
        sp_out_layout.addLayout(sp_out_row)
        layout.addLayout(sp_out_layout)

        # SharePoint download button
        self.sp_download_btn = QPushButton('⬇ Download from SharePoint')
        self.sp_download_btn.clicked.connect(self.start_sp_download)
        self.sp_download_btn.setMinimumHeight(50)
        self.sp_download_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        layout.addWidget(self.sp_download_btn)

        # Note about cookie format
        cookie_note = QLabel('ℹ Cookie format: Netscape (export from "Get cookies.txt LOCALLY" extension)')
        cookie_note.setFont(QFont('Arial', 8))
        cookie_note.setStyleSheet('color: #888;')
        layout.addWidget(cookie_note)

        layout.addStretch()
        self.tab_widget.addTab(sharepoint_widget, '📁 SharePoint UniPR')

    def update_progress(self, message):
        self.status_text.append(message)
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_cookies(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Select Cookies File', '', 'Text files (*.txt);;All files (*.*)'
        )
        if file_path:
            self.cookies_input.setText(file_path)

    def browse_download_location(self):
        directory = QFileDialog.getExistingDirectory(
            self, 'Select Download Directory', ''
        )
        if directory:
            self.download_location_input.setText(directory)

    def start_download(self):
        url = self.url_input.text().strip()
        cookies_path = self.cookies_input.text().strip()
        output_name = self.output_input.text().strip()
        download_location = self.download_location_input.text().strip()

        if not url:
            QMessageBox.warning(self, 'Error', 'Please enter a Panopto URL.')
            return

        if not cookies_path:
            QMessageBox.warning(self, 'Error', 'Please select a cookies file.')
            return

        if not os.path.exists(cookies_path):
            QMessageBox.warning(self, 'Error', 'Cookies file does not exist.')
            return

        self.download_btn.setEnabled(False)
        self.download_btn.setText('Downloading...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_text.clear()
        self.status_text.append('Starting download...')

        self.worker = DownloadWorker(url, cookies_path, output_name, '', download_location if download_location else None)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.start()

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Select Video File', '', 'Video files (*.mp4 *.avi *.mkv *.mov);;All files (*.*)'
        )
        if file_path:
            self.video_input.setText(file_path)

    def start_audio_extraction(self):
        video_path = self.video_input.text().strip()
        audio_output = self.audio_output_input.text().strip()

        if not video_path:
            QMessageBox.warning(self, 'Error', 'Please select a video file.')
            return

        if not os.path.exists(video_path):
            QMessageBox.warning(self, 'Error', 'Video file does not exist.')
            return

        self.extract_audio_btn.setEnabled(False)
        self.extract_audio_btn.setText('Extracting Audio...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_text.clear()
        self.status_text.append('Starting audio extraction...')

        self.audio_worker = AudioExtractionWorker(video_path, audio_output if audio_output else None)
        self.audio_worker.progress.connect(self.update_progress)
        self.audio_worker.finished.connect(self.audio_extraction_finished)
        self.audio_worker.start()

    def start_subtitle_extraction(self):
        url = self.url_input.text().strip()
        download_location = self.download_location_input.text().strip() or '.'
        cookies_path = self.cookies_input.text().strip()

        if not url:
            QMessageBox.warning(self, 'Error', 'Please enter a Panopto URL for subtitle extraction.')
            return

        selected_formats = ['srt']
        self.extract_subtitle_btn.setEnabled(False)
        self.extract_subtitle_btn.setText('Extracting Subtitles...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_text.clear()
        self.status_text.append('Starting subtitle extraction...')

        self.subtitle_worker = SubtitleExtractionWorker(
            url, 
            download_location, 
            selected_formats,
            cookies_path if cookies_path else None
        )
        self.subtitle_worker.progress.connect(self.update_progress)
        self.subtitle_worker.finished.connect(self.subtitle_extraction_finished)
        self.subtitle_worker.start()

    def subtitle_extraction_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.extract_subtitle_btn.setEnabled(True)
        self.extract_subtitle_btn.setText('📝 Extract Subtitles')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')

    def audio_extraction_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.extract_audio_btn.setEnabled(True)
        self.extract_audio_btn.setText('🎵 Extract Audio')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')

    def download_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.download_btn.setText('⬇ Download Video')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')

    def browse_sp_cookie(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Select Cookies File', '', 'Text files (*.txt);;All files (*.*)'
        )
        if file_path:
            self.sp_cookie_input.setText(file_path)

    def browse_sp_output(self):
        directory = QFileDialog.getExistingDirectory(
            self, 'Select Output Directory', ''
        )
        if directory:
            self.sp_out_input.setText(directory)

    def start_sp_download(self):
        url = self.sp_url_input.text().strip()
        cookies_path = self.sp_cookie_input.text().strip()
        out_dir = self.sp_out_input.text().strip() or '.'

        if not url:
            QMessageBox.warning(self, 'Error', 'Please enter a SharePoint URL.')
            return

        if not cookies_path:
            QMessageBox.warning(self, 'Error', 'Please select a cookies file.')
            return

        if not os.path.exists(cookies_path):
            QMessageBox.warning(self, 'Error', 'Cookies file does not exist.')
            return

        filename = url.split("/")[-1].split("?")[0]
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        output_path = os.path.join(out_dir, filename)

        self.sp_download_btn.setEnabled(False)
        self.sp_download_btn.setText('Downloading...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_text.clear()
        self.status_text.append('Starting SharePoint download...')

        self.sp_worker = SharepointDownloadWorker(
            url, cookies_path, output_path,
            progress_callback=self.sp_progress
        )
        self.sp_worker.progress.connect(self.update_progress)
        self.sp_worker.finished.connect(self.sp_download_finished)
        self.sp_worker.start()

    def sp_progress(self, value):
        self.progress_bar.setValue(value)

    def sp_download_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.sp_download_btn.setEnabled(True)
        self.sp_download_btn.setText('⬇ Download from SharePoint')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')


class HSeparator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet('background-color: #ddd; margin: 5px 0;')


def cli_main():
    parser = argparse.ArgumentParser(description='Panopto Video Downloader & Audio Extractor')
    parser.add_argument('--url', help='Panopto Viewer URL')
    parser.add_argument('--cookies', help='Path to cookies.txt (Netscape format)')
    parser.add_argument('--output', default='', help='(Optional) Output file name')
    parser.add_argument('--yt-dlp-path', default='', help='(Optional) Path to yt-dlp or yt-dlp.exe if not in PATH')
    
    # Audio extraction arguments
    parser.add_argument('--extract-audio', help='Extract audio from video file')
    parser.add_argument('--audio-output', default='', help='(Optional) Audio output file name')
    
    # Subtitle extraction arguments
    parser.add_argument('--extract-subtitles', action='store_true', 
                        help='Extract subtitles from Panopto video')
    parser.add_argument('--subtitle-formats', nargs='+', 
                        default=['srt'], choices=['srt', 'json', 'csv', 'txt'],
                        help='Subtitle output formats (default: srt)')
    parser.add_argument('--output-dir', default='./output',
                        help='Output directory for subtitles')
    
    # SharePoint UniPR arguments
    parser.add_argument('--sharepoint-url', 
                        help='SharePoint direct MP4 URL (UniPR)')
    parser.add_argument('--site-url', 
                        help='SharePoint site URL (for API resolution)')
    parser.add_argument('--server-relative-path',
                        help='ServerRelativePath of file on SharePoint')
    
    args = parser.parse_args()

    # SharePoint download mode
    if args.sharepoint_url:
        if not args.cookies:
            print('ERROR: --cookies required for SharePoint download')
            sys.exit(1)
        
        # Use yt-dlp for SharePoint - it's more robust for Microsoft 365 authentication
        yt_dlp_cmd = shutil.which('yt-dlp')
        if not yt_dlp_cmd:
            dlp_exe = os.path.join(os.path.dirname(__file__), 'yt-dlp.exe')
            if os.path.exists(dlp_exe):
                yt_dlp_cmd = dlp_exe
        
        if not yt_dlp_cmd:
            print('ERROR: yt-dlp not found. Install with "pip install yt-dlp"')
            sys.exit(1)
        
        output_path = args.output or os.path.basename(args.sharepoint_url.split("?")[0])
        print(f'Downloading from SharePoint: {args.sharepoint_url}')
        print(f'Output: {output_path}')
        
        command = [
            yt_dlp_cmd,
            '--cookies', args.cookies,
            '--no-check-certificates',
            '--format', 'dash-v720p/dash-v480p/dash-v240p/best',
            args.sharepoint_url,
            '-o', output_path
        ]
        
        print(f'Running: {" ".join(command)}')
        try:
            subprocess.run(command, check=True)
            print(f'\n✅ Download complete! Saved to: {output_path}')
        except subprocess.CalledProcessError as e:
            print(f'\n❌ Download failed: {str(e)}')
            sys.exit(2)
        
        return

    # Subtitle extraction mode
    if args.extract_subtitles:
        if not SUBTITLE_EXTRACTOR_AVAILABLE:
            print('ERROR: Subtitle extractor module not available')
            print('Make sure sottotitoliextractor/panopto_extractor.py exists')
            sys.exit(1)
        
        if not args.url:
            print('ERROR: --url required for subtitle extraction')
            sys.exit(1)
        
        print(f'Extracting subtitles from: {args.url}')
        print(f'Output formats: {", ".join(args.subtitle_formats)}')
        print(f'Output directory: {args.output_dir}')
        
        try:
            # Supporto cookie per video protetti (usa lo stesso file del download)
            cookies_path = args.cookies if args.cookies and os.path.exists(args.cookies) else None
            
            extractor = PanoptoSubtitleExtractor(
                url=args.url,
                output_dir=args.output_dir,
                cookies_path=cookies_path,
                headless=True
            )
            
            if extractor.extract():
                print('\nSaving subtitles in requested formats...')
                for fmt in args.subtitle_formats:
                    if fmt == 'srt':
                        extractor.save_srt()
                    elif fmt == 'json':
                        extractor.save_json()
                    elif fmt == 'csv':
                        extractor.save_csv()
                    elif fmt == 'txt':
                        extractor.save_txt()
                
                print(f'\n✅ Subtitle extraction complete!')
                print(f'Files saved to: {args.output_dir}')
            else:
                print('\n❌ Subtitle extraction failed. See output above for details.')
                sys.exit(2)
        except Exception as e:
            print(f'\n❌ Error during subtitle extraction: {str(e)}')
            sys.exit(2)
        
        return

    # Check if we're doing audio extraction or video download
    if args.extract_audio:
        # Audio extraction mode
        try:
            from moviepy import VideoFileClip
        except ImportError:
            print('ERROR: moviepy not installed. Install with: pip install moviepy')
            sys.exit(1)

        video_path = args.extract_audio
        if not os.path.exists(video_path):
            print(f'ERROR: Video file not found: {video_path}')
            sys.exit(1)

        # Generate output filename if not provided
        if not args.audio_output:
            base_name = os.path.splitext(video_path)[0]
            audio_output = f"{base_name}_audio.mp3"
        else:
            audio_output = args.audio_output

        print(f'Loading video file: {video_path}')
        print('Extracting audio from video...')
        
        try:
            # Extract audio using moviepy
            video_clip = VideoFileClip(video_path)
            audio_clip = video_clip.audio
            
            print(f'Saving audio to: {audio_output}')
            audio_clip.write_audiofile(
                audio_output
            )
            
            # Close the clips to free resources
            audio_clip.close()
            video_clip.close()
            
            print(f'\nAudio extraction complete! Output: {audio_output}')
        except Exception as e:
            print(f'\nAudio extraction failed! Error: {str(e)}')
            sys.exit(2)
        return

    # Video download mode (original functionality)
    if not args.url or not args.cookies:
        print('ERROR: For video download, both --url and --cookies are required.')
        print('For audio extraction, use --extract-audio <video_file>')
        sys.exit(1)

    yt_dlp_cmd = args.yt_dlp_path or shutil.which('yt-dlp')
    if not yt_dlp_cmd:
        # On Windows, try same dir as script
        dlp_exe = os.path.join(os.path.dirname(__file__), 'yt-dlp.exe')
        if os.path.exists(dlp_exe):
            yt_dlp_cmd = dlp_exe
    if not yt_dlp_cmd:
        # Try user local packages Scripts directory
        try:
            import site
            user_site = site.getusersitepackages()
            scripts_dir = os.path.join(os.path.dirname(user_site), 'Scripts')
            dlp_exe = os.path.join(scripts_dir, 'yt-dlp.exe')
            if os.path.exists(dlp_exe):
                yt_dlp_cmd = dlp_exe
        except:
            pass

    if not yt_dlp_cmd:
        print('ERROR: yt-dlp not found. Install with "pip install yt-dlp" or place yt-dlp.exe in PATH/script dir.')
        sys.exit(1)

    out_tpl = args.output or '%(title)s.%(ext)s'
    command = [
        yt_dlp_cmd,
        '--cookies', args.cookies,
        args.url,
        '-o', out_tpl
    ]

    print(f'Running: {" ".join(map(str, command))}')
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print('\nDownload failed!')
        print(e)
        sys.exit(2)
    print('\nDownload complete!')

def main():
    # Check if arguments provided - if yes, use CLI mode
    if len(sys.argv) > 1:
        cli_main()
    else:
        # GUI mode
        if not GUI_AVAILABLE:
            print('PyQt6 not installed. Install with: pip install PyQt6')
            print('Or use CLI mode: python app.py --url <URL> --cookies <COOKIES_FILE>')
            sys.exit(1)

        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Modern style

        # Set application properties
        app.setApplicationName('Panopto Video Downloader')
        app.setApplicationVersion('1.0')
        app.setOrganizationName('Panopto Downloader')

        window = PanoptoDownloaderGUI()
        window.show()
        sys.exit(app.exec())

if __name__ == '__main__':
    main()
