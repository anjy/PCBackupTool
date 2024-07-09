import sys
import requests
import json
import mysql.connector 
import pandas as pd
import numpy as np
import os
import psutil
import shutil
import zipfile
import json
from datetime import datetime
from schedule_model import ScheduleModel
from PIL import Image
from PIL.ExifTags import TAGS , GPSTAGS
from mysql.connector import Error #1234
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from bs4 import BeautifulSoup
from PyQt5.QtWidgets  import QApplication , QMainWindow , QVBoxLayout , QWidget , QPushButton, QFileDialog, QTableWidget, QTableWidgetItem 
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QAbstractTableModel, Qt
#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("file_backup.ui")[0]

#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.fontSize = 10
        self.counter = 0
        self.maxSchedule = 3 # 최대 저장 스케쥴수 
        
        self.settings_file = "settings.json"
        self.comb_1.addItems(["Select","Every Hour","Every Day","Every Week"])
        self.comb_2.addItems(["Sun","Mon","Tue","Wed","Thu","Fri","Sat"])
        
        self.jsonData =''
        self.source_dir=''
        self.target_dir=''
        '''
            화면설정
        '''   
        
        # 요일,시간 선택 기본은 선택 불가
        self.comb_2.setEnabled(False)
        self.timeEdit.setEnabled(False)  
           
        # 기본 백업시간은 '시:분' 만 표시
        self.timeEdit.setDisplayFormat('hh:mm')
        
        # 스케쥴 유형 변경시 스케쥴 유형들 변경
        self.comb_1.currentIndexChanged.connect(self.change_schedule_type)
        
        
        
        '''
            이벤트 설정
        '''
        # 스케쥴 저장버튼(SAVE) 클릭
        self.btn_save.clicked.connect(self.save_setting)
        
              
       
        self.model_tgt = QFileSystemModel()
        self.model_tgt.setRootPath('C:/')
        
        self.model_dst = QFileSystemModel()
        self.model_dst.setRootPath('C:/')
        
        
        self.treeView_tgt.setModel(self.model_tgt)
        self.treeView_tgt.setRootIndex(self.model_tgt.index('C:/'))
        
        self.treeView_dst.setModel(self.model_dst)
        self.treeView_dst.setRootIndex(self.model_dst.index('C:/'))
        
        # 타겟드라이브 선택 콤보
        self.drive_combo_tgt.addItems(self.get_drives())
        self.drive_combo_tgt.currentIndexChanged.connect(self.update_tree_view)
        
        # 목표 드라이브 선택 콤보
        self.drive_combo_dst.addItems(self.get_drives())
        self.drive_combo_dst.currentIndexChanged.connect(self.update_tree_dst_view)
        
        # 복사버튼
        self.btn_copy.clicked.connect(self.copy_item)
        
        # 트레이아이콘
        # System Tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icontray.png"))  # Set your own icon here
        self.tray_icon.setVisible(True)
        
        tray_menu = QMenu(self)
        restore_action = QAction("Restore", self)
        quit_action = QAction("Quit", self)

        restore_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # Override close event
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        
        # tree view column 넓이
        # Set column width for "name" column
        self.treeView_tgt.setColumnWidth(0, 250)
        self.treeView_dst.setColumnWidth(0, 250)
        
       # self.model = QStandardItemModel()
       # self.model.setHorizontalHeaderLabels(['type', 'time', 'path'])
        
        self.schedule = [
            {"type": "매일", "time": "12:00", "path": "C:/aaa"},
            {"type": "매주", "time": "15:30", "path": "C:/bbb"}
        ]
         # Load settings
        self.schedule = self.load_settings()
        self.model = ScheduleModel(self.schedule)
        
        self.tableView_todo.setColumnWidth(0, 100)
        self.tableView_todo.setColumnWidth(1, 100)
        self.tableView_todo.setColumnWidth(2, 100)
        self.tableView_todo.setColumnWidth(3, 150)
        self.tableView_todo.setColumnWidth(4, 150)  
        self.tableView_todo.setColumnWidth(5, 80)  # 삭제 버튼용
        
        # START 클릭시 타이머 시작
        self.btn_get_status.clicked.connect(self.start_timer)
        
        # STOP 클릭시 타이머 종료
        self.btn_stop_status.clicked.connect(self.stop_timer)
        
        # 타이머 : 1초마다 체크
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_time)

        self.copy_in_progress = False  # 복사 작업 중인지 여부를 나타내는 변수
        self.timer_started = False     # 타이머 시작 여부를 나타내는 변수
    
    # 스케쥴 유형 변경시 콤보 형식등 변경 
    def change_schedule_type(self):
        
        self.comb_2.setEnabled(False)
        self.timeEdit.setEnabled(False)
        
        # 유형별 시간포멧 등
        type1 = self.comb_1.currentText()
        if 'Hour' in type1 :
            self.timeEdit.setEnabled(True)
            self.timeEdit.setDisplayFormat('mm')
            self.label_time.setText('mm')
            
        elif 'Day' in type1:
            self.timeEdit.setEnabled(True)
            self.timeEdit.setDisplayFormat('hh:mm')
            self.label_time.setText('hh:mm')
        elif 'Week' in type1:
            self.comb_2.setEnabled(True)
            self.timeEdit.setEnabled(True)
            self.timeEdit.setDisplayFormat('hh:mm')
            self.label_time.setText('hh:mm')
        else:
            self.timeEdit.setEnabled(False)
            self.label_time.setText('')
            
            
    
    # START 버튼 클릭시 타이머 Start
    def start_timer(self):
        if not self.timer_started:
            self.timer.start(1000) # 1초마다 체크
            self.timer_started = True
            self.btn_get_status.setEnabled(False) # START 버튼 비활성화
            QMessageBox.warning(self, "Warning", "Started Timer.")
     
    # STOP 버튼 클릭시 타이머 stop       
    def stop_timer(self):
        if self.timer_started:  
            self.timer.stop()
            self.timer_started = False
            self.btn_get_status.setEnabled(True) # START 버튼 활성화
            QMessageBox.warning(self, "Warning", "Stop Timer.")
            
    def check_time(self):
        '''
        import string
        import random
        letters = string.ascii_letters
        result_str = ''.join(random.choice(letters) for i in range(6))
        print(f'check_time : {result_str}')
        '''
        self.counter += 1
        self.lcd_timer.display(self.counter)
        
        '''
        current_time = datetime.now().strftime("%H:%M:%S")

        # JSON 데이터에서 시간 정보 추출
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        time_str = data["time"]

        if current_time == time_str and not self.copy_in_progress:
            self.label.setText("파일 압축 복사 작업을 실행합니다.")
            self.copy_files()
        '''
        
        #print(f' >>>> {self.jsonData}')
       
        # 현재 시간 정보
        now = datetime.now()
        current_minute = now.strftime("%M:%S")
        current_hour_minute = now.strftime("%H:%M:%S")
        current_weekday = now.strftime("%a")  # 'Mon', 'Tue', 'Wed', ..., 'Sun'
        
        
        # 설정된 시간 비교
        for setting in self.jsonData["settings"]:
            time_setting = datetime.strptime(setting["time"], "%H:%M:%S")
            setting_minute = time_setting.strftime("%M:00")
            setting_hour_minute = time_setting.strftime("%H:%M:00")
            setting_day = setting["Type2"]  # 요일, 예: 'Mon'
            setting_source_dir =  setting["Source Path"]
            setting_target_dir =  setting["Target Path"]   
            
            
            if "Hour" in setting["Type1"]:
                print(f"####{current_minute}/{setting_minute}")
                # 매시간 분 비교
                if current_minute == setting_minute:
                    self.copy_item(setting_source_dir,setting_target_dir)
                    print(f"Every Hour Match Found: {setting['time']}")
                else:
                    print("Hour Not Matched")

            elif "Day" in setting["Type1"]:
                
                
                # 매일 시:분 비교
                if current_hour_minute == setting_hour_minute:
                    self.copy_item(setting_source_dir,setting_target_dir)
                    print(f"Every Day Match Found: {setting['time']}")
                else:
                    print("Day Not Matched")

            elif "Week" in setting["Type1"]:
                # 매주 특정 요일과 시:분 비교
                if current_weekday == setting_day and current_hour_minute == setting_hour_minute:
                    self.copy_item(setting_source_dir,setting_target_dir)
                    print(f"Every Week Match Found on {setting_day}: {setting['time']}")
                else:
                    print("Week Not Matched")
            else:
                print('Not Matched Schedule')
                  
    # 정상 크기로 복원
    def on_tray_icon_activated(self, reason):
        """ Handle tray icon activation event """
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()  
            
    def closeEvent(self, event):
        """ Override close event to hide the window instead of closing it """
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Tray Program",
            "Application was minimized to Tray",
            QSystemTrayIcon.Information,
            2000
        )  
        
    # 파일 백업         
    def copy_item(self , source_path ,target_path ) :
        

        if not source_path or not target_path:
            QMessageBox.warning(self, "Warning", "Please select a source file/folder and a destination folder.")
            return

        
        zip_filename = os.path.join(target_path, f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")
        '''
        # 압축 : 다만 이경우 다른 프로세스가 사용중이라고 하고 빈파일만 생김(permission 오류 발생)
        try:
             # Create Zip file
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for filename in os.listdir(source_path):
                    source_file = os.path.join(source_path, filename)
                    if os.path.isfile(source_file):
                        zipf.write(source_file, os.path.basename(source_file))
                        print(f"File '{filename}' added to the zip file.")

            print(f"Zip file '{os.path.basename(zip_filename)}' created.")
            
           # Copy the zip file to the target directory
            try:
                shutil.copy2(zip_filename, os.path.join(target_path, os.path.basename(zip_filename)))
                print(f"Zip file '{os.path.basename(zip_filename)}' copied to {target_path}.")
                print(f"File compression and copy operation completed.")
            except PermissionError:
                print(f"Permission error: The file '{os.path.basename(zip_filename)}' is being used by another process.")
                print(f"Permission error: The file '{os.path.basename(zip_filename)}' is being used by another process.")
            except Exception as e:
                print(f"An error occurred during copying: {str(e)}")
                print("An error occurred during copying.")

            print(f"File compression and copy operation completed.")
        except Exception as e:
            print(f"An error occurred during copying: {str(e)}")            
        
        '''
        # 압축 없이 복사만
        if os.path.isfile(source_path):
            if os.path.isfile(target_path) :
                shutil.copy(source_path , target_path)
            else:
                QMessageBox.warning(self, "Warning", "Destination must be a folder.")
        elif os.path.isdir(source_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst_folder = os.path.join(target_path , os.path.basename(source_path))
            dst_folder += f'_{timestamp}'
            #datetime.now().strftime("%Y%m%d_%H%M%S")
            if not os.path.exists(dst_folder):
                shutil.copytree(source_path , dst_folder)
            else:
                QMessageBox.warning(self, "Warning", "Folder already exists at the destination.")
        else:
            QMessageBox.warning(self, "Warning", "Invalid source selected.")
        print("Success")
        
        
    def get_drives(self):
        """ Get available drives in the system """
        if sys.platform == "win32":
            import string
            from ctypes import windll

            drives = []
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:\\")
                bitmask >>= 1
            return drives
        else:
            return ["/"]  # Unix-like systems
        
    def update_tree_view(self , type):
        """ Update the TreeView based on selected drive """
        selected_drive = self.drive_combo_tgt.currentText()
        self.treeView_tgt.setRootIndex(self.model_tgt.index(selected_drive))
       
            
    def update_tree_dst_view(self , type):
        """ Update the TreeView based on selected drive """
        selected_drive = self.drive_combo_dst.currentText()
        self.treeView_dst.setRootIndex(self.model_dst.index(selected_drive))
    
    def validate_schedule(self, add_type1 , add_type2 , time , dir):
        print("Validate save information")

    # save schedules    
    def save_setting(self):
        
        index1 = self.treeView_tgt.currentIndex()
        index2 = self.treeView_dst.currentIndex()
        
        type1 = self.comb_1.currentText()
        
        if 'Week' in type1:
            type2 = self.comb_2.currentText()
        elif 'Select' in type1   :
            QMessageBox.warning(self, "No Selection", "Schedule items must be selected")
            return
        else:
            type2=''
            
        '''
        print(f'>> 1 {index1.isValid()}')
        print(f'>> 2 {index2.isValid()}')
        print(self.model_tgt.filePath(index1))
        print(self.model_dst.filePath(index2))
        '''

        # 저장할때 백업대상과 백업이 저장될 폴더가 선택 되어야 함.
        if not index1.isValid() or not index2.isValid():
            QMessageBox.warning(self, "No Selection", "Both items must be selected")
            return
            
    
        # 파일이 존재하지 않으면 빈 배열로 초기화하여 생성
        if not os.path.exists(self.settings_file):
            initial_data = {"settings": []}
            with open(self.settings_file, 'w', encoding='utf-8') as file:
                json.dump(initial_data, file, ensure_ascii=False, indent=4)
        
        # 기존 JSON 데이터를 로드
        with open(self.settings_file, 'r', encoding='utf-8') as file:
            data = json.load(file)


        # 스케쥴은 최대 self.maxSchedule 숫자만큼 저장가능
        if len(data['settings']) > self.maxSchedule-1 :
            QMessageBox.warning(self, "Over Max Schedule", "You can save up to three schedules.")
            return
        

        save_time = self.timeEdit.time().toString()
        save_src_dir = self.model_tgt.filePath(index1)
        save_tgt_dir = self.model_tgt.filePath(index2)

        # 저장데이타
        new_entry = {
                    "Type1": type1 , 
                    "Type2": type2 , 
                    "time": save_time, 
                    "Source Path":save_src_dir,
                    "Target Path":save_tgt_dir,
                   }
        # 중복입력 체크 : TODO Type1 별로 나눠야됨
        for valid in data:
            if valid['Type1'] == type1 and valid['Type2'] == type2  and valid['time'] == save_time and valid['Source Path'] == save_src_dir and valid['Target Path'] == save_tgt_dir :
                return False
            

        # "settings" 키에 새로운 항목 추가
        data["settings"].append(new_entry)
        
        
        # 수정된 데이터를 다시 JSON 파일에 저장
        with open(self.settings_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
       
        self.load_settings()
            
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
    
  
        
    def load_settings(self):
        
        # 파일이 존재하지 않으면 빈 배열로 초기화하여 생성
        if not os.path.exists(self.settings_file):
            initial_data = {"settings": []}
            with open(self.settings_file, 'w', encoding='utf-8') as file:
                json.dump(initial_data, file, ensure_ascii=False, indent=4)
        
        # 기존 JSON 데이터를 로드
        with open(self.settings_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        self.jsonData = data
            
        # 데이터를 pandas DataFrame으로 변환
        df = pd.DataFrame(data["settings"])
        
        
        self.model = PandasModel(df)
        self.tableView_todo.setModel(self.model)


        # Index Widget을 사용하여 버튼 추가
        for row in range(self.model.rowCount()):
            btn_delete = QPushButton('Delete', self)
            btn_delete.clicked.connect(lambda ch, row=row: self.delete_row(row))
            self.tableView_todo.setIndexWidget(self.model.index(row, df.shape[1]), btn_delete)

        # 컬럼 크기 조정
        self.tableView_todo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


        '''
        # Index Widget을 사용하여 버튼 추가
        btn_delete = QPushButton('Delete', self)
        #btn_delete.clicked.connect(self.button_clicked)

        row_count = self.model.rowCount()

        #print(f' >>>>> row cnt : {self.model.index(row_count, 1)}')
        #self.tableView_todo.setIndexWidget(self.model.index(row_count, 4), btn_delete)
        ### 
        '''      
                
                            
    def add_row(self, schedule, time):
        schedule_item = QStandardItem(schedule) # key
        time_item = QStandardItem(time) # value

        #delete_button = QPushButton('Delete')
        #delete_button.clicked.connect(lambda: self.delete_row(schedule))
      
        row = [schedule_item, time_item]
        for col, item in enumerate(row):
            print(f'>>>{self.model.rowCount()} ')
            self.model.setItem(self.model.rowCount(), col, item)
      
    def delete_row(self,schedule):
        print("delete")      
    
    # 프로그램 시작시 자동 실행 이벤트
    def showEvent(self, event):
        # 프로그램 시작 시 타이머 시작
        print('Start Program')
        event.accept()
     
    # 프로그램 종료(closeEvent)시 자동 실행 이벤트  : 이렇게 하면 Tray로 안내려가고 바로 종료 
    def closeEvent(self, event):
        # Stop the timer when the program exits
        print('Stop Program')
        self.timer.stop()
        event.accept()    
            

# Pandas 데이터 모델
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data
       

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1] + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if index.column() < self._data.shape[1]:
                return str(self._data.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < self._data.shape[1]:
                    return str(self._data.columns[section])
                elif section == self._data.shape[1]:
                    return "Action"
            elif orientation == Qt.Vertical:
                return str(section)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index))


if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = WindowClass() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()