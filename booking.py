import tkinter as tk
from datetime import datetime
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
from io import BytesIO
import requests

class PetBedDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Pet&Bed Dashboard")
        self.root.geometry("1400x900")
        self.root.configure(bg="#E8C5D8")
        
        # Main container
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Sidebar
        self.create_sidebar(main_frame)
        
        # Right Content Area with Scrollbar
        self.create_content_area(main_frame)
    
    def create_sidebar(self, parent):
        """Create left sidebar with navigation"""
        sidebar = tk.Frame(parent, bg="#FFFFFF", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)
        sidebar.pack_propagate(False)
        
        # Logo
        logo_label = tk.Label(sidebar, text="Pet&Bed", font=("Arial", 24, "bold"), bg="#FFFFFF", fg="#3D2817")
        logo_label.pack(pady=20)
        
        # Menu buttons
        menu_items = ["Dashboard", "Care View", "Booking", "Rooms", "Customer & Pet", "Billing", "Staff", "Report"]
        
        for i, item in enumerate(menu_items):
            if i == 0:
                btn = tk.Button(sidebar, text=item, font=("Arial", 11), bg="#E8C5D8", fg="#3D2817", 
                               relief=tk.FLAT, padx=20, pady=10, width=18)
            else:
                btn = tk.Button(sidebar, text=item, font=("Arial", 11), bg="#FFFFFF", fg="#3D2817",
                               relief=tk.FLAT, padx=20, pady=10, width=18, bd=1, highlightthickness=1, highlightcolor="#CCCCCC")
            btn.pack(pady=8)
        
        # Spacer
        sidebar.pack_configure(fill=tk.BOTH, expand=True)
        
        # Log out button (at bottom)
        logout_btn = tk.Button(sidebar, text="Log out", font=("Arial", 10, "bold"), bg="#3D2817", fg="#FFFFFF",
                              relief=tk.FLAT, padx=20, pady=10, width=18)
        logout_btn.pack(side=tk.BOTTOM, pady=20)
        
        # Rabbit icon placeholder
        rabbit_icon = tk.Label(sidebar, text="🐰", font=("Arial", 40), bg="#FFFFFF")
        rabbit_icon.pack(side=tk.BOTTOM, pady=10)
    
    def create_content_area(self, parent):
        """Create main content area with scrollbar"""
        content_frame = ttk.Frame(parent)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Canvas for scrolling
        canvas = tk.Canvas(content_frame, bg="#E8C5D8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scroll
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg="#FFFFFF", highlightthickness=1, highlightbackground="#DDD")
        header_frame.pack(fill=tk.X, padx=0, pady=(0, 15))
        
        today_str = datetime.now().strftime("%A, %d/%m/%Y")
header_label = tk.Label(header_frame, text=f"Dashboard   {today_str}", font=("Arial", 14, "bold"),
                               bg="#FFFFFF", fg="#3D2817", justify=tk.LEFT)
        header_label.pack(pady=10, padx=15, anchor="w")
        
        new_booking_btn = tk.Button(header_frame, text="+ New Booking", font=("Arial", 10, "bold"),
                                    bg="#3D2817", fg="#FFFFFF", relief=tk.FLAT, padx=15, pady=8)
        new_booking_btn.pack(pady=10, padx=15, side=tk.RIGHT)
        
        # Stats Cards
        stats_frame = tk.Frame(scrollable_frame, bg="#E8C5D8")
        stats_frame.pack(fill=tk.X, padx=0, pady=(0, 15))
        
        self.create_stat_card(stats_frame, "Currently staying", "19", "7 dogs - 12 cats")
        self.create_stat_card(stats_frame, "Available rooms", "31", "out of 50 rooms")
        self.create_stat_card(stats_frame, "Monthly revenue", "18M", "+12% vs last month")
        self.create_stat_card(stats_frame, "Check-outs today", "5", "Pending billing")
        
        # Dog image placeholder
        dog_frame = tk.Frame(scrollable_frame, bg="#E8C5D8")
        dog_frame.pack(fill=tk.X, padx=0, pady=(0, 15))
        dog_img_label = tk.Label(dog_frame, text="[Dog Image]", font=("Arial", 40), bg="#8B9D6F",
                                fg="#FFFFFF", width=40, height=8)
        dog_img_label.pack(pady=5)
        
        # Active Bookings
        self.create_table(scrollable_frame, "Active Bookings",
                         ["Pet", "Owner", "Check-in", "Check-out", "Status", "Room"],
                         [
                             ["Milo", "Ha Thanh", "04/05", "06/05", "Completed", "R-03"],
                             ["Milo", "Ha Thanh", "04/05", "06/05", "Completed", "R-07"],
                             ["Milo", "Ha Thanh", "04/05", "06/05", "Completed", "R-06"]
                         ])
        
        # Today's Services
        self.create_table(scrollable_frame, "Today's Services",
                         ["Pet", "Service", "Room", "Status", "Frequency"],
                         [
                             ["Milo", "Grooming", "R-03", "Done", "1 time/day"],
                             ["Milo", "Grooming", "R-07", "Not done", "1 time/day"],
                             ["Milo", "Grooming", "R-06", "Done", "1 time/day"]
                         ])
        
        # Quote image placeholder
        quote_frame = tk.Frame(scrollable_frame, bg="#7FB5A1", height=120)
        quote_frame.pack(fill=tk.X, padx=0, pady=(15, 0))
        
        quote_label = tk.Label(quote_frame, text='[Cat Image] "Until one has loved an animal, a part of one\'s soul remains unawakened"',
                              font=("Arial", 12, "italic"), bg="#7FB5A1", fg="#FFFFFF", wraplength=400, justify=tk.CENTER)
        quote_label.pack(pady=30, padx=20)
    
    def create_stat_card(self, parent, title, value, subtitle):
        """Create a statistics card"""
        card = tk.Frame(parent, bg="#FFFFFF", relief=tk.FLAT, highlightthickness=1, highlightbackground="#DDD")
        card.pack(side=tk.LEFT, padx=8, pady=5, fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(card, text=title, font=("Arial", 10), bg="#FFFFFF", fg="#3D2817")
        title_label.pack(pady=(10, 0), padx=10)
        
        value_label = tk.Label(card, text=value, font=("Arial", 32, "bold"), bg="#FFFFFF", fg="#3D2817")
        value_label.pack(pady=(5, 0), padx=10)
        
        subtitle_label = tk.Label(card, text=subtitle, font=("Arial", 9), bg="#FFFFFF", fg="#666666")
        subtitle_label.pack(pady=(0, 10), padx=10)
    
    def create_table(self, parent, title, columns, rows):
        """Create a table with headers and data"""
        table_frame = tk.Frame(parent, bg="#FFFFFF", relief=tk.FLAT, highlightthickness=1, highlightbackground="#DDD")
        table_frame.pack(fill=tk.X, padx=0, pady=(0, 15))
        
        title_label = tk.Label(table_frame, text=title, font=("Arial", 12, "bold"), bg="#FFFFFF", fg="#3D2817")
        title_label.pack(pady=10, padx=15, anchor="w")
        
        # Table header
        header_frame = tk.Frame(table_frame, bg="#F5F5F5")
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for col in columns:
            col_label = tk.Label(header_frame, text=col, font=("Arial", 10, "bold"), bg="#F5F5F5",
                                fg="#3D2817", width=15, anchor="w")
            col_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Table rows
        for row in rows:
            row_frame = tk.Frame(table_frame, bg="#FFFFFF", highlightthickness=0)
            row_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for cell_text in row:
                cell_label = tk.Label(row_frame, text=cell_text, font=("Arial", 10), bg="#FFFFFF",
                                     fg="#666666", width=15, anchor="w")
                cell_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Bottom padding
        padding_label = tk.Label(table_frame, text="", bg="#FFFFFF")
        padding_label.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = PetBedDashboard(root)
    root.mainloop()
