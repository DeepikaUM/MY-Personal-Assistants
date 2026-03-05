

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QTimer
from dotenv import dotenv_values
import os
import sys
from threading import Lock
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Backend.TextToSpeech import StopSpeaking

file_lock = Lock()  # ✅ New: protect file writes

env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirectoryPath = rf"{current_dir}\Frontend\Graphics"

# --- Language selection helpers ---
LANG_FILE = os.path.join(TempDirPath, "Language.data")

# ensure the file exists with a default
if not os.path.exists(LANG_FILE):
    with open(LANG_FILE, "w", encoding="utf-8") as f:
        f.write("en-IN")  # default to English (India)

def SetLanguage(lang_code: str):
    """Persist the selected UI/STT/TTS language."""
    with file_lock:
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            f.write(lang_code)

def GetLanguage() -> str:
    """Read current selected language."""
    try:
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "en-IN"
# --- end helpers ---



def AnswerModifier(Answer):
      lines = Answer.split('\n')
      non_empty_lines = [line for line in lines if line.strip()]
      modified_answer = '\n'.join(non_empty_lines)
      return modified_answer

def QueryModifier(Query):

      new_query = Query.lower().strip()
      query_words = new_query.split()
      question_words = [ "how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

      if any(word + ' ' in new_query for word in question_words):
            if query_words[-1][-1] in ['.', '?', '!']:
                   new_query = new_query[:-1] + '?'
            else:
                   new_query += "?"
  
      else:
            if query_words[-1][-1] in ['.', '?', '!']:
                   new_query = new_query[:-1] + '.'
            else:
                   new_query += "."

      return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with file_lock:
        with open(rf"{TempDirPath}\Mic.data", "w", encoding='utf-8') as file:
            file.write(Command)

def GetMicrophoneStatus():
      with open(rf"{TempDirPath}\Mic.data", "r", encoding='utf-8') as file:
            Status = file.read()
      return Status

def SetAssistantStatus(Status):
    with file_lock:
        with open(rf"{TempDirPath}\Status.data", "w", encoding='utf-8') as file:
            file.write(Status)

def GetAssistantStatus():
      with open(rf"{TempDirPath}\Status.data", "r", encoding='utf-8') as file:
            Status = file.read()
      return Status

def MicButtonInitialed():
     SetMicrophoneStatus("False")

def MicButtonClosed():
     SetMicrophoneStatus("True")

def GetGraphicsPath(Filename):
    return rf'{GraphicsDirectoryPath}\{Filename}'

def TempDirectoryPath(Filename):
      Path = rf'{TempDirPath}\{Filename}'
      return Path

def ShowTextToScreen(Text):
    with file_lock:
        with open(rf"{TempDirPath}\Responses.data", "w", encoding='utf-8') as file:
            file.write(Text)

class ChatSection(QWidget):

      def __init__(self):
            super(ChatSection, self).__init__()
            layout = QVBoxLayout(self)
            layout.setContentsMargins(-10, 40, 40, 100)
            layout.setSpacing(-100)
            self.chat_text_edit = QTextEdit()
            self.chat_text_edit.setReadOnly(True)
            self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)  # No text interaction
            self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
            layout.addWidget(self.chat_text_edit)
            self.setStyleSheet("background-color: black;")
            layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
            layout.setStretch(1, 1)
            self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
            text_color = QColor(Qt.blue)
            text_color_text = QTextCharFormat()
            text_color_text.setForeground(text_color)
            self.chat_text_edit.setCurrentCharFormat(text_color_text)
            self.gif_label = QLabel()
            self.gif_label.setStyleSheet("border: none;")
            movie = QMovie(GetGraphicsPath('Red.gif'))    #gif change remainder
            max_gif_size_W = 480
            max_gif_size_H = 270
            movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
            self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            self.gif_label.setMovie(movie)
            movie.start()
            layout.addWidget(self.gif_label)
            self.label = QLabel("")
            self.label.setStyleSheet("color: white; font-size:16px; margin-right: 195px; border: none; margin-top: -30px;")
            self.label.setAlignment(Qt.AlignRight)
            layout.addWidget(self.label)
            layout.setSpacing(-10)
            layout.addWidget(self.gif_label)
            font = QFont()
            font.setPointSize(13)
            self.chat_text_edit.setFont(font)
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.loadMessages)
            self.timer.timeout.connect(self.SpeechRecogText)
            self.timer.start(100)
            self.chat_text_edit.viewport().installEventFilter(self)
            self.setStyleSheet("""
                  QScrollBar:vertical {
                  border: none;
                  background: black;
                  width: 10px;
                  margin: 0px 0px 0px 0px;
                  }
                               
                  QScrollBar::handle:vertical {
                  background: white;
                  min-height: 20px;
                  }
                               
                  QScrollBar::add-line:vertical {
                  background: black;
                  subcontrol-position: bottom;
                  subcontrol-origin: margin;
                  height: 10px;
                  }
                               
                  QScrollBar::sub-line:vertical {
                  background: black;
                  subcontrol-position: top;
                  subcontrol-origin: margin;
                  height: 10px;
                  }
                               
                  QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                  border: none;
                  background: none;
                  color: none;
                  }
                               
                  QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                  background: none;
                  }
            """)
    
      def loadMessages(self):
            global old_chat_message

            with open(TempDirectoryPath('Responses.data'), "r", encoding="utf-8") as file:
                  messages = file.read()
    
                  if None==messages:
                        pass
                  elif len(messages)<=1:
                        pass

                  elif str(old_chat_message)==str(messages):
                        pass
                  else:
                       self.addMessage(message=messages, color='White')
                       old_chat_message = messages

      def SpeechRecogText(self):
            with open(TempDirectoryPath('Status.data'), "r", encoding="utf-8") as file:
                  messages = file.read()
                  self.label.setText(messages)

      def Load_icon(self, path, width=60, height=60):
            pixmap = QPixmap(path)
            new_pixmap = pixmap.scaled(width, height)
            self.icon_label.setPixmap(new_pixmap)

      def toggle_icon(self, event=None):

            if self.toggled:
                  self.load_icon(GetGraphicsPath("voice.png"), 60, 60)
                  MicButtonInitialed()
            else:
                  self.load_icon(GetGraphicsPath("mic.png"), 60, 60)
                  MicButtonClosed()

            self.toggled = not self.toggled

      def addMessage(self, message, color):
            cursor = self.chat_text_edit.textCursor()
            format = QTextCharFormat()
            formatm = QTextBlockFormat()
            formatm.setTopMargin(10)
            formatm.setLeftMargin(10)
            format.setForeground(QColor(color))
            cursor.setCharFormat(format)
            cursor.setBlockFormat(formatm)
            cursor.insertText(message + "\n")
            self.chat_text_edit.setTextCursor(cursor)

class InitialScreen(QWidget):
      def __init__(self, parent=None):
            super().__init__(parent)
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
            content_layout = QVBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)
            gif_label = QLabel()
            movie = QMovie(GetGraphicsPath("Red.gif"))
            gif_label.setMovie(movie)
            max_gif_size_H = int(screen_width / 16 * 9)
            movie.setScaledSize(QSize(screen_width, max_gif_size_H))
            gif_label.setAlignment(Qt.AlignCenter)
            movie.start()
            gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.icon_label = QLabel()
            pixmap = QPixmap(GetGraphicsPath("Mic_on.png"))
            new_pixmap = pixmap.scaled(60, 60)
            self.icon_label.setPixmap(new_pixmap)
            self.icon_label.setFixedSize(150, 150)
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.toggled = True
            self.toggle_icon()
            self.icon_label.mousePressEvent = self.toggle_icon
            self.label = QLabel("")
            self.label.setStyleSheet("color: white; font-size:16px ; margin-bottom:0;")
            content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
            content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
            content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
            content_layout.setContentsMargins(0, 0, 0, 150)
            self.setLayout(content_layout)
            self.setFixedHeight(screen_height)
            self.setFixedWidth(screen_width)
            self.setStyleSheet("background-color: black;")
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.SpeechRecogText)
            self.timer.start(5)

        
      def SpeechRecogText(self):
            with open(TempDirectoryPath('Status.data'), "r", encoding="utf-8") as file:
                  messages = file.read()
                  self.label.setText(messages)

      def load_icon(self, path, width=60, height=60):
            pixmap = QPixmap(path) 
            new_pixmap = pixmap.scaled(width, height)
            self.icon_label.setPixmap(new_pixmap)

      def toggle_icon(self, event=None): 
            if self.toggled:
                  print("🔍 Trying to load:", GetGraphicsPath("Mic_on.png"))
                  self.load_icon(GetGraphicsPath('Mic_on.png'),60 ,60)
                  MicButtonInitialed()
            
            else:
                  print("🔍 Trying to load:", GetGraphicsPath("Mic_off.png"))
                  self.load_icon(GetGraphicsPath('Mic_off.png'),60 ,60)
                  MicButtonClosed()

            self.toggled = not self.toggled

class MessageScreen(QWidget):
      def __init__(self, parent=None):
            super().__init__(parent)
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
            layout = QVBoxLayout()
            lable = QLabel("")
            layout.addWidget(lable)
            chat_section = ChatSection()
            layout.addWidget(chat_section)
            self.setLayout(layout)
            self.setStyleSheet("background-color: black;")
            self.setFixedHeight(screen_height)
            self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
      
      def __init__(self, parent, stacked_widget):
            super().__init__(parent)
            self.initUI()
            self.current_screen = None
            self.stacked_widget = stacked_widget
            
      def _on_lang_clicked(self, code: str):
          SetLanguage(code)
          self._refresh_lang_buttons()

      def _refresh_lang_buttons(self):
          sel = GetLanguage()
          def set_style(btn, code):
              if sel == code:
            # selected = inverted (white bg) to stand out
                  btn.setStyleSheet("background-color: white; color: black; font-weight: bold; border: 2px solid white;")
              else:
                 btn.setStyleSheet("background-color: black; color: white; font-weight: bold; border: 1px solid white;")
          set_style(self.btn_en, "en-IN")
          set_style(self.btn_hi, "hi-IN")
          set_style(self.btn_kn, "kn-IN")


      def initUI(self):
            self.setFixedHeight(50)
            layout = QHBoxLayout(self)
            layout.setAlignment(Qt.AlignRight)
            home_button = QPushButton()
            home_icon = QIcon(GetGraphicsPath("Home.png"))
            home_button.setIcon(home_icon)
            home_button.setText("Home")
            home_button.setStyleSheet("height:40px; line-height:40px; background-color:black; color: white")
           
            message_button = QPushButton()
            message_icon = QIcon(GetGraphicsPath("Chats.png"))
            message_button.setIcon(message_icon)
            message_button.setText(" Chat")
            message_button.setStyleSheet("height:40px; line-height:40px; background-color:black; color: white")
            
            minimize_button = QPushButton()
            minimize_icon = QIcon(GetGraphicsPath("Minimize2.png"))
            minimize_button.setIcon(minimize_icon)
            minimize_button.setStyleSheet("background-color:white")
            minimize_button.clicked.connect(self.minimizeWindow)

            self.maximize_button = QPushButton()
            self.maximize_icon = QIcon(GetGraphicsPath("Maximize.png"))
            self.restore_icon = QIcon(GetGraphicsPath("Maximize.png"))
            self.maximize_button.setIcon(self.maximize_icon)
            self.maximize_button.setFlat(True)
            self.maximize_button.setStyleSheet("background-color:white")
            self.maximize_button.clicked.connect(self.maximizeWindow)

            close_button = QPushButton()
            close_icon = QIcon(GetGraphicsPath("Close.png"))
            close_button.setIcon(close_icon)
            close_button.setStyleSheet("background-color:white")
            close_button.clicked.connect(self.closeWindow)

        # Other components
            line_frame = QFrame()
            line_frame.setFixedHeight(1)
            line_frame.setFrameShape(QFrame.HLine)
            line_frame.setFrameShadow(QFrame.Sunken)
            line_frame.setStyleSheet("border-color: white;")

            title_label = QLabel(f" {str(Assistantname).capitalize()} AI   ")
            title_label.setStyleSheet("color: white; font-size: 18px;; background-color:black")

            # --- Language buttons (EN/HI/KN) ---
            self.btn_en = QPushButton("EN")
            self.btn_hi = QPushButton("HI")
            self.btn_kn = QPushButton("KN")

            for b in (self.btn_en, self.btn_hi, self.btn_kn):
                b.setFixedWidth(42)
                b.setCursor(Qt.PointingHandCursor)

# click handlers -> update file + refresh styles
            self.btn_en.clicked.connect(lambda: self._on_lang_clicked("en-IN"))
            self.btn_hi.clicked.connect(lambda: self._on_lang_clicked("hi-IN"))
            self.btn_kn.clicked.connect(lambda: self._on_lang_clicked("kn-IN"))
# --- end buttons ---

            home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
            message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
       
            layout.addWidget(title_label)
            layout.addSpacing(8)
            layout.addWidget(self.btn_en)
            layout.addWidget(self.btn_hi)
            layout.addWidget(self.btn_kn)
            layout.addStretch(1)

            layout.addStretch(1)
            layout.addWidget(home_button)
            layout.addWidget(message_button)
            layout.addStretch(1)
            layout.addWidget(minimize_button)
            layout.addWidget(self.maximize_button)
            layout.addWidget(close_button)
            layout.addWidget(line_frame)
            self.draggable = True
            self.offset = None
            self._refresh_lang_buttons()


      def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), Qt.black)
            super().paintEvent(event)

      def minimizeWindow(self):
            self.parent().showMinimized()

      def maximizeWindow(self):
            if self.parent().isMaximized():
                  self.parent().showNormal()
                  self.maximize_button.setIcon(self.maximize_icon)
            else:
                  self.parent().showMaximized()
                  self.maximize_button.setIcon(self.restore_icon)

      def closeWindow(self):
            self.parent().close()

      def mousePressEvent(self, event):
            if self.draggable:
                  self.offset = event.pos()

      def mouseMoveEvent(self, event):
            if self.draggable and self.offset is not None:

                  new_pos = event.globalPos() - self.offset
                  self.parent().move(new_pos)

      def showMessageScreen(self):
            if self.current_screen is not None:
                  self.current_screen.hide()

            message_screen = MessageScreen(self)
            layout = self.parent().layout()
            if layout is not None:
                  layout.addWidget(message_screen)
            self.current_screen = message_screen

      def showInitialScreen(self):
            if self.current_screen is not None:
                  self.current_screen.hide()

            initial_screen = InitialScreen(self)
            layout = self.parent().layout()
            if layout is not None:
                  layout.addWidget(initial_screen)
            self.current_screen = initial_screen

class MainWindow(QMainWindow):

      def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.initUI()

      def initUI(self):
            desktop = QApplication.desktop()
            screen_width = desktop.screenGeometry().width()
            screen_height = desktop.screenGeometry().height()
            stacked_widget = QStackedWidget(self)
            initial_screen = InitialScreen()
            message_screen = MessageScreen()
            stacked_widget.addWidget(initial_screen)
            stacked_widget.addWidget(message_screen)
            self.setGeometry(0, 0, screen_width, screen_height)
            self.setStyleSheet("background-color: black;")
            top_bar = CustomTopBar(self, stacked_widget)
            stop_button = QPushButton("Stop")
            stop_button.setFixedSize(80, 30)
            stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
            stop_button.clicked.connect(self.stop_interaction)
            top_bar.layout().addWidget(stop_button)
            self.setMenuWidget(top_bar)
            self.setCentralWidget(stacked_widget)

      def stop_interaction(self):
          try:
            from Backend.TextToSpeech import StopSpeaking
            StopSpeaking()
          except Exception as e:
             print("❌ Failed to stop speaking:", e)

    # Optional: reset assistant status
          try:
             with open("Frontend/Files/Status.data", "w", encoding="utf-8") as f:
                 f.write("Idle")
          except Exception as e:
              print("❌ Failed to update Status.data:", e)

    # Optional: stop long-processing tasks (requires main.py support)
          try:
              from Backend import main
              main.set_stop_flag(True)
          except Exception as e:
             print("❌ Couldn't call stop flag:", e)



def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()  # GUI runs here

    # After user closes the window
    os._exit(0)  # Safely shuts down backend too


if __name__ == "__main__":
    GraphicalUserInterface()



