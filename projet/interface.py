'''
File to launch app
'''
# General imports
import sys
sys.path.append("..")
import os
import time
import h5py
from datetime import datetime
from tqdm import tqdm

# Qt imports
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# Calculation imports
import math
import numpy as np
from matplotlib import pyplot as plt

import cv2


class Controller(QMainWindow):
    '''Class for the app's main window'''

    sig_update_progress = pyqtSignal(int) #Signal for progress bar in status bar

    def __init__(self):
        QMainWindow.__init__(self)
        
        # Load user interface
        basepath = os.path.join(os.path.dirname(__file__))
        uic.loadUi(os.path.join(basepath,"interface.ui"), self)

        # Initiate buttons
        self.pushButton_cancel.clicked.connect(self.CancelFeed)

        self.pushButton_rotateLeft.clicked.connect(self.rotate_left)
        self.pushButton_rotateRight.clicked.connect(self.rotate_right)

        # Start camera thread
        self.Thread1 = Camera1_Thread()
        self.Thread1.start()
        self.Thread1.ImageUpdate.connect(self.ImageUpdateSlot)

        # Create status bar
        self.label_statusBar = QLabel()
        self.progress_statusBar = QProgressBar()
        self.statusbar.addPermanentWidget(self.label_statusBar)
        self.statusbar.addPermanentWidget(self.progress_statusBar)
        self.progress_statusBar.hide()
        self.progress_statusBar.setFixedWidth(250)

        self.sig_update_progress.connect(self.progress_statusBar.setValue)

    def ImageUpdateSlot(self, Image):
        '''Update camera 1 image with the images emitted by the thread'''
        self.label_camera1.setPixmap(QPixmap.fromImage(Image))

        self.label_cameraTraitee.setPixmap(QPixmap.fromImage(Image)) ###

    def CancelFeed(self):
        '''Stops camera 1 feed'''
        self.Thread1.stop()
    
    def update_status_bar(self, text=''):
        '''Updates the status bar text'''

        self.label_statusBar.setText(text)

    def show_error_popup(self, error=''):
        '''Shows error popup'''
        
        error_popup = QMessageBox()
        error_popup.setWindowTitle('Program Error')
        error_popup.setText('Error while '+error+', please try again')
        error_popup.setIcon(QMessageBox.Warning)
        error_popup.setStandardButtons(QMessageBox.Ok)
        error_popup.setDefaultButton(QMessageBox.Ok)
        error_popup.exec_()
    
    def rotate_left(self):
        '''Rotates left the motor'''
        pass

    def rotate_right(self):
        '''Rotates right the motor'''
        pass

class Camera1_Thread(QThread):
    '''Thread that emits a QT image from camera 1'''

    ImageUpdate = pyqtSignal(QImage)
    
    def run(self):
        self.ThreadActive = True
        Capture = cv2.VideoCapture(0, cv2.CAP_DSHOW) ##cv2.VideoCapture(0) # Webcam

        while self.ThreadActive:
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(Image, 1)
                # Convert to QT format
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Pic)
    
    def stop(self):
        self.ThreadActive = False
        self.quit()

# Launch app
if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    controller = Controller()
    controller.show()
    sys.exit(app.exec_())