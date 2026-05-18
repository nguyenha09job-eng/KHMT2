import sys
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import webbrowser
import os


# ── BỘ MÀU CHUẨN TRANG 5 (CHỈ DÙNG CHO NỘI DUNG) ────────────────
BG_MAIN    = "#E8BFC7"  # Hồng nền chính
BG_CARD    = "#F8F8F8"  # Trắng xám card
TEXT_DARK  = "#5A392F"  # Nâu đậm
ACCENT_TEAL= "#68BBB2"  # Xanh Teal (nút bấm)
WHITE      = "#FFFFFF"


# ── DỮ LIỆU ────────────────────────────────────────────────────
SAMPLE_DATA = [
    ("Alice Nguyen",  "012-345-678", "Milo", "1,230 P", "VIP"),
    ("Alice Nguyen",  "012-345-678", "Moa",  "1,230 P", "VIP"),
    ("Helen Tran",    "098-765-432", "Bong", "800 P",   "Standard"),
]


class CustomerPetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pet&Bed – Hotel Management")
        self.setGeometry(100, 40, 1920, 1080)
        self.setStyleSheet(f"background-color: {BG_MAIN}; font-family: Baghdad;")


        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)


        # ══════════════════════════════════════════════════════════
        # SIDEBAR (GIỮ NGUYÊN GIAO DIỆN GỐC + CON THỎ)
        # ══════════════════════════════════════════════════════════
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: white; border-top-right-radius: 20px; border-bottom-right-radius: 20px;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(20, 30, 20, 20)
       
        logo = QLabel("Pet&Bed")
        logo.setStyleSheet(f"font-size: 32px; font-weight: bold; font-family: 'Arial Rounded MT'; color: {TEXT_DARK};")
        sb_layout.addWidget(logo)
        sb_layout.addSpacing(25)


        menu = ["Dashboard", "Care View", "Booking", "Rooms", "Customer & Pet", "Billing", "Staff", "Report"]
        for item in menu:
            btn = QPushButton(item)
            btn.setFixedHeight(42)
            is_active = (item == "Customer & Pet")
            style = f"""
                QPushButton {{
                    background-color: {'#E6A8B6' if is_active else 'white'};
                    border-radius: 20px;
                    border: 1px solid #D8C7C2;
                    text-align: left; padding-left: 18px; font-size: 15px; color: {TEXT_DARK};
                    font-weight: {'bold' if is_active else 'normal'};
                }}
                QPushButton:hover {{ background-color: #F4E5E9; }}
            """
            btn.setStyleSheet(style)
            sb_layout.addWidget(btn)
            sb_layout.addSpacing(5)
           
        sb_layout.addStretch()


        # KHU VỰC CON THỎ (AVATAR)
        avatar_box = QVBoxLayout()
        rabbit_label = QLabel()
        r_pix = QPixmap("thỏ.png") # Load con thỏ của bạn ở đây
        if not r_pix.isNull():
            rabbit_label.setPixmap(r_pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            rabbit_label.setText("🐰")
            rabbit_label.setStyleSheet("font-size: 60px;")
        rabbit_label.setAlignment(Qt.AlignCenter)
        avatar_box.addWidget(rabbit_label)


        logout_btn = QPushButton("Log out")
    ````_btn.setFixedHeight(45)
        logout_btn.setStyleSheet(f"background-color: {TEXT_DARK}; color: white; border-radius: 22px; font-weight: bold; font-size: 14px;")
        avatar_box.addWidget(logout_btn)
       
        sb_layout.addLayout(avatar_box)
        main_layout.addWidget(sidebar)


        # ══════════════════════════════════════════════════════════
        # KHUNG NỘI DUNG (CHỈ SỬA PHẦN NÀY ĐỂ MATCHING TRANG 5)
        # ══════════════════════════════════════════════════════════
        content_wrapper = QWidget()
        v_layout = QVBoxLayout(content_wrapper)
        v_layout.setContentsMargins(30, 25, 30, 25)
        v_layout.setSpacing(20)


        # 1. Topbar (Style Trang 5)
        topbar = QFrame()
        topbar.setFixedHeight(55)
        topbar.setStyleSheet("background-color: #F8F8F8; border-radius: 27px;")
        top_lay = QHBoxLayout(topbar)
        top_lay.addWidget(QLabel("  Customer & Pet", styleSheet=f"font-weight: bold; font-size: 18px; color: {TEXT_DARK};"))
        top_lay.addStretch()
        today_str = datetime.now().strftime("%A, %d/%m/%Y")
top_lay.addWidget(QLabel(f"{today_str}  ", styleSheet=f"color: {TEXT_DARK}; font-size: 14px;"))
        v_layout.addWidget(topbar)


        # 2. Banner (Ảnh bìa bo tròn 30px)
        self.banner = QLabel()
        self.banner.setFixedHeight(220)
        pixmap = QPixmap("bìa1.png")
        if not pixmap.isNull():
            canvas = QPixmap(1600, 220)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 1600, 220, 30, 30) # Bo góc khớp trang 5
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap.scaled(1600, 220, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            painter.end()
            self.banner.setPixmap(canvas)
        else:
            self.banner.setStyleSheet("background-color: #D8C18F; border-radius: 30px;") # Màu fallback
        v_layout.addWidget(self.banner)


        # 3. Search Bar
        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("🔍 Search by name, phone, or pet name...")
        self.search_in.setFixedHeight(50)
        self.search_in.setStyleSheet("background-color: white; border-radius: 25px; padding-left: 20px; border: none; font-size: 15px;")
        v_layout.addWidget(self.search_in)


        # 4. Table Card (Bo góc 30px, nền F8F8F8)
        table_card = QFrame()
        table_card.setStyleSheet("background-color: #F8F8F8; border-radius: 30px;")
        table_lay = QVBoxLayout(table_card)
        table_lay.setContentsMargins(20, 20, 20, 20)
       
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Customer", "Phone", "Pets", "Points", "Membership", "Action"])
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background: transparent; border: none; color: {TEXT_DARK}; font-size: 15px; }}
            QHeaderView::section {{
                background: transparent; border: none; font-weight: bold;
                padding: 15px; border-bottom: 2px solid #D8CBC7; color: {TEXT_DARK};
            }}
            QTableWidget::item {{ border-bottom: 1px solid #EDE0DD; padding: 15px; }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
       
        table_lay.addWidget(self.table)
        v_layout.addWidget(table_card)
       
        main_layout.addWidget(content_wrapper, stretch=1)
        self.render_table(SAMPLE_DATA)


    def render_table(self, data):
        self.table.setRowCount(len(data))
        for row, (cust, phone, pet, pts, mem) in enumerate(data):
            for col, text in enumerate([cust, phone, "", pts, mem]):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                if col != 2: self.table.setItem(row, col, item)


            # Pet Chip
            p_container = QWidget()
            p_lay = QHBoxLayout(p_container); p_lay.setContentsMargins(0,0,0,0)
            pet_btn = QPushButton(f"🐾 {pet}")
            pet_btn.setFixedSize(110, 32)
            pet_btn.setStyleSheet("background-color: #FDECD0; color: #7A4A1A; border-radius: 15px; font-weight: bold; border: none;")
            p_lay.addWidget(pet_btn)
            self.table.setCellWidget(row, 2, p_container)


            # Profile Button
            a_container = QWidget()
            a_lay = QHBoxLayout(a_container); a_lay.setContentsMargins(0,0,0,0)
            act_btn = QPushButton("Profile")
            act_btn.setFixedSize(100, 32)
            act_btn.setStyleSheet(f"background-color: {ACCENT_TEAL}; color: white; border-radius: 15px; font-weight: bold; border: none;")
            a_lay.addWidget(act_btn)
            self.table.setCellWidget(row, 5, a_container)
           
            self.table.setRowHeight(row, 65)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomerPetApp()
    window.show()
    sys.exit(app.exec_())

