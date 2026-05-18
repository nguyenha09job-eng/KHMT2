import tkinter as tk


# =========================
# Rounded Rectangle
# =========================
def round_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):

    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,

        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,

        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,

        x1, y1 + radius,
        x1, y1
    ]

    return canvas.create_polygon(
        points,
        smooth=True,
        splinesteps=36,
        **kwargs
    )


# =========================
# APP
# =========================
class NewStaffPopup(tk.Tk):

    def __init__(self):

        super().__init__()

        # ===== WINDOW =====
        WIDTH = 535
        HEIGHT = 385

        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.configure(bg="#DDECEC")
        self.resizable(False, False)

        # CENTER
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        x = (sw - WIDTH) // 2
        y = (sh - HEIGHT) // 2

        self.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")

        # ===== COLORS =====
        self.BG = "#DDECEC"
        self.WHITE = "#FFFFFF"

        self.TEXT = "#4A3525"
        self.BORDER = "#D7D0CB"
        self.PLACE = "#B6AEA9"

        self.BUTTON = "#73C9C1"

        # ===== CANVAS =====
        self.cv = tk.Canvas(
            self,
            width=WIDTH,
            height=HEIGHT,
            bg=self.BG,
            highlightthickness=0
        )

        self.cv.pack(fill="both", expand=True)

        # =========================
        # MAIN POPUP
        # =========================
        round_rect(
            self.cv,
            8,
            8,
            527,
            377,
            radius=32,
            fill=self.WHITE,
            outline=""
        )

        # =========================
        # TITLE
        # =========================
        self.cv.create_text(
            40,
            58,
            text="New staff",
            anchor="w",
            fill=self.TEXT,
            font=("Arial Rounded MT Bold", 18, "bold")
        )

        # DIVIDER
        self.cv.create_line(
            40,
            84,
            490,
            84,
            fill="#DCD6D2",
            width=1
        )

        # =========================
        # PHONE LABEL
        # =========================
        self.cv.create_text(
            40,
            122,
            text="Phone number",
            anchor="w",
            fill=self.TEXT,
            font=("Arial Rounded MT Bold", 12, "bold")
        )

        # PHONE INPUT
        round_rect(
            self.cv,
            38,
            140,
            440,
            186,
            radius=23,
            fill="white",
            outline=self.BORDER,
            width=1.5
        )

        self.phone_entry = tk.Entry(
            self,
            bd=0,
            relief="flat",
            bg="white",
            fg=self.PLACE,
            font=("Arial", 13),
            insertbackground=self.TEXT
        )

        self.phone_entry.insert(0, "ex: 012345678")

        self.phone_entry.place(
            x=65,
            y=153,
            width=250,
            height=22
        )

        # =========================
        # NAME LABEL
        # =========================
        self.cv.create_text(
            40,
            222,
            text="Full Name",
            anchor="w",
            fill=self.TEXT,
            font=("Arial Rounded MT Bold", 12, "bold")
        )

        # NAME INPUT
        round_rect(
            self.cv,
            38,
            240,
            440,
            286,
            radius=23,
            fill="white",
            outline=self.BORDER,
            width=1.5
        )

        self.name_entry = tk.Entry(
            self,
            bd=0,
            relief="flat",
            bg="white",
            fg=self.PLACE,
            font=("Arial", 13),
            insertbackground=self.TEXT
        )

        self.name_entry.insert(0, "ex: Thuy Hang")

        self.name_entry.place(
            x=65,
            y=253,
            width=250,
            height=22
        )

        # =========================
        # BUTTON
        # =========================
        round_rect(
            self.cv,
            180,
            310,
            335,
            355,
            radius=23,
            fill=self.BUTTON,
            outline=""
        )

        self.cv.create_text(
            257,
            333,
            text="Add staff",
            fill="white",
            font=("Arial Rounded MT Bold", 13, "bold"),
            tags="button"
        )

        self.cv.tag_bind(
            "button",
            "<Button-1>",
            self.add_staff
        )

    # =========================

    def add_staff(self, event=None):

        print("Phone:", self.phone_entry.get())
        print("Name:", self.name_entry.get())


# =========================
# RUN
# =========================
if __name__ == "__main__":

    app = NewStaffPopup()

    app.mainloop()