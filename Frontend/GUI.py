from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os

env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

def AnswerModifier(Answer):

    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def QueryMOdifier(Query):

    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = [ "how", "what", "who", "when", "why", "which", "whose", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query from word in question_words):
       if query_words[-1][-1] in ['.', '?', '!']:
          new_query = new_query[:-1]+"."
       else:
          new_query +="."
    
    else: 
       if query_words[-1][-1] in ['.','?','!']:
          new_query = new_query[:-1]+"."

       else:
          new_query += "."

    return new_query.capitalize()

def SetMIcrophoneStatus(Command):
   with open(rf'{TempDirPath}\Mic.data', "w", encoding='utf-8') as file:
      file.write(Command)

def GetMIcrophoneStatus():
   with open (rf'{TempDirPath}\Mic.data', "r", encoding='utf-8') as file:
      Status = file.read() 
   return Status

def SetAssistantStatus(Status):
   with open(rf'{TempDirPath}\Status.data', "w", encoding='utf-8') as file:
      file.write(Status)

def GetAssistantStatus():
   with open (rf'{TempDirPath}\Status.data', "r", encoding='utf-8') as file:
      Status = file.read() 
   return Status

def MicButtonInitialized():
   SetAssistantStatus|("False")

def MicButtonClosed():
   SetMIcrophoneStatus("True")

def GarphicsDirectoryPath(Filename):
   Path = rf'{GraphicsDirPath}\{Filename}'
   return Path

def TempDirectoryPath(Filename):
   Path = rf'{TempDirPath}\{Filename}'
   return Path

def ShowTextToScreen(Text):
   with open(rf'{TempDirPath}\Response.data', "W", encoding='utf-8') as file:
      file.write(Text)

class ChatSection(QWidget):
   
   def __init__(self):
      
      super(ChatSection, self).__init__()
      layout = QVBoxLayout(self)
      layout.setContentsMargins(-10, 40, 40, 100)
      layout.setSpacing(-100)
      self.chat_text_edit = QTextEdit()
      self.chat_text_edit.setReadOnly(True)
      self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
      self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
      layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
      layout.setStretch(1, 1)
      self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
      text_color = QColor(QT.blue)
      text_color_text = QTextCharFormat()
      text_color_text.setForeground(text_color)
      self.chat_text_edit.setCurrentCharFormat(text_color_text)
      self.gif_label = QLabel()
      self


    

    
