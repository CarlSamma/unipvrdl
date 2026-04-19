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
                                 QFileDialog, QProgressBar, QTextEdit, QMessageBox)
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
        self.setWindowTitle('Panopto Video Downloader & Audio Extractor')
        self.setGeometry(100, 100, 600, 850)

        # Set modern styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                font-size: 12px;
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
            }
        """)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

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
        self.download_btn = QPushButton('Start Download')
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setMinimumHeight(40)
        layout.addWidget(self.download_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status text area
        status_label = QLabel('Status:')
        status_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        layout.addWidget(status_label)
        self.status_text = QTextEdit()
        self.status_text.setMinimumHeight(150)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        # Audio extraction section
        audio_layout = QVBoxLayout()
        audio_label = QLabel('Audio Extraction:')
        audio_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        audio_layout.addWidget(audio_label)

        # Video file selection for audio extraction
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

        # Audio output filename (optional)
        audio_output_layout = QVBoxLayout()
        audio_output_label = QLabel('Audio Output Filename (optional):')
        audio_output_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.audio_output_input = QLineEdit()
        self.audio_output_input.setPlaceholderText('Leave empty for auto-generated name')
        audio_output_layout.addWidget(audio_output_label)
        audio_output_layout.addWidget(self.audio_output_input)
        audio_layout.addLayout(audio_output_layout)

        # Extract audio button
        self.extract_audio_btn = QPushButton('Extract Audio')
        self.extract_audio_btn.clicked.connect(self.start_audio_extraction)
        self.extract_audio_btn.setMinimumHeight(40)
        audio_layout.addWidget(self.extract_audio_btn)

        layout.addLayout(audio_layout)

        # --- Subtitle Extraction Section ---
        if SUBTITLE_EXTRACTOR_AVAILABLE:
            subtitle_layout = QVBoxLayout()
            subtitle_label = QLabel('Subtitle Extraction:')
            subtitle_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            subtitle_layout.addWidget(subtitle_label)

            # Note: The new JS-based extractor only produces SRT.
            # The format options are removed to reflect this.
            info_label = QLabel("This will extract subtitles into a <b>.srt</b> file.")
            info_label.setFont(QFont('Arial', 9))
            subtitle_layout.addWidget(info_label)


            # Extract subtitles button
            self.extract_subtitle_btn = QPushButton('Extract Subtitles')
            self.extract_subtitle_btn.clicked.connect(self.start_subtitle_extraction)
            self.extract_subtitle_btn.setMinimumHeight(40)
            subtitle_layout.addWidget(self.extract_subtitle_btn)

            layout.addLayout(subtitle_layout)
        else:
            subtitle_warning = QLabel('Subtitle extractor module not found. Please ensure `sottotitoliextractor` is available.')
            layout.addWidget(subtitle_warning)

        # Initial status
        self.status_text.append('Ready to download videos or extract audio from existing files.')

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

        # Disable download button and show progress
        self.download_btn.setEnabled(False)
        self.download_btn.setText('Downloading...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_text.clear()
        self.status_text.append('Starting download...')

        # Start download in separate thread
        self.worker = DownloadWorker(url, cookies_path, output_name, '', download_location if download_location else None)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.start()

    def update_progress(self, message):
        self.status_text.append(message)
        # Scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

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

        # Disable extract audio button and show progress
        self.extract_audio_btn.setEnabled(False)
        self.extract_audio_btn.setText('Extracting Audio...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_text.clear()
        self.status_text.append('Starting audio extraction...')

        # Start audio extraction in separate thread
        self.audio_worker = AudioExtractionWorker(video_path, audio_output if audio_output else None)
        self.audio_worker.progress.connect(self.update_progress)
        self.audio_worker.finished.connect(self.audio_extraction_finished)
        self.audio_worker.start()

    def start_subtitle_extraction(self):
        url = self.url_input.text().strip()
        download_location = self.download_location_input.text().strip() or '.'
        cookies_path = self.cookies_input.text().strip()  # Usa lo stesso file cookie del download

        if not url:
            QMessageBox.warning(self, 'Error', 'Please enter a Panopto URL for subtitle extraction.')
            return

        # The new extractor only supports SRT, so we hardcode it.
        selected_formats = ['srt']
        # Disable button and show progress
        self.extract_subtitle_btn.setEnabled(False)
        self.extract_subtitle_btn.setText('Extracting Subtitles...')
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_text.clear()
        self.status_text.append('Starting subtitle extraction...')

        # Start subtitle extraction in a separate thread
        # Passa cookies_path se fornito (video protetti richiedono autenticazione)
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
        self.extract_subtitle_btn.setText('Extract Subtitles')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')


    def audio_extraction_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.extract_audio_btn.setEnabled(True)
        self.extract_audio_btn.setText('Extract Audio')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')

    def download_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.download_btn.setText('Start Download')

        if success:
            QMessageBox.information(self, 'Success', message)
            self.status_text.append(f'\n✅ {message}')
        else:
            QMessageBox.critical(self, 'Error', message)
            self.status_text.append(f'\n❌ {message}')

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
    
    args = parser.parse_args()

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
