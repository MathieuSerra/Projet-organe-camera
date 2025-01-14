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
import cv2
# Communication with C-ARM
import serial
import serial.tools.list_ports

### AUTOMATICALLY FIND ARDUINO PORT ###

try:
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" in p[1]:
            arduino_port = p[0]
    ser = serial.Serial(arduino_port , 9600) ###arduino_port
except:
    arduino_port='COM3'
    print('No Arduino Port')
try:
    ser = serial.Serial(arduino_port , 9600)
except:
    
    print('No Arduino Port2')


### FIND CAMERA INDEX ###
device1 = 'None'
device2 = 'None'
device3 = 'None'
indices = [0,1,2,3,4,5]
for i in indices:
    device = indices[i]
    try :
        cap = cv2.VideoCapture(device)#, cv2.CAP_DSHOW)
        while True:
            ret,frame=cap.read()
            cv2.imshow('frame'+str(device),frame)
            #if cv2.waitKey(1) == ord('q'):
            contrast = cap.get(cv2.CAP_PROP_CONTRAST)
            print(contrast)
            if contrast == 5.0:
                device1 = device
            if contrast == 50.0:
                device2 = device
            if contrast == 10.0:
                device3 = device
            break
        cap.release()
        cv2.destroyAllWindows()
    except cv2.error as error :
        print("[Error]: {}".format(error))
print(device1)
print(device2)
print(device3)
# Qt imports
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
#import qdarkstyle ##

# Calculation imports
#import math
import numpy as np
#from matplotlib import pyplot as plt


# imported fluor
img_fluoro=cv2.imread('fluoro_2.jpg')


class Controller(QMainWindow):
    '''Class for the app's main window'''

    def __init__(self):
        QMainWindow.__init__(self)
        self.current_angle = 0
        self.steps_per_deg = 1600/360
        self.angleIncrement = 5
        self.showFps = False

        #Instantiating the settings and properties windows
        self.settingsDialog = Settings_Dialog()

        # Load user interface
        #basepath = os.path.join(os.path.dirname(__file__))
        #uic.loadUi(os.path.join(basepath,"interface.ui"), self)
        uic.loadUi("interface.ui", self)
        self.showMaximized()

        # Initialize status variables
        self.camera1Active = True
        self.camera2Active = True
        self.camera3Active = True

        self.frameOrder = {'Simulation':self.label_cam0, \
            'Image originale':self.label_cam1, \
            'Image secondaire gauche':self.label_cam2, \
            'Image secondaire droite':self.label_cam3}
        self.zoom = 'Simulation'

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
        self.pushButton_settings.clicked.connect(self.openSettingsDialog)

        #Connect settings options
        self.settingsDialog.buttonBox.accepted.connect(self.changeSettings)
        self.settingsDialog.buttonBox.rejected.connect(self.cancelSettings)
        self.updateAngleToolTip()

        # Start camera thread
        self.thread1 = Camera1_Thread()
        self.startCamera1()

        self.thread2 = Camera2_Thread()
        self.startCamera2()

        self.thread3 = Camera3_Thread()
        self.startCamera3()

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

        if self.frameOrder['Image originale'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Image originale'].setPixmap(QPixmap.fromImage(Image))

    def imageUpdateSlotXray(self, Image):
        '''Update camera 1 image with the Xray images emitted by the thread'''

        if self.frameOrder['Simulation'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Simulation'].setPixmap(QPixmap.fromImage(Image))


    def imageUpdateSlot2(self, Image):
        '''Update camera 2 image with the images emitted by the thread'''

        if self.frameOrder['Image secondaire gauche'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Image secondaire gauche'].setPixmap(QPixmap.fromImage(Image))


    def imageUpdateSlot3(self, Image):
        '''Update camera 3 image with the images emitted by the thread'''

        if self.frameOrder['Image secondaire droite'] != self.label_cam0:
            Image = Image.scaled(int(self.width()*0.2), int(self.height()*0.2), Qt.KeepAspectRatio)
        else:
            Image = Image.scaled(int(self.width()*0.7), int(self.height()*0.7), Qt.KeepAspectRatio)
        self.frameOrder['Image secondaire droite'].setPixmap(QPixmap.fromImage(Image))


    def activateDeactivateCam1(self):
        '''Stop or activate camera 1 feed'''
        if self.camera1Active:
            self.thread1.stop()
            self.pushButton_camera1.setToolTip('Activer')
            self.pushButton_camera1.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.pushButton_cameraTraitee.setToolTip('Activer')
            self.pushButton_cameraTraitee.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.camera1Active = False
        else:
            self.startCamera1()
            self.pushButton_camera1.setToolTip('Désactiver')
            self.pushButton_camera1.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            self.pushButton_cameraTraitee.setToolTip('Désactiver')
            self.pushButton_cameraTraitee.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            self.camera1Active = True

    def activateDeactivateCam2(self):
        '''Stop or activate camera 1 feed'''
        if self.camera2Active:
            self.thread2.stop()
            self.pushButton_camera2.setToolTip('Activer')
            self.pushButton_camera2.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.camera2Active = False
        else:
            self.startCamera2()
            self.pushButton_camera2.setToolTip('Désactiver')
            self.pushButton_camera2.setIcon(QIcon(os.getcwd()+"\\icones\\icon-pause-white.png"))
            self.camera2Active = True

    def activateDeactivateCam3(self):
        '''Stop or activate camera 1 feed'''
        if self.camera3Active:
            self.thread2.stop()
            self.pushButton_camera3.setToolTip('Activer')
            self.pushButton_camera3.setIcon(QIcon(os.getcwd()+"\\icones\\icon-play-white.png"))
            self.camera3Active = False
        else:
            self.startCamera2()
            self.pushButton_camera3.setToolTip('Désactiver')
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
        try:
            angle = self.horizontalSlider.value()
            angle = int(angle)
            if angle != self.current_angle :
                rotation = angle - self.current_angle
                rotation = float(rotation)
                steps = int(np.round(self.steps_per_deg * rotation))
                steps_byte = bytes(str(steps), 'utf-8')
                ser.write(steps_byte)
                self.current_angle = angle
        except:
            self.showErrorPopup('turning motor')

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
        rotation = float(self.angleIncrement) * -1 ####

        newAngle = self.horizontalSlider.value() + int(rotation)
        if newAngle >= -45:
            self.horizontalSlider.setValue(newAngle)
            self.updateAngle()
        else:
            self.showErrorPopup('rotating, angle exceeds the range of rotation')


    def rotate_right(self):
        '''Rotates right the motor'''
        rotation = float(self.angleIncrement)

        newAngle = self.horizontalSlider.value() + int(rotation)
        if newAngle <= 45:
            self.horizontalSlider.setValue(newAngle)
            self.updateAngle()
        else:
            self.showErrorPopup('rotating, angle exceeds the range of rotation')

    def openHelp(self):
        '''Open help documentation for the program (PDF)'''
        webbrowser.open_new('Guide.pdf') ##

    def openSettingsDialog(self):
        '''Open the dialog window for modification of settings'''
        self.settingsDialog.exec_()

    def changeSettings(self):
        '''Change the configuration settings'''
        self.angleIncrement = int(self.settingsDialog.doubleSpinBox_motorIncrement.value())
        self.updateAngleToolTip()
        self.showFps = self.settingsDialog.checkBox_fps.isChecked()
        self.settingsDialog.accept()

    def cancelSettings(self):
        '''Change the configuration settings'''
        self.settingsDialog.doubleSpinBox_motorIncrement.setValue(self.angleIncrement)
        self.settingsDialog.checkBox_fps.setChecked(self.showFps)
        self.settingsDialog.accept()


    def updateAngleToolTip(self):
        self.pushButton_rotateLeft.setToolTip('Tourner de -' + str(self.angleIncrement) + '° (sens anti-horaire)')
        self.pushButton_rotateRight.setToolTip('Tourner de ' + str(self.angleIncrement) + '° (sens horaire)')

#    def resizeEvent(self, event):
#        '''Executes when the main window is resized'''
#        pass
        #self.label.resize(self.width(), self.height())

    def closeEvent(self, event):
        '''Making sure that everything is closed when the user exits the software.
           This function executes automatically when the user closes the UI.
           This is an intrinsic function name of Qt, don't change the name even 
           if it doesn't follow the naming convention'''

        self.activateDeactivateCam1()
        self.activateDeactivateCam2()
        self.activateDeactivateCam3()

class Settings_Dialog(QDialog):
    '''Class for Settings Dialog'''
    
    def __init__(self):
        QDialog.__init__(self)
        
        #Loading user interface
        #basepath = os.path.join(os.path.dirname(__file__))
        #uic.loadUi(os.path.join(basepath,"settings.ui"), self)
        uic.loadUi("settings.ui", self)
        
        #Loading preset
        self.loadPreset()

    def loadPreset(self):
        '''Load preset'''
        self.doubleSpinBox_motorIncrement.setValue(5)

class Camera1_Thread(QThread):
    '''Thread that emits a QT image from camera 1'''

    imageUpdate = pyqtSignal(QImage)
    imageUpdateXray = pyqtSignal(QImage)
    
    def run(self):
        self.threadActive = True
        #VideoDevice1 = 0 ##2 ##0 ##À changer selon le device # Webcam
        Capture = cv2.VideoCapture(device1)#, cv2.CAP_DSHOW)
        #img=cv2.imread('fluoro_1.jpg')
        
        prev_frame_time = 0
        new_frame_time = 0
        start_time = 0
        frame_width = int(Capture.get(3))
        frame_height = int(Capture.get(4))
        while self.threadActive:
            ##print(self.image_label1.width())
            ##print(self.image_label1.height())
            ##

            # Redimensionnalisation de l'image fluoroscopique
            simg=img_fluoro
            #simg=cv2.resize(simg,(320,240),interpolation=cv2.INTER_AREA)
            img_gray_fluoro=cv2.cvtColor(simg, cv2.COLOR_BGR2GRAY)
            
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                #start_time = time.time() # start time of the loop

                # Original camera 1 image
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(rgb_frame, 1) # utile?

                #Calcul des fps
                new_frame_time = time.time()
                fps = int(1/(new_frame_time-prev_frame_time))
                prev_frame_time = new_frame_time

                if controller.showFps == True:
                    fpsText = "FPS: " + str(fps)
                    cv2.putText(FlippedImage, fpsText, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)
                
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888) #Size: (640, 480) = (4,3)
                ##Pic = ConvertToQtFormat.scaled(self.image_label1.width(), self.image_label1.height(), Qt.KeepAspectRatio) 
                #Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                ##Pic = ConvertToQtFormat.scaled(200, 150, Qt.KeepAspectRatio)
                Pic = ConvertToQtFormat.scaled(1000, 750, Qt.KeepAspectRatio)
                self.imageUpdate.emit(Pic)

                #fps = int(1 / (time.time() - start_time)) # FPS = 1 / time to process loop
                #print("FPS: ", fps)

                ####

                if (i%40==0):
                    mean=np.mean(img[:,:,0])
                i+=1
                print (mean)

                if (mean==0):
                    ret,th=cv2.threshold(img[:,:,0],210,255,cv2.THRESH_BINARY)
                    ret,mask=cv2.threshold(img[:,:,0],130,255,cv2.THRESH_BINARY)
                    img_masked=cv2.bitwise_or(img[:,:,0],mask)
                    heart=mask-th
                    heart[heart==255]=160
                else:
                    ret,th=cv2.threshold(img[:,:,0],142+mean,255,cv2.THRESH_BINARY)
                    ret,mask=cv2.threshold(img[:,:,0],42+mean,255,cv2.THRESH_BINARY)
                    img_masked=img[:,:,0]-mask
                    heart=mask-th
                #heart[heart==255]=100+mean
    
                img_masked=img[:,:,0]*cv2.bitwise_not(mask)
                mask=cv2.bitwise_not(mask)
                mask[mask==255]=1
                th2=cv2.bitwise_not(th)
                th2[th2==255]=1
                kernel=np.ones((3,3),np.uint8)
                heart_erode=cv2.erode(heart,kernel,iterations=2)
                
                kernel2=np.ones((5,5),np.uint8)

                heart_closed=cv2.morphologyEx(heart_erode,cv2.MORPH_CLOSE,kernel2)
                

                #heart_closed=cv.morphologyEx(heart_closed,cv.MORPH_CLOSE,kernel2)


                heart_closed[heart_closed>0]=120
                #heart_closed[heart_closed==0]=10
                img_b=img[:,:,0]
                img_b[img_b<120]=120
                img_b=img_b-heart_closed

                final=cv2.addWeighted((img_b),0.2,cv.cvtColor(img2,cv.COLOR_BGR2GRAY),0.8,0.0)*th2#*heart#+heart+cv.bitwise_not(th)
                
                final=cv2.resize(final,(frame_width,frame_height),interpolation=cv.INTER_AREA)
                #fpsText = "FPS: " + str(fps)
                #cv.putText(final, fpsText, (10, 50), cv.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3, cv.LINE_AA)
                final=cv.flip(cv.rotate(final,cv.ROTATE_90_CLOCKWISE),1)
                final=cv.cvtColor(final,cv.COLOR_GRAY2BGR)
                final=cv2.flip(final,1)

                #Redimensionnalisation de l'image

                # Alternatives à explorer: 1- Smoothing du threshold (doit etre fait apres le resize)
                # 2-Ajout cathéter en binaire sur l'image fluoro (pas le mm poids que l'autre image)
                # 3-Faire tests après reset de lordinateur et sans autre programmes ouverts
                # Bon Chance 

                if controller.showFps == True:
                    fpsText = "FPS: " + str(fps)
                    cv2.putText(final, fpsText, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 229, 255), 3, cv2.LINE_AA)
                
                ConvertToQtFormat = QImage(final.data, final.shape[1], final.shape[0], QImage.Format_Grayscale8) #Size: (640, 480)
                ##Pic = ConvertToQtFormat.scaled(self.image_label2.width(), self.image_label2.height(), Qt.KeepAspectRatio) 
                #Pic = ConvertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                Pic = ConvertToQtFormat.scaled(1000, 750, Qt.KeepAspectRatio)
                #Pic = ConvertToQtFormat.scaled(200, 150, Qt.KeepAspectRatio)
                self.imageUpdateXray.emit(Pic)

                start_time = time.time()

                #print("FPS: ", int(1 / (time.time() - start_time))) # FPS = 1 / time to process loop
    
    def stop(self):
        self.threadActive = False
        self.quit()

class Camera2_Thread(QThread):
    '''Thread that emits a QT image from camera 2'''
    imageUpdate2 = pyqtSignal(QImage)
    
    def run(self):
        self.threadActive = True
        #VideoDevice2 = 1
        Capture = cv2.VideoCapture(device2)#, cv2.CAP_DSHOW) ##cv2.VideoCapture(0) # Webcam
        
        prev_frame_time = 0
        new_frame_time = 0

        while self.threadActive:
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(Image, 1)

                new_frame_time = time.time()
                fps = int(1/(new_frame_time-prev_frame_time))
                prev_frame_time = new_frame_time

                if controller.showFps == True:
                    fpsText = "FPS: " + str(fps)
                    cv2.putText(FlippedImage, fpsText, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 229, 255), 3, cv2.LINE_AA)
                
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
        #VideoDevice3 = 3
        Capture = cv2.VideoCapture(device3)#, cv2.CAP_DSHOW) ##cv2.VideoCapture(0) # Webcam
        
        prev_frame_time = 0
        new_frame_time = 0

        while self.threadActive:
            ret, frame = Capture.read()
            if ret: # If there is no issue with the capture
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert to RGB
                FlippedImage = cv2.flip(Image, 1)

                new_frame_time = time.time()
                fps = int(1/(new_frame_time-prev_frame_time))
                prev_frame_time = new_frame_time
                
                if controller.showFps == True:
                    fpsText = "FPS: " + str(fps)
                    cv2.putText(FlippedImage, fpsText, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 229, 255), 3, cv2.LINE_AA)
                
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
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) ##

    #from qt_material import apply_stylesheet
    #apply_stylesheet(app, theme='my_theme.xml', extra={'font_size': '18px',})


    #app.setStyleSheet("QLabel{font-size: 18pt;}")
    #app.setStyle("Fusion")

    #dark_palette = QPalette()
    #dark_palette.setColor(QPalette.Window, QColor('#346792'))
    #dark_palette.setColor(QPalette.WindowText, Qt.white)
    #dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    #dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    #dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    #dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    #dark_palette.setColor(QPalette.Text, Qt.white)
    #dark_palette.setColor(QPalette.Button, QColor('#26486B'))
    #dark_palette.setColor(QPalette.ButtonText, Qt.white)
    #dark_palette.setColor(QPalette.BrightText, Qt.red)
    #dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    #dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    #dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    #app.setPalette(dark_palette)

    #app.setStyleSheet("QMainWindow { background-color: #1A72BB }")
    #app.setStyleSheet("QPushButton { background-color: #26486B }")
        #"color: red;"
         #                   "background-color: #7FFFD4;"
          #                   "border-style: solid;"
           #                  "border-width: 2px;"
            #                 "border-color: #FA8072;"
             #                "border-radius: 3px")
    controller = Controller()
    controller.show()
    sys.exit(app.exec_())