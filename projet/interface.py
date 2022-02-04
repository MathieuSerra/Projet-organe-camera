'''
File to launch app
'''
# General imports
import sys
sys.path.append("..")
import os
import time
#qimport h5py
from datetime import datetime
#from tqdm import tqdm
import webbrowser

# Communication with C-ARM
import serial
import serial.tools.list_ports

### AUTOMATICALLY FIND ARDUINO PORT ###
try:
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" in p[1]:
            arduino_port = p[0]
    ser = serial.Serial(arduino_port, 9600)
except:
    print('No Arduino Port')

# Qt imports
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import qdarkstyle ##

# Calculation imports
#import math
import numpy as np
#from matplotlib import pyplot as plt

import cv2
# imported fluor
img_fluoro=cv2.imread('fluoro_1.jpg')


class Controller(QMainWindow):
    '''Class for the app's main window'''

    sig_update_progress = pyqtSignal(int) #Signal for progress bar in status bar
    sig_update_motor_angle = pyqtSignal(int) ###

    def __init__(self):
        QMainWindow.__init__(self)
        self.current_angle = 0
        self.steps_per_deg = 1600/360
        # Load user interface
        basepath = os.path.join(os.path.dirname(__file__))
        uic.loadUi(os.path.join(basepath,"interface.ui"), self)
        self.showMaximized()

        # Initialize status variables
        self.camera1Active = True
        self.camera2Active = True
        self.camera3Active = True

        self.frameOrder = {'Caméra principale (traitée)':self.label_cam0, \
            'Caméra principale (non traitée)':self.label_cam1, \
            'Caméra secondaire gauche':self.label_cam2, \
            'Caméra secondaire droite':self.label_cam3}
        self.zoom = 'Caméra principale (traitée)'

        # Initiate buttons
        self.pushButton_camera1.clicked.connect(self.activateDeactivateCam1)
        self.pushButton_cameraTraitee.clicked.connect(self.activateDeactivateCam1)
        self.pushButton_camera2.clicked.connect(self.activateDeactivateCam2)
        self.pushButton_camera3.clicked.connect(self.activateDeactivateCam3)

        self.pushButton_zoom1.clicked.connect(self.zoomCam1)
        self.pushButton_zoom2.clicked.connect(self.zoomCam2)
        self.pushButton_zoom3.clicked.connect(self.zoomCam3)

        self.pushButton_rotateLeft.clicked.connect(self.rotate_left)
        self.pushButton_rotateRight.clicked.connect(self.rotate_right)
        self.horizontalSlider.setTracking(False)
        self.horizontalSlider.valueChanged.connect(self.updateAngle)
        self.horizontalSlider.valueChanged.connect(self.turnAngle)
        self.horizontalSlider.setMinimum(-45)
        self.horizontalSlider.setMaximum(45)

        self.pushButton_infos.clicked.connect(self.openHelp)

        # Start camera thread
        self.thread1 = Camera1_Thread(self.label_cam1, self.label_cam0)
        self.startCamera1()

        self.thread2 = Camera2_Thread()
        self.startCamera2()

        self.thread3 = Camera3_Thread()
        self.startCamera3()

        # Create status bar
        self.label_statusBar = QLabel()
        self.progress_statusBar = QProgressBar()
        self.statusbar.addPermanentWidget(self.label_statusBar)
        self.statusbar.addPermanentWidget(self.progress_statusBar)
        self.progress_statusBar.hide()
        self.progress_statusBar.setFixedWidth(250)

        self.sig_update_progress.connect(self.progress_statusBar.setValue)

        #self.sig_update_motor_angle.connect(self.updateAngle)

    def startCamera1(self):
        '''Start camera 1'''
        try:
            self.thread1.start()
            self.thread1.imageUpdate.connect(self.imageUpdateSlot)
            self.thread1.imageUpdateXray.connect(self.imageUpdateSlotXray)
        except:
            self.showErrorPopup('starting camera 1')

    def startCamera2(self):
        '''Start camera 2'''
        try:
            self.thread2.start()
            self.thread2.imageUpdate2.connect(self.imageUpdateSlot2)
        except:
            self.showErrorPopup('starting camera 2')

    def startCamera3(self):
        '''Start camera 3'''
        try:
            self.thread3.start()
            self.thread3.imageUpdate3.connect(self.imageUpdateSlot3)
        except:
            self.showErrorPopup('starting camera 3')

    def imageUpdateSlot(self, Image):
        '''Update camera 1 image with the images emitted by the thread'''

        if self.frameOrder['Caméra principale (non traitée)'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Caméra principale (non traitée)'].setPixmap(QPixmap.fromImage(Image))

    def imageUpdateSlotXray(self, Image):
        '''Update camera 1 image with the Xray images emitted by the thread'''

        if self.frameOrder['Caméra principale (traitée)'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Caméra principale (traitée)'].setPixmap(QPixmap.fromImage(Image))


    def imageUpdateSlot2(self, Image):
        '''Update camera 2 image with the images emitted by the thread'''

        if self.frameOrder['Caméra principale gauche'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Caméra principale gauche'].setPixmap(QPixmap.fromImage(Image))


    def imageUpdateSlot3(self, Image):
        '''Update camera 3 image with the images emitted by the thread'''

        if self.frameOrder['Caméra principale droite'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Caméra principale droite'].setPixmap(QPixmap.fromImage(Image))


    def activateDeactivateCam1(self):
        '''Stop or activate camera 1 feed'''
        if self.camera1Active:
            self.thread1.stop()
            #self.pushButton_camera1.setText('Activer')
            self.pushButton_camera1.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            #self.pushButton_cameraTraitee.setText('Activer')
            self.pushButton_cameraTraitee.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.camera1Active = False
        else:
            self.startCamera1()
            #self.pushButton_camera1.setText('Désactiver')
            self.pushButton_camera1.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            #self.pushButton_cameraTraitee.setText('Désactiver')
            self.pushButton_cameraTraitee.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            self.camera1Active = True

    def activateDeactivateCam2(self):
        '''Stop or activate camera 1 feed'''
        if self.camera2Active:
            self.thread2.stop()
            #self.pushButton_camera2.setText('Activer')
            self.pushButton_camera2.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.camera2Active = False
        else:
            self.startCamera2()
            #self.pushButton_camera2.setText('Désactiver')
            self.pushButton_camera2.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            self.camera2Active = True

    def activateDeactivateCam3(self):
        '''Stop or activate camera 1 feed'''
        if self.camera3Active:
            self.thread2.stop()
            #self.pushButton_camera3.setText('Activer')
            self.pushButton_camera3.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.camera3Active = False
        else:
            self.startCamera2()
            #self.pushButton_camera3.setText('Désactiver')
            self.pushButton_camera3.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            self.camera3Active = True

    def zoomCam1(self):
        ''' '''
        previousZoom = self.groupBox_frame0.title()
        self.zoom = self.groupBox_frame1.title()
        self.groupBox_frame0.setTitle(self.zoom)
        self.groupBox_frame1.setTitle(previousZoom)

        self.frameOrder[previousZoom] = self.label_cam1
        self.frameOrder[self.zoom] = self.label_cam0


    def zoomCam2(self):
        ''' '''
        previousZoom = self.groupBox_frame0.title()
        self.zoom = self.groupBox_frame2.title()
        self.groupBox_frame0.setTitle(self.zoom)
        self.groupBox_frame2.setTitle(previousZoom)

        self.frameOrder[previousZoom] = self.label_cam2
        self.frameOrder[self.zoom] = self.label_cam0

    def zoomCam3(self):
        ''' '''
        previousZoom = self.groupBox_frame0.title()
        self.zoom = self.groupBox_frame3.title()
        self.groupBox_frame0.setTitle(self.zoom)
        self.groupBox_frame3.setTitle(previousZoom)

        self.frameOrder[previousZoom] = self.label_cam3
        self.frameOrder[self.zoom] = self.label_cam0
    
    def updateAngle(self):
        angle = self.horizontalSlider.value()
        self.label_angle.setText('Angle : '+str(angle)+'°')

    def turnAngle(self):
        angle = self.horizontalSlider.value()
        angle = int(angle)
        if angle != self.current_angle :
            rotation = angle - self.current_angle
            rotation = float(rotation)
            steps = int(np.round(self.steps_per_deg * rotation))
            steps_byte = bytes(str(steps), 'utf-8')
            ser.write(steps_byte)
            self.current_angle = angle


    def update_status_bar(self, text=''):
        '''Updates the status bar text'''

        self.label_statusBar.setText(text)

    def showErrorPopup(self, error=''):
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
        rotation = 5 ## 5 degrees
        rotation = float(rotation)
        steps = int(np.round(self.steps_per_deg * rotation))
        steps_byte = bytes(str(steps), 'utf-8')
        ser.write(steps_byte)

    def rotate_right(self):
        '''Rotates right the motor'''
        rotation = -5 ## -5 degrees
        rotation = float(rotation)
        steps = int(np.round(self.steps_per_deg * rotation))
        steps_byte = bytes(str(steps), 'utf-8')
        ser.write(steps_byte)

    def openHelp(self):
        '''Open help documentation for the program (PDF)'''
        webbrowser.open_new(r'file://Guide.pdf') ##

#    def resizeEvent(self, event):
#        '''Executes when the main window is resized'''
#        pass
        #self.label.resize(self.width(), self.height())

#    def closeEvent(self, event):
#        '''Making sure that everything is closed when the user exits the software.
#           This function executes automatically when the user closes the UI.
#           This is an intrinsic function name of Qt, don't change the name even 
#           if it doesn't follow the naming convention'''
#
#        if self.camera1Active:
#            self.thread1.stop()
#        if self.camera2Active:
#            self.thread2.stop()
#
#        print('Window closed')

class Camera1_Thread(QThread):
    '''Thread that emits a QT image from camera 1'''

    imageUpdate = pyqtSignal(QImage)
    imageUpdateXray = pyqtSignal(QImage)

    def __init__(self, image_label1, image_label2):
        super().__init__()
        self.image_label1 = image_label1
        self.image_label2 = image_label2
    
    def run(self):
        self.threadActive = True
        VideoDevice1 = 0##2 ##0 ##À changer selon le device # Webcam
        Capture = cv2.VideoCapture(VideoDevice1, cv2.CAP_DSHOW)
        #img=cv2.imread('fluoro_1.jpg')
        
        while self.threadActive:
            ##print(self.image_label1.width())
            ##print(self.image_label1.height())
            ##
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                # Original camera 1 image
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(Image, 1)
                
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888) #Size: (640, 480) = (4,3)
                ##Pic = ConvertToQtFormat.scaled(self.image_label1.width(), self.image_label1.height(), Qt.KeepAspectRatio) 
                #Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                ##Pic = ConvertToQtFormat.scaled(200, 150, Qt.KeepAspectRatio)
                Pic = ConvertToQtFormat.scaled(1000, 750, Qt.KeepAspectRatio)
                self.imageUpdate.emit(Pic)

                # Processed camera 1 image (x ray)
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                width=480
                height=480
                sImage=Image[0:width, 0:height]
                simg=img_fluoro[0:width, 0:height]
                img_gray_fluoro=cv2.cvtColor(simg, cv2.COLOR_BGR2GRAY)
                gray=cv2.cvtColor(sImage, cv2.COLOR_BGR2GRAY)
                FlippedImage = cv2.flip(gray, 1)

                
                #nouveau
                sImage_rgb=cv2.cvtColor(sImage, cv2.COLOR_BGR2RGB)
                twoDimage=sImage_rgb.reshape((-1,3))
                twoDimage=np.float32(twoDimage)
                #Nombre d'iteration 2-3 (pour la rapidité)-perte de précision avec n=2
                criteria=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,3,1.0)
                K=3
                attempts=3
                ret, label, center=cv2.kmeans(twoDimage,K,None,criteria,attempts,cv2.KMEANS_PP_CENTERS)
                center=np.uint8(center)
                res=center[label.flatten()]
                result_image=res.reshape((sImage_rgb.shape))
                result_gray=cv2.cvtColor(result_image, cv2.COLOR_RGB2GRAY)
                ret,th=cv2.threshold(result_gray,100,255,cv2.THRESH_BINARY_INV)
                ret, result=cv2.threshold(cv2.bitwise_or(gray,th),253,255,cv2.THRESH_TOZERO_INV)
                final=cv2.addWeighted(result,0.7,img_gray_fluoro,0.3,0.0)
                final=cv2.flip(final,1)

                # #ancien
                # _, th1=cv2.threshold(FlippedImage, np.mean(FlippedImage)-20, 255, cv2.THRESH_TOZERO)
                # #sum2=cv2.bitwise_and(FlippedImage,FlippedImage,mask=th1)
                # #sum2=cv2.bitwise_not(sum2)
                # #final=cv2.bitwise_and(th1,img_gray_fluoro)
                # final=cv2.addWeighted(th1,0.6,img_gray_fluoro,0.5,0)
                # Convert to QT format
                ConvertToQtFormat = QImage(final.data, final.shape[1], final.shape[0], QImage.Format_Grayscale8) #Size: (640, 480)
                ##Pic = ConvertToQtFormat.scaled(self.image_label2.width(), self.image_label2.height(), Qt.KeepAspectRatio) 
                #Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                Pic = ConvertToQtFormat.scaled(1000, 750, Qt.KeepAspectRatio)
                #Pic = ConvertToQtFormat.scaled(200, 150, Qt.KeepAspectRatio)
                self.imageUpdateXray.emit(Pic)
    
    def stop(self):
        self.threadActive = False
        self.quit()

class Camera2_Thread(QThread):
    '''Thread that emits a QT image from camera 2'''

    imageUpdate2 = pyqtSignal(QImage)
    
    def run(self):
        self.threadActive = True
        VideoDevice2 = 3
        Capture = cv2.VideoCapture(VideoDevice2, cv2.CAP_DSHOW) ##cv2.VideoCapture(0) # Webcam
        
        while self.threadActive:
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(Image, 1)
                
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                #Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                Pic = ConvertToQtFormat.scaled(1000, 750, Qt.KeepAspectRatio)
                self.imageUpdate2.emit(Pic)
    
    def stop(self):
        self.threadActive = False
        self.quit()

class Camera3_Thread(QThread):
    '''Thread that emits a QT image from camera 3'''

    imageUpdate3 = pyqtSignal(QImage)
    
    def run(self):
        self.threadActive = True
        VideoDevice2 = 4
        Capture = cv2.VideoCapture(VideoDevice2, cv2.CAP_DSHOW) ##cv2.VideoCapture(0) # Webcam
        
        while self.threadActive:
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(Image, 1)
                
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                #Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                Pic = ConvertToQtFormat.scaled(1000, 750, Qt.KeepAspectRatio)
                self.imageUpdate3.emit(Pic)
    
    def stop(self):
        self.threadActive = False
        self.quit()

# Launch app
if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) ##
    controller = Controller()
    controller.show()
    sys.exit(app.exec_())