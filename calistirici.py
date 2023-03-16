from PyQt5 import QtWidgets, QtCore,QtGui
import sys, io,folium
import cv2
import time
from PyQt5.QtCore import Qt, QPointF, QTimer,QThread,pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog,QTableWidgetItem,QLabel,QGridLayout, QHBoxLayout, QVBoxLayout
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import vtk
from vtk import vtkSTLReader, vtkPolyDataMapper, vtkActor, vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor
from pyqtgraph import ImageView
import numpy as np
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import tomato

from Main_Window import Ui_MainWindow

import csv
import serial
import threading

from pyG5View import pyG5DualStack, g5Width, g5Height
from PyQt5.QtWidgets import QSlider,QMainWindow,QScrollArea
from PyQt5.QtWidgets import  QSpinBox

class AlarmThread(QThread):
    alarm_signal = pyqtSignal(bool)

    def run(self):
        while True:
            self.alarm_signal.emit(True)
            time.sleep(1)
            self.alarm_signal.emit(False)
            time.sleep(1)

class App (QtWidgets.QMainWindow):
    def __init__(self):
        super(App,self).__init__()
        self.ui=Ui_MainWindow()
        #self.timer_graph = QTimer()
        #self.timer_graph.timeout.connect(self.update_graph)
        #self.timer_graph.start(1000) # update every second
        
        # initialize telemetri values
        # self.ui.label_29=QLabel("ALARM: 1 ve 4 Sistem Hatası")
        # self.ui.label_29.setStyleSheet("color: red; font-size: 24pt;")

        # alarm_thread = AlarmThread()
        # alarm_thread.label = self.ui.label_29
        # alarm_thread.start()
        # connect the timer to the update_ui_from_telemetry function
        #self.timer_table = QTimer()
        #self.timer_table.timeout.connect(self.update_ui_from_telemetry)
        #self.timer_table.start(1000)
        #self.telemetri_kaydet()

        # Create alarm thread and connect signal to slot


        self.ui.setupUi(self)
            
        HATA_SOZLUK = {
            "00000": "",
            "00001": "1 Sistem Hatası",
            "00010": "2 Sistem Hatası",
            "00011": "1 ve 2 Sistem Hatası",
            "00100": "3 Sistem Hatası",
            "01000": "4 Sistem Hatası",
            "10000": "5 Sistem Hatası",
            "10010": "1 ve 5 Sistem Hatası",
            "11111": "Tüm sistemlerde hata",
        }

# Hata kontrolü
        hata_kodu = self.telemetri_oku(2)
        if hata_kodu in HATA_SOZLUK:
            hata_mesaji = HATA_SOZLUK[hata_kodu]
        else:
            hata_mesaji = "Sistem Hatası"
        self.ui.label_29.setText(hata_mesaji)
        self.ui.label_29.setStyleSheet("color: red; font-size: 13pt;")
        self.alarm_thread = AlarmThread()
        self.alarm_thread.alarm_signal.connect(self.toggle_label)
        self.alarm_thread.start()

            
        # with open("data.csv", "a", newline='', encoding="utf-8") as myfile:
        #     wr = csv.writer(myfile)
        #     wr.writerow([0,0,0,0,0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0])
        #textlabel

        self.pressure1 = []
        self.pressure2 = []
        self.temperature = []
        self.yuk1 = []
        self.yuk2 = []
        self.iniss = []
        self.paketno = []

        self.text_label()

        #dosya
        self.ui.pushButton.clicked.connect(self.initUI)
        self.ui.pushButton_2.clicked.connect(self.initUI)
        self.ui.pushButton_3.clicked.connect(self.initUI)

        self.ui.pushButton.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.ui.pushButton_2.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.ui.pushButton_3.setStyleSheet("background-color: green; color: white; font-weight: bold;")

        #checkBox
        self.checkBox()


        #self.ui.checkBox.stateChanged.connect(self.onCheckboxChanged)

        #time
        self.date_time_edit = QtWidgets.QDateTimeEdit()
        self.date_time_edit.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        self.dateTime()

        self.create_list()
        #*****************
        #new_pitch_and_roll
        #self.g5View = pyG5DualStack()
        #self.ui.gridLayout_4.addWidget(self.g5View)
        #pitch and roll
        #               self.attitude_indicator = AttitudeIndicator(self.ui.centralwidget)
        #               self.ui.gridLayout_4.addWidget(self.attitude_indicator, 0, 0, 1, 1)
        #self.ui.gridLayout_5.addWidget(self.roll())

        # self.pitch = 0
        # self.roll = 0
        # self.img = QtGui.QPixmap("attitude_indicator.png")
        # self.ui.gridLayout_4.addWidget(self.paintEvent())

        #uydu 3d
        #self.ui.gridLayout_12.addWidget(self.uydu_3d())
        #self.uydu_3d()

        self.ui.gridLayout_6.addWidget(self.location())

        #pil
        self.battery_bar = QtWidgets.QProgressBar(self)
        self.ui.gridLayout_13.addWidget(self.battery_bar)
        
        self.battery_bar.setMinimum(0)
        self.battery_bar.setMaximum(100)
        #self.battery_bar.setValue(int(self.telemetri_oku(11)))
        self.battery_bar.setValue(float(self.telemetri_oku(12)))
        
        self.graph()

        #HATA KODU
        self.change_colors()

        self.image_viewer()
        #camera
        # getting available cameras
        self.available_cameras = QCameraInfo.availableCameras()

        # if no camera found
        if not self.available_cameras:
            # exit the code
            sys.exit()

        # creating a QCameraViewfinder object
        self.viewfinder = QCameraViewfinder()

        # showing this viewfinder
        self.viewfinder.show()

        # grid_layout = QGridLayout()

        self.ui.gridLayout_3.addWidget(self.viewfinder)
        #self.setLayout(grid_layout)

        # making it central widget of main window
        #self.setCentralWidget(self.viewfinder)
        self.viewfinder.setGeometry(300, 300, 300, 300)
        self.ui.centralwidget
        
        self.select_camera(0)
        #self.kamera()

    def toggle_label(self, visible):
        self.ui.label_29.setVisible(visible)
    
    def dateTime(self):
        self.date_time_edit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.ui.dateTimeEdit.setDateTime(self.date_time_edit.dateTime())

    def text_label(self):
        self.ui.takimno.setText(QLabel("22113").text())
        self.ui.paketno.setText(self.telemetri_oku(0))
        self.ui.hata_kodu.setText(self.telemetri_oku(2))
        self.ui.gonderimzamani.setText(self.telemetri_oku(3))
        self.ui.gonderimtarihi.setText(self.telemetri_oku(4))

        self.ui.basinc.setText(self.telemetri_oku(5))
        self.ui.basinc2.setText(self.telemetri_oku(6))

        self.ui.yukseklik.setText(self.telemetri_oku(7))
        self.ui.yukseklik2.setText(self.telemetri_oku(8))

        self.ui.irtifa_fark.setText(self.telemetri_oku(9))
        self.ui.inis.setText(self.telemetri_oku(10))
        self.ui.sicaklik.setText(self.telemetri_oku(11))
        self.ui.pil_gerilimi.setText(self.telemetri_oku(12))
        self.ui.gps_lat.setText(self.telemetri_oku(13))
        self.ui.gps_long.setText(self.telemetri_oku(14))
        self.ui.gps_alt.setText(self.telemetri_oku(15))

        #uydu statüsü
        status_dict = {
                0: "Uçuşa Hazır", #(Roket Ateşlenmeden Önce)
                1: "Yükselme",
                2: "Model Uydu İniş",
                3: "Ayrılma",
                4: "Görev Yükü İniş",
                5: "Kurtarma (Görev Yükü’nün Yere Teması)",
                6: "Paket Video (500 KB) Alındı",
                7: "Paket Video (500 KB) Gönderildi (Bonus Görev)"
            }
        self.received_number =int(self.telemetri_oku(1))
        status = status_dict.get(self.received_number, "Geçersiz sayı")
        self.ui.uydu_durumu_2.setText(status)

        #video durumu
        video_durumu=False
        self.ui.video_durumu.setText(str(video_durumu))


    def initUI(self):
        self.ui.pushButton.clicked.connect(self.showDialog_sim)
        self.ui.pushButton_2.clicked.connect(self.showDialog_video)
        self.ui.pushButton_3.clicked.connect(self.showDialog_manuel)
        

    def showDialog_sim(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')

        if fname[0]:
            with open(fname[0], 'r', encoding='utf-8') as f:
                data = f.read()
                print(data)

    def showDialog_video(self):
        # Dosya Seçme Penceresi
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Video Dosyası Seç", "",
                                                  "Video Dosyası (*.mp4 *.avi *.mov);;All Files (*)", options=options)
        if fileName:
            print(fileName)

    def showDialog_manuel(self):
        print("my_other_function() fonksiyonu çalıştı.")    
        self.xbee_send_data() 
    
    # def onCheckboxChanged(self):
    #     if state == self.received_number:
    #         self.checkBox.setText(self.status_dict[self.received_number])
    #     else:
    #         self.checkBox.setText("")
    def update_ui_from_telemetry(self):
        paket_no = self.telemetri_oku(0)
        uydu_status = self.telemetri_oku(1)
        hata_kodu = self.telemetri_oku(2)
        gonderim_zamani = self.telemetri_oku(3)
        gonderim_tarihi = self.telemetri_oku(4)
        basinc1 = self.telemetri_oku(5)
        basinc2 = self.telemetri_oku(6)
        yukseklik1 = self.telemetri_oku(7)
        yukseklik2 = self.telemetri_oku(8)
        irtifa_fark = self.telemetri_oku(9)
        inis_hizi = self.telemetri_oku(10)
        sicaklik = self.telemetri_oku(11)
        pil = self.telemetri_oku(12)
        latitude = self.telemetri_oku(13)
        longitude = self.telemetri_oku(14)
        altitude = self.telemetri_oku(15)

        # update the table with the telemetry values
        row_count = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row_count)
        values = [paket_no, uydu_status, gonderim_zamani, gonderim_tarihi, basinc1, basinc2, yukseklik1, yukseklik2,
                irtifa_fark, inis_hizi, sicaklik, pil, latitude, longitude, altitude, "VideoStatü"]
        for i in range(self.ui.tableWidget.columnCount()):
            item = QtWidgets.QTableWidgetItem(str(values[i]))
            self.ui.tableWidget.setItem(row_count, i, item)

        # update the telemetry labels
        self.ui.takimno.setText("22113")
        self.ui.paketno.setText(paket_no)
        self.ui.hata_kodu.setText(hata_kodu)
        self.ui.gonderimzamani.setText(gonderim_zamani)
        self.ui.gonderimtarihi.setText(gonderim_tarihi)
        self.ui.basinc.setText(basinc1)
        self.ui.basinc2.setText(basinc2)
        self.ui.yukseklik.setText(yukseklik1)
        self.ui.yukseklik2.setText(yukseklik2)
        self.ui.irtifa_fark.setText(irtifa_fark)
        self.ui.inis.setText(inis_hizi)
        self.ui.sicaklik.setText(sicaklik)
        self.ui.pil_gerilimi.setText(pil)
        self.ui.gps_lat.setText(latitude)
        self.ui.gps_long.setText(longitude)
        self.ui.gps_alt.setText(altitude)

    def create_list(self):
        self.ui.tableWidget.setColumnCount(16)
        self.ui.tableWidget.setHorizontalHeaderLabels(('PaketNo', 'UyduStatü', 'Zaman', 'Tarih', 'Basınç1', 'Basınç2', 'Yükseklik1', 'Yükseklik2', 'İrtifaFark', 'İnişHızı', 'Sıcaklık', 'Pil', 'Latitude', 'Longitude', 'Altitude', 'VideoStatü'))
        for column in range(self.ui.tableWidget.columnCount()):
            self.ui.tableWidget.setColumnWidth(column, 53)
            
    def checkBox(self):
        if int(self.telemetri_oku(1)) == 0:
            self.ui.checkBox_3.setChecked(True)
        elif int(self.telemetri_oku(1)) == 1:
            self.ui.checkBox_4.setChecked(True)
        elif int(self.telemetri_oku(1)) == 2:
            self.ui.checkBox_8.setChecked(True)
        elif int(self.telemetri_oku(1)) == 3:
            self.ui.checkBox_7.setChecked(True)
        elif int(self.telemetri_oku(1)) == 4:
            self.ui.checkBox_6.setChecked(True)
        elif int(self.telemetri_oku(1)) == 5:
            self.ui.checkBox_5.setChecked(True)
        elif int(self.telemetri_oku(1)) == 6:
            self.ui.checkBox_2.setChecked(True)
        elif int(self.telemetri_oku(1)) == 7:
            self.ui.checkBox.setChecked(True)
    # method to select camera
    def select_camera(self, i):
        # getting the selected camera
        self.camera = QCamera(self.available_cameras[i])

        # setting view finder to the camera
        self.camera.setViewfinder(self.viewfinder)

        # setting capture mode to the camera
        self.camera.setCaptureMode(QCamera.CaptureStillImage)

        # if any error occur show the alert
        self.camera.error.connect(lambda: self.alert(self.camera.errorString()))

        # start the camera
        self.camera.start()

        # creating a QCameraImageCapture object
        self.capture = QCameraImageCapture(self.camera)

        # showing alert if error occur
        self.capture.error.connect(lambda error_msg, error,
                                msg: self.alert(msg))

        # when image captured showing message
        self.capture.imageCaptured.connect(lambda d,
                                        i: self.status.showMessage("Image captured : "
                                                                    + str(self.save_seq)))

        # getting current camera name
        self.current_camera_name = self.available_cameras[i].description()

        # initial save sequence
        self.save_seq = 0

    def location(self):
        coordinate = (41.027557,28.884985)
        m = folium.Map(
        	zoom_start=13,
        	location=coordinate
        )
        data = io.BytesIO()
        m.save(data, close_file=False)

        self.webView = QWebEngineView()
        self.webView.setHtml(data.getvalue().decode())

        return self.webView

    def image_viewer(self):
        # Generate a 3D numpy array for the image
        self.image = np.random.rand(100,100,100)

        # Create an ImageView widget and set the image data
        self.image_view = ImageView()
        self.image_view.setImage(self.image)

        # Add the ImageView widget to the layout
        #self.ui.gridLayout_12.addWidget(self.image_view)
    def update_graph(self):
        # Anlık veriyi al
        pressure1_value = float(self.telemetri_oku(5))
        pressure2_value = float(self.telemetri_oku(6))
        temperature_value = float(self.telemetri_oku(7))
        yuk1_value = float(self.telemetri_oku(8))
        yuk2_value = float(self.telemetri_oku(9))
        iniss_value = float(self.telemetri_oku(10))
        paketno_value = int(self.telemetri_oku(0))
        
        # Veri noktalarını sakla
        self.pressure1.append(pressure1_value)
        self.pressure2.append(pressure2_value)
        self.temperature.append(temperature_value)
        self.yuk1.append(yuk1_value)
        self.yuk2.append(yuk2_value)
        self.iniss.append(iniss_value)
        self.paketno.append(paketno_value)

        # En son 5 veriyi sakla
        num_points_to_display = 5
        if len(self.pressure1) > num_points_to_display:
            self.pressure1 = self.pressure1[-num_points_to_display:]
            self.pressure2 = self.pressure2[-num_points_to_display:]
            self.temperature = self.temperature[-num_points_to_display:]
            self.yuk1 = self.yuk1[-num_points_to_display:]
            self.yuk2 = self.yuk2[-num_points_to_display:]
            self.iniss = self.iniss[-num_points_to_display:]
            self.paketno = self.paketno[-num_points_to_display:]
        
        # Grafikleri güncelle
        self.graph_widget.plot(self.paketno, self.pressure1,pen="#006400",symbol='o', symbolBrush="#006400", clear=True)
        self.graph_widget1.plot(self.paketno, self.pressure2,pen="#006400",symbol='o', symbolBrush='#006400', clear=True)
        self.graph_widget2.plot(self.paketno, self.yuk1,pen="#006400",symbol='o', symbolBrush='#006400', clear=True)
        self.graph_widget3.plot(self.paketno, self.yuk2,pen="#006400",symbol='o', symbolBrush='#006400', clear=True)
        self.graph_widget4.plot(self.paketno, self.temperature,pen="#006400",symbol='o', symbolBrush='#006400', clear=True)
        self.graph_widget5.plot(self.paketno, self.iniss,pen="#006400",symbol='o', symbolBrush='#006400', clear=True)

    def graph(self):
        self.pressure1.append(float(self.telemetri_oku(5)))  
        self.pressure2.append(float(self.telemetri_oku(6)))
        self.temperature.append(float(self.telemetri_oku(7)))
        self.yuk1.append(float(self.telemetri_oku(8)))
        self.yuk2.append(float(self.telemetri_oku(9)))
        self.iniss.append(float(self.telemetri_oku(10)))
        self.paketno.append(int(self.telemetri_oku(0)))

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.plot(self.paketno, self.pressure1,pen="#006400",symbol='o', symbolBrush="#006400")
        self.graph_widget.setBackground('w')
        self.graph_widget.setLabel('left', "Pressure1", units='Pa')
        self.graph_widget.setLabel('bottom', "Paketno")

        self.graph_widget1 = pg.PlotWidget()
        self.graph_widget1.plot(self.paketno, self.pressure2,pen="#006400",symbol='o', symbolBrush='#006400')
        self.graph_widget1.setBackground('w')
        self.graph_widget1.setLabel('left', "Pressure2", units='Pa')
        self.graph_widget1.setLabel('bottom', "Paketno")

        self.graph_widget2 = pg.PlotWidget()
        self.graph_widget2.plot(self.paketno, self.yuk1,pen="#006400",symbol='o', symbolBrush='#006400')
        self.graph_widget2.setBackground('w')
        self.graph_widget2.setLabel('left', "Yükseklik1")
        self.graph_widget2.setLabel('bottom', "Paketno")

        self.graph_widget3 = pg.PlotWidget()
        self.graph_widget3.plot(self.paketno, self.yuk2,pen="#006400",symbol='o', symbolBrush='#006400')
        self.graph_widget3.setBackground('w')
        self.graph_widget3.setLabel('left', "Yükseklik2")
        self.graph_widget3.setLabel('bottom', "Paketno")
        
        self.graph_widget4 = pg.PlotWidget()
        self.graph_widget4.plot(self.paketno, self.temperature,pen="#006400",symbol='o', symbolBrush='#006400')
        self.graph_widget4.setBackground('w')
        self.graph_widget4.setLabel('left', "Sicaklik")
        self.graph_widget4.setLabel('bottom', "Paketno")

        self.graph_widget5 = pg.PlotWidget()
        self.graph_widget5.plot(self.paketno, self.iniss,pen="#006400",symbol='o', symbolBrush='#006400')
        self.graph_widget5.setBackground('w')
        self.graph_widget5.setLabel('left', "İniş Hizi")
        self.graph_widget5.setLabel('bottom', "Paketno")

        #2basınc 1yük 1iniş 1sıc 

        self.ui.gridLayout.addWidget(self.graph_widget)
        self.ui.gridLayout_11.addWidget(self.graph_widget1)
        self.ui.gridLayout_7.addWidget(self.graph_widget2)
        self.ui.gridLayout_10.addWidget(self.graph_widget3)
        self.ui.gridLayout_9.addWidget(self.graph_widget4)
        self.ui.gridLayout_8.addWidget(self.graph_widget5)
    
    #hata kodu
    def change_colors(self):
        self.hata_kodu_liste = []
        for karakter in self.telemetri_oku(2):
            self.hata_kodu_liste.append(karakter)
        sayac=1

        self.ui.label_23.setStyleSheet("background-color: green")
        self.ui.label_21.setStyleSheet("background-color: green")
        self.ui.label_19.setStyleSheet("background-color: green")
        self.ui.label_15.setStyleSheet("background-color: green")
        self.ui.label_11.setStyleSheet("background-color: green")

        for i in self.hata_kodu_liste:
            if i=="1":
                if sayac==1:
                    self.ui.label_23.setStyleSheet("background-color: red")
                elif sayac==2:
                    self.ui.label_21.setStyleSheet("background-color: red")
                elif sayac==3:
                    self.ui.label_19.setStyleSheet("background-color: red")
                elif sayac==4:
                    self.ui.label_15.setStyleSheet("background-color: red")
                elif sayac==5:
                    self.ui.label_11.setStyleSheet("background-color: red")
            sayac+=1
    
    def uydu_3d(self):
        self.vtkWidget = QVTKRenderWindowInteractor(self.ui.frame_2)
        self.ui.verticalLayout_2.addWidget(self.vtkWidget)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.ren.SetBackground(1, 1, 1)
 
        # Create source
        source = vtkSTLReader()
        source.SetFileName("taşıyıcı_montaj_son .stl")
 
        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
 
        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(tomato)
        actor.RotateX(70.)
        actor.RotateY(-60.)
 
        self.ren.AddActor(actor)
 
        self.ren.ResetCamera()
 
        self.show()
        self.iren.Initialize()
    
    def kamera(self):
        # self.vtkWidget = QVTKRenderWindowInteractor(self)
        # self.ren = vtk.vtkRenderer()
        # self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        # self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Kamera bağlantısı oluştur
        self.camera = cv2.VideoCapture(0)

        # Kamerayı arayüze ekle
        self.ui.gridLayout_5.addWidget(self.ui.frame_3)

        # Arayüzü oluştur ve göster
        self.setCentralWidget(self.vtkWidget)
        self.show()
        self.iren.Initialize()

        # Kamerayı çalıştır
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)

    def update_frame(self):
        _, frame = self.camera.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = QtGui.QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QtGui.QImage.Format_RGB888)
        self.ui.frame_3.setPixmap(QtGui.QPixmap.fromImage(frame))

    # def controlWidgetGen(self,control):
    #     layout = QGridLayout()

    #     w = QWidget()
    #     w.setLayout(layout)

    #     layout.addWidget(QLabel(self.control["name"], parent=w), 0, 0)

    #     slider = QSlider(Qt.Horizontal, parent=w)
    #     slider.setRange(self.control["min"], self.control["max"])

    #     spinbox = QSpinBox(parent=w)
    #     spinbox.setRange(self.control["min"], self. control["max"])

    #     slider.valueChanged.connect(spinbox.setValue)
    #     spinbox.valueChanged.connect(slider.setValue)

    #     layout.addWidget(slider, 0, 1)
    #     layout.addWidget(spinbox, 0, 2)

    #     return (w, slider)

    # def telemetri_kaydet(self):
    #     ser = serial.Serial('COM3', 9600)
    #     while True:
    #         data = ser.readline().decode().strip().split(',')
    #         with open("data.csv", "a", encoding="utf-8", newline='') as myfile:
    #             wr = csv.writer(myfile)
    #             wr.writerows([data])
    #             myfile.close()
    def telemetri_oku(self,index_y):
        with open('data.csv') as file:
            content = file.readlines()
            rows = [row.strip().split(',') for row in content]
            index_x = len(rows) - 1
            return rows[index_x][index_y]
    
    def xbee_send_data(self):
        ser = serial.Serial('COM7', 9600)  # port ve baud rate'i kendinize göre ayarlayın
        data = "1"
        #print(ser.is_open())
        ser.write(data.encode())
        ser.close()

# class AlarmThread(QThread):
#     def __init__(self, label):
#         super().__init__()
#         self.label = label

#     def run(self):
#         while True:
#             self.label.setVisible(not self.label.isVisible())
#             time.sleep(1)
class UpdateValueThread(QThread):
    valueChanged = pyqtSignal()

    def __init__(self, parent=None):
        super(UpdateValueThread, self).__init__(parent)

    def run(self):
        temp1 = 0
        temp2 = 0
        while True:
            temp1 = (temp1+1)%10
            temp2 = -((-temp2+1)%10)
            # The value is updated in this loop.
            # Here I'm just increasing it by 1 every second.
            g5View.pyG5AI.setValues(temp1, temp2)
            self.valueChanged.emit()
            time.sleep(1)
            
class AttitudeIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pitch = 70
        self.roll = 50
        self.img = QtGui.QPixmap("attitude_indicator_ic.png")
    
    def resizeEvent(self, event):
        self.img = self.img.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(-self.pitch)
        painter.drawPixmap(-self.img.rect().center(), self.img)

    def setPitch(self, pitch):
        self.pitch = pitch
        self.update()

    def setRoll(self, roll):
        self.roll = roll
        self.update()


def telemetri_kaydet():
        ser = serial.Serial('COM3', 9600)
        while True:
            data = ser.readline().decode().strip().split(',')
            with open("data.csv", "a", encoding="utf-8", newline='') as myfile:
                wr = csv.writer(myfile)
                wr.writerows([data])
                myfile.close()
def my_app():
    app=QtWidgets.QApplication(sys.argv)
    win=App()

    # win.ui.label_29=QLabel("ALARM: 1 ve 4 Sistem Hatası")
    # win.ui.label_29.setStyleSheet("color: red; font-size: 24pt;")

    # alarm_thread = AlarmThread(win.ui.label_29)
    # alarm_thread.start()
    #win.setStyleSheet("font-weight: bold;background-color: orange;")
    win.show()
    #telemetri_thread = threading.Thread(target=telemetri_kaydet)
    #telemetri_thread.start()

    timer_list = [QTimer(), QTimer(), QTimer(),QTimer(),QTimer()]

    timer_list[0].timeout.connect(win.text_label)
    timer_list[1].timeout.connect(win.update_graph)
    timer_list[2].timeout.connect(win.update_ui_from_telemetry)
    timer_list[3].timeout.connect(win.dateTime)
    timer_list[4].timeout.connect(win.xbee_send_data)

    for i, timer in enumerate(timer_list):
        interval = (i + 1) * 1000  # Interval increases for each timer
        timer.setInterval(interval)
        timer.start()

    w = QMainWindow()

    # Set window size.
    w.resize(g5Width, g5Height)

    hlayout = QHBoxLayout()
    mainWidget = QWidget()
    mainWidget.setLayout(hlayout)

    scrollArea = QScrollArea(w)
    controlWidget = QWidget(w)
    scrollArea.setWidget(controlWidget)
    scrollArea.setFixedWidth(380)
    scrollArea.setMinimumHeight(160)
    scrollArea.setWidgetResizable(True)
    scrollArea.setObjectName("scrollArea")
    controlVLayout = QVBoxLayout()
    controlWidget.setLayout(controlVLayout)

    g5View = pyG5DualStack()
    hlayout.addWidget(g5View)

    w.setCentralWidget(mainWidget)

    # Create the thread to update the value, and connect its signal to the label's setText slot
    thread = UpdateValueThread()
    thread.valueChanged.connect(lambda: mainWidget.update())

    # Start the thread
    thread.start()
    w.show()
    #------------------------
    # r = QMainWindow()
    # hlayout = QHBoxLayout()
    # mainWidget = QWidget()
    # mainWidget.setLayout(hlayout)
    # scrollArea = QScrollArea(r)
    # controlWidget = QWidget(r)
    # scrollArea.setWidget(controlWidget)
    # scrollArea.setFixedWidth(380)
    # scrollArea.setMinimumHeight(160)
    # scrollArea.setWidgetResizable(True)
    # scrollArea.setObjectName("scrollArea")
    # controlVLayout = QVBoxLayout()
    # controlWidget.setLayout(controlVLayout)
    # hlayout.addWidget(scrollArea)
    # # select only pitch and roll controls
    # controls = [
    #     {"name": "pitchAngle", "min": -25, "max": 25},
    #     {"name": "rollAngle", "min": -70, "max": 70},
    # ]
    
    # for win.control in controls:
    #     widget, slider = win.controlWidgetGen(win.control)
    #     try:
    #         slider.valueChanged.connect(getattr(win.g5View.pyG5AI, win.control["name"]))
    #         print("Slider connected: {}".format(win.control["name"]))
    #     except Exception as inst:
    #         print("{} control not connected to view: {}".format(win.control["name"], inst))

    #     controlVLayout.addWidget(widget)
    # controlVLayout.addStretch()

    # r.setCentralWidget(mainWidget)
    # r.show()
    #------------------------
    sys.exit(app.exec())

if __name__ == '__main__':
    my_app()
