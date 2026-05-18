from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys


class HistoryApp(QMainWindow):
    def __init__(self):
        super().__init__()


        # ================= SETUP CƠ BẢN =================
        self.setWindowTitle("Pet&Bed History")
        self.resize(1920, 1080)
        self.setMinimumSize(1700, 950)


        # Cài đặt Font Baghdad mặc định cho toàn bộ nội dung
        self.setStyleSheet("""
            QWidget {
                background: #A8D3CF;
                color: #5A392F;
                font-family: 'Baghdad', 'Segoe UI', sans-serif;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.3);
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #68BBB2;
                min-height: 40px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #509E96;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)


        # ================= MAIN =================
        main = QWidget()
        self.setCentralWidget(main)


        main_layout = QHBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)


        # ================= SIDEBAR =================
        sidebar = QFrame()
        sidebar.setFixedWidth(290)
        sidebar.setStyleSheet("""
            QFrame {
                background: #F8F8F8;
                border: none;
            }
        """)


        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(22, 30, 22, 24)
        sidebar_layout.setSpacing(14)


        # ================= LOGO =================
        title = QLabel("Pet&Bed")
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            font-family: 'Arial Rounded MT Bold', 'Arial Rounded MT';
            color: #5A392F;
            padding-left: 6px;
            background: transparent;
        """)
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(20)


        # ================= MENU =================
        menus = ["Dashboard", "Care View", "Booking", "Rooms", "Customer & Pet", "Billing", "Staff", "Report"]


        for text in menus:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(62)


            # In đậm menu theo đúng chuẩn UI
            if text == "Booking":
                btn.setStyleSheet("""
                    QPushButton {
                        background: #68BBB2;
                        color: #3E2A24;
                        border: none;
                        border-radius: 22px;
                        text-align: left;
                        padding-left: 24px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: white;
                        color: #5A392F;
                        border: 2px solid #D8CBC6;
                        border-radius: 22px;
                        text-align: left;
                        padding-left: 24px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #F3E7EA;
                    }
                """)
            sidebar_layout.addWidget(btn)


        sidebar_layout.addStretch()


        # ================= LOGOUT =================
        self.logout_btn = QPushButton("Log out")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setFixedHeight(62)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background: #5A392F;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #412820;
            }
        """)
       
        # Thêm sự kiện THOÁT ứng dụng thực sự
        self.logout_btn.clicked.connect(self.logout_action)
       
        sidebar_layout.addWidget(self.logout_btn)
        main_layout.addWidget(sidebar)


        # ================= CONTENT AREA =================
        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background: transparent;")
       
        layout = QVBoxLayout(content_wrapper)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)


        # ================= TOPBAR =================
        topbar = QFrame()
        topbar.setFixedHeight(84)
        topbar.setStyleSheet("""
            QFrame {
                background: #F8F8F8;
                border-radius: 42px;
            }
        """)


        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(35, 0, 15, 0)


        # Trái Topbar
        booking_label = QLabel("Booking")
        booking_label.setStyleSheet("font-size: 26px; font-weight: bold; font-family: 'Arial Rounded MT Bold'; color: #5A392F; background: transparent;")
       
        date_label = QLabel("Tuesday, 06/05/2025")
        # In đậm ngày tháng
        date_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #5A392F; background: transparent;")


        left_info = QHBoxLayout()
        left_info.setSpacing(20)
        left_info.addWidget(booking_label)
        left_info.addWidget(date_label)
       
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_widget.setLayout(left_info)


        top_layout.addWidget(left_widget)
        top_layout.addStretch()


        # Tab Slider (Phải Topbar)
        self.tab_container = QFrame()
        self.tab_container.setFixedSize(430, 68)
        self.tab_container.setStyleSheet("QFrame { background: transparent; border: none; }")


        # Nền trượt (Slider)
        self.slider = QFrame(self.tab_container)
        self.slider.setGeometry(219, 6, 203, 56)
        self.slider.setStyleSheet("QFrame { background: #5A392F; border-radius: 28px; }")


        button_widget = QWidget(self.tab_container)
        button_widget.setGeometry(0, 0, 430, 68)
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(8, 6, 8, 6)
        button_layout.setSpacing(0)


        self.booking_btn = QPushButton("Bookings")
        self.history_btn = QPushButton("History")


        self.booking_btn.setCursor(Qt.PointingHandCursor)
        self.history_btn.setCursor(Qt.PointingHandCursor)


        self.booking_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 22px; font-weight: bold; color: #5A392F; }")
        self.history_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 22px; font-weight: bold; color: white; }")


        self.booking_btn.clicked.connect(lambda: self.switch_tab(0))
        self.history_btn.clicked.connect(lambda: self.switch_tab(1))


        button_layout.addWidget(self.booking_btn)
        button_layout.addWidget(self.history_btn)


        top_layout.addWidget(self.tab_container)
        layout.addWidget(topbar)


        # ================= TITLE =================
        history_title = QLabel("History")
        history_title.setStyleSheet("font-size: 52px; font-weight: bold; font-family: 'Arial Rounded MT Bold'; color: #4A3B32; background: transparent;")
        layout.addWidget(history_title)


        # ================= TOP SECTION (FILTER + IMAGE) =================
        top_section = QHBoxLayout()
        top_section.setSpacing(35)


        # FILTER BOX
        filter_box = QFrame()
        filter_box.setFixedHeight(270)
        filter_box.setStyleSheet("QFrame { background: #F8F8F8; border-radius: 30px; }")


        filter_layout = QGridLayout(filter_box)
        filter_layout.setContentsMargins(40, 30, 40, 30)
        filter_layout.setHorizontalSpacing(30)
        filter_layout.setVerticalSpacing(25)


        filters = ["Check - in", "Check - out", "Staying", "Cancelled"]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]


        for text, pos in zip(filters, positions):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # In đậm nút Filter
            btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 2px solid #D8CBC6;
                    border-radius: 28px;
                    font-size: 24px;
                    font-weight: bold;
                    color: #5A392F;
                }
                QPushButton:hover {
                    background: #F5EEEE;
                }
                QPushButton:checked {
                    background: #68BBB2;
                    color: white;
                    border: none;
                }
            """)
            filter_layout.addWidget(btn, *pos)


        top_section.addWidget(filter_box, 1)


        # IMAGE BOX
        image_label = QLabel()
        image_label.setFixedHeight(270)
        image_label.setStyleSheet("QLabel { background: #F8F8F8; border-radius: 30px; }")
       
        img_path = r"C:\project cki khmt\meo.jpg"
        pixmap = QPixmap(img_path)


        if not pixmap.isNull():
            rounded = QPixmap(pixmap.size())
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(QRectF(rounded.rect()), 30, 30)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
           
            image_label.setPixmap(rounded)
            image_label.setScaledContents(True)
        else:
            image_label.setText("IMAGE NOT FOUND\n(meo.jpg)")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setStyleSheet("QLabel { background: #EAD7DC; border-radius: 30px; font-size: 24px; color: #5A392F; font-weight: bold; }")


        top_section.addWidget(image_label, 1)
        layout.addLayout(top_section)


        # ================= SEARCH BAR =================
        search_frame = QFrame()
        search_frame.setFixedHeight(75)
        search_frame.setStyleSheet("QFrame { background: white; border-radius: 37px; }")


        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(35, 0, 30, 0)


        search = QLineEdit()
        search.setPlaceholderText("Search room_id")
        # NỘI DUNG tìm kiếm để NORMAL
        search.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 22px;
                font-weight: normal;
                color: #5A392F;
            }
        """)


        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 28px; color: #5A392F; background: transparent; font-weight: bold;")


        search_layout.addWidget(search)
        search_layout.addWidget(icon)


        layout.addWidget(search_frame)


        # ================= TABLE =================
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background: #F8F8F8; border-radius: 30px; }")


        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(25, 20, 25, 25)


        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["#", "Pet", "Owner", "Check in", "Check out", "Room", "Service", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)


        # HEADER in đậm (bold) | NỘI DUNG BẢNG nét thường (normal)
        self.table.setStyleSheet("""
            QTableWidget {
                background: transparent;
                border: none;
                color: #5A392F;
                font-size: 20px;
                font-weight: normal;
            }
            QHeaderView::section {
                background: transparent;
                border: none;
                border-bottom: 3px solid #E7D7D2;
                padding: 18px;
                font-size: 20px;
                font-weight: bold;
                font-family: 'Arial Rounded MT Bold';
                color: #4A3B32;
            }
            QTableWidget::item {
                border-bottom: 1px solid #E7D7D2;
                padding: 12px;
            }
        """)


        self.fill_table()
        table_layout.addWidget(self.table)
        layout.addWidget(table_frame)


        # Scroll Area ráp vào Main Layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(content_wrapper)
        main_layout.addWidget(scroll)


    # ================= EVENT CHUYỂN TAB =================
    def switch_tab(self, index):
        anim = QPropertyAnimation(self.slider, b"geometry")
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.InOutQuad)


        if index == 0:
            anim.setEndValue(QRect(8, 6, 203, 56))
            self.booking_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 22px; font-weight: bold; color: white; }")
            self.history_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 22px; font-weight: bold; color: #5A392F; }")
        else:
            anim.setEndValue(QRect(219, 6, 203, 56))
            self.booking_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 22px; font-weight: bold; color: #5A392F; }")
            self.history_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 22px; font-weight: bold; color: white; }")


        anim.start()
        self.anim = anim


    # ================= EVENT THOÁT ỨNG DỤNG =================
    def logout_action(self):
        # Hiện bảng hỏi xác nhận thoát ứng dụng
        reply = QMessageBox.question(self, 'Xác nhận',
                                     'Bạn có chắc chắn muốn đăng xuất và thoát ứng dụng?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
       
        if reply == QMessageBox.Yes:
            QApplication.quit() # Đóng hoàn toàn app


    # ================= TABLE DATA =================
    def fill_table(self):
        rows = [
            ["001", "Milo", "Nguyen Lan", "04/05", "08/05", "R-01"],
            ["002", "Moa", "Nguyen Lan", "04/05", "08/05", "R-02"],
            ["003", "Luna", "Tran Vy", "08/05", "12/05", "R-05"],
            ["004", "Coco", "Minh Anh", "09/05", "13/05", "R-08"],
            ["005", "Kiki", "Bao Ngoc", "10/05", "15/05", "R-10"],
            ["006", "Bubu", "Gia Bao", "11/05", "16/05", "R-12"],
        ]
       
        self.table.setRowCount(len(rows))
        self.table.verticalHeader().setDefaultSectionSize(80)


        for row in range(len(rows)):
            for col in range(6):
                item = QTableWidgetItem(rows[row][col])
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)


        services = [
            ("Grooming", "#D8E59E"),
            ("Daycare", "#EDC0CB"),
            ("Spa", "#C9DDF8"),
            ("VIP", "#F5D49A"),
            ("Grooming", "#D8E59E"),
            ("Daycare", "#EDC0CB")
        ]


        for row in range(len(rows)):
            # In đậm Tag Dịch vụ
            service = QLabel(services[row][0])
            service.setAlignment(Qt.AlignCenter)
            service.setFixedSize(150, 42)
            service.setStyleSheet(f"""
                background: {services[row][1]};
                border-radius: 21px;
                font-size: 16px;
                font-weight: bold;
                color: #5A392F;
            """)
            wrap_service = QWidget()
            lay_service = QHBoxLayout(wrap_service)
            lay_service.setContentsMargins(0, 0, 0, 0)
            lay_service.setAlignment(Qt.AlignCenter)
            lay_service.addWidget(service)
            self.table.setCellWidget(row, 6, wrap_service)


            # In đậm trạng thái
            status = QLabel("Staying")
            status.setAlignment(Qt.AlignCenter)
            status.setStyleSheet("font-size: 18px; font-weight: bold; color: #5A392F; background: transparent;")
            wrap_status = QWidget()
            lay_status = QHBoxLayout(wrap_status)
            lay_status.setContentsMargins(0, 0, 0, 0)
            lay_status.setAlignment(Qt.AlignCenter)
            lay_status.addWidget(status)
            self.table.setCellWidget(row, 7, wrap_status)


# ================= RUN =================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = HistoryApp()
    window.show()
    sys.exit(app.exec_())

