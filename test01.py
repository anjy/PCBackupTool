import shutil
import os
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTableView

class Worker(QThread):
    progress = pyqtSignal(str, str)  # 작업 로그와 시간을 보낼 시그널
    finished = pyqtSignal(str, str, float)  # 메시지, 시간, 걸린 시간을 보낼 시그널

    def __init__(self, source_path, target_path):
        super().__init__()
        self.source_path = source_path
        self.target_path = target_path

    def run(self):
        source_path = self.source_path
        target_path = self.target_path

        # 작업 시작 시간 기록
        start_time = time.time()
        self.progress.emit("백업 중...", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if not source_path or not target_path:
            self.finished.emit("Please select a source file/folder and a destination folder.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0.0)
            return

        try:
            # 압축 없이 복사만
            if os.path.isfile(source_path):
                if os.path.isdir(target_path):
                    shutil.copy(source_path, os.path.join(target_path, os.path.basename(source_path)))
                else:
                    self.finished.emit("Destination must be a folder.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0.0)
                    return
            elif os.path.isdir(source_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dst_folder = os.path.join(target_path, os.path.basename(source_path))
                dst_folder += f'_{timestamp}'
                if not os.path.exists(dst_folder):
                    shutil.copytree(source_path, dst_folder)
                else:
                    self.finished.emit("Folder already exists at the destination.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0.0)
                    return
            else:
                self.finished.emit("Invalid source selected.", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0.0)
                return

            # 작업 완료 시간 기록
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.finished.emit("Success", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), elapsed_time)
        except Exception as e:
            self.finished.emit(f"파일 복사 실패: {source_path} -> {target_path}, 오류: {e}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0.0)

class WindowClass(QWidget):
    def __init__(self):
        super().__init__()

        # UI 설정
        self.btn_copy = QPushButton('Backup now', self)
        self.btn_copy.clicked.connect(self.copy_now)
        self.table_view = QTableView(self)

        layout = QVBoxLayout()
        layout.addWidget(self.btn_copy)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

        self.worker = None

        # 테이블 모델 설정
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Timestamp', 'Message', 'Elapsed Time (s)'])
        self.table_view.setModel(self.model)

    def copy_now(self):
        # 예시로 임의의 인덱스를 사용하여 소스 및 타겟 경로 생성
        source_index = 0  # 예제용 인덱스
        target_index = 1  # 예제용 인덱스
        source_dir = 'C:\Python312'
        target_dir = 'D:\_백업'


        # Worker 스레드 생성 및 시작
        self.worker = Worker(source_dir, target_dir)
        self.worker.progress.connect(self.update_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

        self.btn_copy.setEnabled(False)

    def update_log(self, message, timestamp):
        self.model.appendRow([
            QStandardItem(timestamp),
            QStandardItem(message),
            QStandardItem("")  # 빈 값으로 초기화
        ])
        # 자동으로 마지막 행으로 스크롤
        self.table_view.scrollToBottom()

    def on_finished(self, message, timestamp, elapsed_time):
        self.model.appendRow([
            QStandardItem(timestamp),
            QStandardItem(message),
            QStandardItem(f"{elapsed_time:.2f}")
        ])
        self.btn_copy.setEnabled(True)

# PyQt5 애플리케이션 실행
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = WindowClass()
    window.show()
    sys.exit(app.exec_())
