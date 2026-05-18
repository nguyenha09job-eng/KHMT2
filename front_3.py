import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
import sys
from datetime import datetime

def _round_rect(cv, x1, y1, x2, y2, radius=25, **kwargs):
    d = 2 * radius
    kwargs["outline"] = kwargs.get("fill", "")
    items = []
    items.append(cv.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs))
    items.append(cv.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs))
    items.append(cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style='pieslice', **kwargs))
    items.append(cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style='pieslice', **kwargs))
    return tuple(items)


class BookingDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pet&Bed - Booking")
        self.attributes("-fullscreen", True)
        self.configure(bg="#A8D3CF")
        self.update_idletasks()

        self.W = self.winfo_width()
        self.H = self.winfo_height()
        self.BASE_W = 1200.0
        self.BASE_H = 850.0
        self._s = self.W / self.BASE_W
        s = self._s
        self.Y_OFF = 20

        # Colors
        self.C_BG = "#A8D3CF"
        self.C_SIDEBAR = "#FFFFFF"
        self.C_TEXT = "#4A3525"
        self.C_TEXT_LIGHT = "#7A685F"
        self.C_WHITE = "#FFFFFF"
        self.C_ACTIVE = "#68BBB2"
        self.C_CARD_BG = "#FFFFFF"
        self.C_BORDER = "#CFC9C3"
        self.C_DIVIDER = "#DDD8D2"
        self.C_CONFIRM = "#68BBB2"
        self.C_CHIP_BORDER = "#D8D4CF"
        self.C_TOGGLE_OFF = "#D8D4D0"
        self.C_PLACEHOLDER = "#B5B0AA"

        # Fonts
        self.F_LOGO = ("Arial Rounded MT Bold", max(16, int(40 * s)), "bold")
        self.F_NAV = ("Baghdad", max(10, int(18 * s)))
        self.F_TITLE = ("Arial Rounded MT Bold", max(10, int(18 * s)), "bold")
        self.F_DATE = ("Baghdad", max(10, int(18 * s)))
        self.F_SECTION = ("Arial Rounded MT Bold", max(10, int(20 * s)), "bold")
        self.F_QUICK = ("Arial Rounded MT Bold", max(18, int(36 * s)), "bold")
        self.F_LABEL = ("Baghdad", max(10, int(16 * s)), "bold")
        self.F_INPUT = ("Baghdad", max(10, int(18 * s)))
        self.F_BTN = ("Baghdad", max(10, int(16 * s)))
        self.F_PRICE = ("Baghdad", max(10, int(18 * s)), "bold")
        self.F_QUOTE = ("Arial Rounded MT Bold", max(10, int(16 * s)), "bold")
        self.F_TOGGLE_BTN = ("Baghdad", max(9, int(14 * s)), "bold")

        self.images = []

        # Layout
        main = tk.Frame(self, bg=self.C_BG)
        main.pack(fill=tk.BOTH, expand=True)

        self.BASE_SIDE_W = 260
        side_w = int(self.BASE_SIDE_W * s)

        # Sidebar
        self.side_frame = tk.Frame(main, width=side_w, bg=self.C_BG)
        self.side_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.side_frame.pack_propagate(False)
        self.sidebar_canvas = tk.Canvas(self.side_frame, width=side_w, height=self.H,
                                        bg=self.C_BG, highlightthickness=0)
        self.sidebar_canvas.pack(fill=tk.BOTH, expand=True)

        # Content - scrollable frame approach
        self.content_container = tk.Frame(main, bg=self.C_BG)
        self.content_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        content_canvas = tk.Canvas(self.content_container, bg=self.C_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_container, orient=tk.VERTICAL, command=content_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_canvas.configure(yscrollcommand=scrollbar.set)
        self.content_canvas = content_canvas

        # Scrollable inner frame
        self.inner = tk.Frame(content_canvas, bg=self.C_BG)
        self.inner_window = content_canvas.create_window(0, 0, window=self.inner, anchor="nw")

        # Draw
        self.draw_sidebar()
        self.sidebar_canvas.scale("all", 0, 0, s, s)
        self.build_content()

        # Scroll bindings - global capture to work over all child widgets
        def _on_mw_global(event):
            # Only scroll when cursor is in the content area (right of sidebar)
            sidebar_right = self.side_frame.winfo_rootx() + self.side_frame.winfo_width()
            if event.x_root >= sidebar_right:
                if sys.platform == "darwin":
                    content_canvas.yview_scroll(int(-event.delta), "units")
                else:
                    content_canvas.yview_scroll(int(-event.delta / 120), "units")

        self.bind_all("<MouseWheel>", _on_mw_global, add="+")
        self.bind_all("<Button-4>", lambda e: content_canvas.yview_scroll(-1, "units"), add="+")
        self.bind_all("<Button-5>", lambda e: content_canvas.yview_scroll(1, "units"), add="+")

        # Also bind on content_canvas itself for when it has focus
        content_canvas.bind("<MouseWheel>", _on_mw_global, add="+")

        def _on_configure(e):
            content_canvas.itemconfig(self.inner_window, width=e.width)
            content_canvas.configure(scrollregion=content_canvas.bbox("all"))
        content_canvas.bind("<Configure>", _on_configure)
        self.inner.bind("<Configure>", lambda e: content_canvas.configure(scrollregion=content_canvas.bbox("all")))

        self.bind("<Escape>", lambda e: self.destroy())

    # =====================================================
    # SIDEBAR (same as front_1, Booking active, turtle icon)
    # =====================================================
    def draw_sidebar(self):
        cv = self.sidebar_canvas
        _round_rect(cv, -80, 0, 250, 820, radius=30, fill=self.C_SIDEBAR, outline="")
        cv.create_text(125, 70, text="Pet&Bed", font=self.F_LOGO, fill=self.C_TEXT)

        nav_items = ["Dashboard", "Care View", "Booking", "Rooms",
                     "Customer & Pet", "Billing", "Staff", "Report"]
        y = 110
        item_h, item_r, pad_x, right_x, gap = 37, 18, 36, 215, 10

        for i, item in enumerate(nav_items):
            fill = self.C_ACTIVE if i == 2 else "#efefef"
            _round_rect(cv, pad_x, y, right_x, y + item_h, radius=item_r, fill=fill, outline="")
            cv.create_text(pad_x + 20, y + 20, text=item, font=self.F_NAV, fill=self.C_TEXT, anchor="w")
            y += item_h + gap

        # Turtle icon
        _dir = os.path.dirname(__file__)
        icon_path = os.path.join(_dir, "image", "turtle.png")
        s = self._s
        iw, ih = int(130 * s), int(130 * s)
        sr = int(20 * s)
        if os.path.exists(icon_path):
            img = Image.open(icon_path).convert("RGBA")
        else:
            img = Image.new("RGBA", (iw, ih), color="#CCCCCC")
        img = img.resize((iw, ih), Image.Resampling.LANCZOS)
        mask = Image.new("L", (iw, ih), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw, ih), radius=sr, fill=255)
        result = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        icon_tk = ImageTk.PhotoImage(result)
        self.images.append(icon_tk)
        cv.create_image(125 - 65, 550, image=icon_tk, anchor="nw")

        # Logout
        base_bottom = self.H / self._s
        btn_h, btn_pad = 42, 25
        btn_y2 = base_bottom - btn_pad
        btn_y1 = btn_y2 - btn_h
        _round_rect(cv, 30, btn_y1, 220, btn_y2, radius=btn_h // 2,
                    fill=self.C_TEXT, outline="", tags="logout_btn")
        cv.create_text(125, (btn_y1 + btn_y2) / 2, text="Log out",
                       font=self.F_NAV, fill="#FFFFFF", tags="logout_btn")
        cv.tag_bind("logout_btn", "<Button-1>", lambda e: self.destroy())

    # =====================================================
    # ROUNDED IMAGE HELPER
    # =====================================================
    def create_rounded_image(self, image_path, width, height, radius):
        s = self._s
        sw, sh, sr = int(width * s), int(height * s), int(radius * s)
        if not os.path.exists(image_path):
            img = Image.new("RGB", (sw, sh), color="#CCCCCC")
        else:
            img = Image.open(image_path).convert("RGB")
        img_ratio = img.width / img.height
        target_ratio = sw / sh
        if img_ratio > target_ratio:
            nw = int(sh * img_ratio)
            img = img.resize((nw, sh), Image.Resampling.LANCZOS)
            left = (nw - sw) // 2
            img = img.crop((left, 0, left + sw, sh))
        else:
            nh = int(sw / img_ratio)
            img = img.resize((sw, nh), Image.Resampling.LANCZOS)
            top = (nh - sh) // 2
            img = img.crop((0, top, sw, top + sh))
        mask = Image.new("L", (sw, sh), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh), radius=sr, fill=255)
        result = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask=mask)
        return ImageTk.PhotoImage(result)

    # =====================================================
    # CONTENT (header + form + banner using Frame widgets)
    # =====================================================
    def build_content(self):
        s = self._s
        pad_x = int(30 * s)
        pad_y = int(45 * s)
        inner = self.inner

        # === HEADER BAR ===
        header_h = int(40 * s)
        header_cv = tk.Canvas(inner, height=header_h, bg=self.C_BG, highlightthickness=0)
        header_cv.pack(fill=tk.X, padx=pad_x, pady=(pad_y, int(5 * s)))

        def _draw_header(event=None):
            header_cv.delete("all")
            w = header_cv.winfo_width()
            h = header_cv.winfo_height()
            _round_rect(header_cv, 0, 0, w, h, radius=h//2, fill=self.C_WHITE)
            header_cv.create_text(int(30*s), h//2, text="Booking", font=self.F_TITLE, fill=self.C_TEXT, anchor="w")
            header_cv.create_text(int(135*s), h//2, text=datetime.now().strftime("%A, %d/%m/%Y"),
                                  font=self.F_DATE, fill=self.C_TEXT_LIGHT, anchor="w")
            # Toggle: Bookings | History
            tw = int(95 * s)
            tx = w - int(12 * s) - tw * 2
            tg_h = h - int(6*s)
            _round_rect(header_cv, tx, int(3*s), tx + tw, h - int(3*s),
                        radius=tg_h//2, fill=self.C_TEXT)
            header_cv.create_text(tx + tw//2, h//2, text="Bookings",
                                  font=self.F_TOGGLE_BTN, fill=self.C_WHITE)
            header_cv.create_text(tx + tw + tw//2, h//2, text="History",
                                  font=self.F_TOGGLE_BTN, fill=self.C_TEXT)
        header_cv.bind("<Configure>", _draw_header)

        # === QUICK BOOKING TITLE ===
        tk.Label(inner, text="Quick booking", font=self.F_QUICK,
                 bg=self.C_BG, fg=self.C_TEXT, anchor="w").pack(fill=tk.X, padx=pad_x, pady=(int(5*s), int(14*s)))

        # === FORM CARD (layered Canvas behind Frame for rounded corners) ===
        card_wrapper = tk.Frame(inner, bg=self.C_BG)
        card_wrapper.pack(fill=tk.X, padx=pad_x, pady=(0, int(12*s)))

        # Canvas behind everything for the rounded white background
        card_bg_cv = tk.Canvas(card_wrapper, bg=self.C_BG, highlightthickness=0)
        card_bg_cv.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.lower(card_bg_cv)  # send behind form_frame

        # Form frame on top, padded so its corners are inside the rounded area
        card_inset = int(16 * s)
        form_frame = tk.Frame(card_wrapper, bg=self.C_CARD_BG)
        form_frame.pack(fill=tk.X, padx=card_inset, pady=card_inset)

        def _draw_card_bg(event=None):
            card_bg_cv.delete("all")
            w = card_wrapper.winfo_width()
            h = card_wrapper.winfo_height()
            if w > 1 and h > 1:
                _round_rect(card_bg_cv, 0, 0, w, h, radius=int(30*s), fill=self.C_CARD_BG)

        card_wrapper.bind("<Configure>", _draw_card_bg)

        form_pad = int(36 * s)

        # --- Customer Section ---
        self._add_section_label(form_frame, "Customer", form_pad)
        row1 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row1.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row1, "Phone number", "ex: 012345678", side=tk.LEFT, expand=True)
        self._add_labeled_entry(row1, "Full Name", "ex: Thuy Hang", side=tk.LEFT, expand=True)

        row2 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row2.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row2, "Street address", "ex: 45 Nguyễn Thị Minh Khai", side=tk.LEFT, expand=True)
        self._add_labeled_entry(row2, "District", "Quận 3", side=tk.LEFT)

        mem_frame = tk.Frame(form_frame, bg=self.C_CARD_BG)
        mem_frame.pack(fill=tk.X, padx=form_pad, pady=(0, int(12*s)))
        tk.Label(mem_frame, text="Membership", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        chip_row = tk.Frame(mem_frame, bg=self.C_CARD_BG)
        chip_row.pack(anchor="w", pady=(int(3*s), 0))
        for idx, chip in enumerate(["No", "VIP", "Premium"]):
            self._add_chip(chip_row, chip, active=(idx == 0))

        # --- Pets Section ---
        self._add_section_label(form_frame, "Pets", form_pad)
        row3 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row3.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row3, "Name", "ex: Milo", side=tk.LEFT, expand=True)

        sp_frame = tk.Frame(row3, bg=self.C_CARD_BG)
        sp_frame.pack(side=tk.LEFT, padx=(int(12*s), 0))
        tk.Label(sp_frame, text="Species", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        sp_chips = tk.Frame(sp_frame, bg=self.C_CARD_BG)
        sp_chips.pack(anchor="w")
        for c in ["Dog", "Cat"]:
            self._add_chip(sp_chips, c)

        st_frame = tk.Frame(row3, bg=self.C_CARD_BG)
        st_frame.pack(side=tk.LEFT, padx=(int(12*s), 0))
        tk.Label(st_frame, text="Sterilization", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        self._add_toggle(st_frame)

        row4 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row4.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row4, "Breed", "ex: Poodle", side=tk.LEFT, expand=True)

        gd_frame = tk.Frame(row4, bg=self.C_CARD_BG)
        gd_frame.pack(side=tk.LEFT, padx=(int(12*s), 0))
        tk.Label(gd_frame, text="Gender", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        gd_chips = tk.Frame(gd_frame, bg=self.C_CARD_BG)
        gd_chips.pack(anchor="w")
        for c in ["Male", "Female"]:
            self._add_chip(gd_chips, c)

        vc_frame = tk.Frame(row4, bg=self.C_CARD_BG)
        vc_frame.pack(side=tk.LEFT, padx=(int(12*s), 0))
        tk.Label(vc_frame, text="Vaccinated", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        self._add_toggle(vc_frame)

        for label in ["Health condition", "Behaviour note", "Special requirement"]:
            r = tk.Frame(form_frame, bg=self.C_CARD_BG)
            r.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
            self._add_labeled_entry(r, label, "Note here", side=tk.TOP, expand=True, full=True)

        # --- Booking Section ---
        self._add_section_label(form_frame, "Booking", form_pad)
        row5 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row5.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row5, "Room type", "ex: type_name", side=tk.LEFT, expand=True)

        price_f = tk.Frame(row5, bg=self.C_CARD_BG)
        price_f.pack(side=tk.LEFT, padx=(int(10*s), 0))
        tk.Label(price_f, text="Price", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        pv = tk.Frame(price_f, bg=self.C_CARD_BG)
        pv.pack(anchor="w")
        tk.Label(pv, text="875,000đ", font=self.F_PRICE, bg=self.C_CARD_BG, fg="#6BA52F").pack(side=tk.LEFT)
        tk.Label(pv, text="/night", font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(side=tk.LEFT)

        row6 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row6.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row6, "Specific room", "ex: room_id", side=tk.LEFT, expand=True)
        self._add_labeled_entry(row6, "Service", "", side=tk.LEFT, expand=True)

        row7 = tk.Frame(form_frame, bg=self.C_CARD_BG)
        row7.pack(fill=tk.X, padx=form_pad, pady=(0, int(10*s)))
        self._add_labeled_entry(row7, "Check in", "mm/dd/yy", side=tk.LEFT, expand=True)
        self._add_labeled_entry(row7, "Check out", "mm/dd/yy", side=tk.LEFT, expand=True)

        # Confirm button (rounded via Canvas)
        btn_h = int(46 * s)
        btn_cv = tk.Canvas(form_frame, height=btn_h, bg=self.C_CARD_BG, highlightthickness=0)
        btn_cv.pack(pady=(int(14*s), int(20*s)))
        def _draw_confirm_btn(event=None):
            btn_cv.delete("cbtn")
            cw = btn_cv.winfo_width()
            ch = btn_cv.winfo_height()
            if cw > 1 and ch > 1:
                bw = int(180 * s)
                bx = (cw - bw) // 2
                _round_rect(btn_cv, bx, 0, bx + bw, ch, radius=ch//2, fill=self.C_CONFIRM, tags="cbtn")
                btn_cv.create_text(cw//2, ch//2, text="Confirm", font=self.F_BTN, fill="white", tags="cbtn")
        btn_cv.bind("<Configure>", _draw_confirm_btn)
        btn_cv.bind("<Button-1>", lambda e: messagebox.showinfo("Success", "Booking confirmed!"))


        # === BOTTOM BANNER (image + text overlay) ===
        _dir = os.path.dirname(__file__)
        banner_path = os.path.join(_dir, "image", "booking.jpg")
        bw_base = int(self.BASE_W - self.BASE_SIDE_W - pad_x * 2 / s)
        bh_base = 280  # larger cat image
        banner_tk = self.create_rounded_image(banner_path, bw_base, bh_base, radius=20)
        self.images.append(banner_tk)

        bh = int(bh_base * s)
        banner_cv = tk.Canvas(inner, height=bh, bg=self.C_BG, highlightthickness=0)
        banner_cv.pack(fill=tk.X, padx=pad_x, pady=(0, int(15*s)))
        quote_font = ("Arial Rounded MT Bold", max(12, int(18 * s)), "bold")

        def _draw_banner(event=None):
            banner_cv.delete("banner")
            cw = banner_cv.winfo_width()
            ch = banner_cv.winfo_height()
            if cw > 1 and ch > 1:
                banner_cv.create_image(cw // 2, ch // 2, image=banner_tk, tags="banner")
                # 2-line quote at top-left corner of the banner
                banner_cv.create_text(int(24 * s), int(22 * s),
                                      text='"Until one has loved an animal,\na part of one\'s soul remains unawakened"',
                                      font=quote_font, fill="white", anchor="nw", tags="banner")
        banner_cv.bind("<Configure>", _draw_banner)

    # =====================================================
    # FORM HELPERS
    # =====================================================
    def _add_section_label(self, parent, text, padx):
        s = self._s
        f = tk.Frame(parent, bg=self.C_CARD_BG)
        f.pack(fill=tk.X, padx=padx, pady=(int(18*s), int(10*s)))
        tk.Label(f, text=text, font=self.F_SECTION, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        sep = tk.Frame(f, bg=self.C_DIVIDER, height=2)
        sep.pack(fill=tk.X, pady=(int(8*s), 0))

    def _add_labeled_entry(self, parent, label, placeholder, side=tk.LEFT, expand=False, full=False):
        s = self._s
        f = tk.Frame(parent, bg=self.C_CARD_BG)
        if full:
            f.pack(fill=tk.X)
        else:
            f.pack(side=side, fill=tk.X, expand=expand, padx=(0, int(10*s)))
        tk.Label(f, text=label, font=self.F_LABEL, bg=self.C_CARD_BG, fg=self.C_TEXT).pack(anchor="w")
        # Capsule input: white bg canvas, draw rounded-rect border outline
        entry_h = int(48 * s)
        border_cv = tk.Canvas(f, height=entry_h, bg=self.C_CARD_BG, highlightthickness=0)
        border_cv.pack(fill=tk.X, pady=(int(5*s), 0))
        entry = tk.Entry(border_cv, font=self.F_INPUT, relief=tk.FLAT, bg="white",
                         fg=self.C_TEXT, highlightthickness=0,
                         insertbackground=self.C_TEXT)
        entry.insert(0, placeholder)
        entry.config(fg=self.C_PLACEHOLDER)
        entry.bind("<FocusIn>", lambda e, en=entry, ph=placeholder: self._clear_placeholder(en, ph))
        entry.bind("<FocusOut>", lambda e, en=entry, ph=placeholder: self._set_placeholder(en, ph))
        win_id = border_cv.create_window(int(6*s), int(8*s), window=entry, anchor="w", tags="entry_win")
        def _draw_entry_border(event=None):
            border_cv.delete("efill")
            cw = border_cv.winfo_width()
            ch = border_cv.winfo_height()
            if cw > 1 and ch > 1:
                r = ch // 2
                bw = max(1, int(1.5*s))
                _round_rect(border_cv, 0, 0, cw, ch, radius=r, fill=self.C_BORDER, tags="efill")
                _round_rect(border_cv, bw, bw, cw-bw, ch-bw, radius=max(1, r-bw), fill="white", tags="efill")
                border_cv.itemconfig(win_id, width=cw - int(26*s))
                border_cv.coords(win_id, int(10*s), ch // 2)
        border_cv.bind("<Configure>", _draw_entry_border)
        return entry

    def _clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=self.C_TEXT)

    def _set_placeholder(self, entry, placeholder):
        if entry.get() == "":
            entry.insert(0, placeholder)
            entry.config(fg=self.C_PLACEHOLDER)

    def _add_chip(self, parent, text, active=False):
        s = self._s
        chip_h = int(42 * s)
        txt_len = len(text) if text else 3
        chip_w = int((txt_len * 18 + 36) * s)
        cv = tk.Canvas(parent, width=chip_w, height=chip_h,
                       bg=self.C_CARD_BG, highlightthickness=0)
        cv.pack(side=tk.LEFT, padx=(0, int(12*s)), pady=(int(4*s), 0))
        def _draw_chip(event=None):
            cv.delete("chip")
            cw = cv.winfo_width()
            ch = cv.winfo_height()
            if cw > 1 and ch > 1:
                r = ch // 2
                if active:
                    _round_rect(cv, 0, 0, cw, ch, radius=r, fill=self.C_ACTIVE, tags="chip")
                    cv.create_text(cw//2, ch//2, text=text, font=self.F_BTN, fill="white", tags="chip")
                else:
                    # Capsule: border color outer + white inner → clean 1px border
                    _round_rect(cv, 0, 0, cw, ch, radius=r, fill=self.C_CHIP_BORDER, tags="chip")
                    _round_rect(cv, 1, 1, cw-1, ch-1, radius=max(1, r-1), fill="white", tags="chip")
                    cv.create_text(cw//2, ch//2, text=text, font=self.F_BTN, fill=self.C_TEXT_LIGHT, tags="chip")
        cv.bind("<Configure>", _draw_chip)
        cv.bind("<Button-1>", lambda e: None)
        return cv

    def _add_toggle(self, parent):
        s = self._s
        var = tk.BooleanVar(value=False)
        tw, th = int(52*s), int(30*s)
        cv = tk.Canvas(parent, width=tw, height=th,
                       bg=self.C_CARD_BG, highlightthickness=0)
        cv.pack(anchor="w", pady=(int(4*s), 0))

        def draw_toggle():
            cv.delete("all")
            w, h = tw, th
            r = h // 2
            pad = int(2*s)
            thumb_d = h - 2*pad
            if var.get():
                _round_rect(cv, 0, 0, w, h, radius=r, fill=self.C_ACTIVE)
                cv.create_oval(w - h + pad, pad, w - pad, h - pad,
                              fill="white", outline="")
            else:
                _round_rect(cv, 0, 0, w, h, radius=r, fill=self.C_TOGGLE_OFF)
                cv.create_oval(pad, pad, h - pad, h - pad,
                              fill="white", outline="")

        draw_toggle()
        cv.bind("<Button-1>", lambda e: (var.set(not var.get()), draw_toggle()))
        return var


if __name__ == "__main__":
    app = BookingDashboard()
    app.mainloop()