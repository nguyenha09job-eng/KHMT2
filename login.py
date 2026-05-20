from __future__ import annotations

import math
import tkinter as tk
from collections import deque
from pathlib import Path

import mysql.connector
from PIL import Image, ImageFilter, ImageTk

from navigation import launch_page

# ── Paths ─────────────────────────────────────────────────────────────

def _find_project_root() -> Path:
    roots = []
    for start in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        roots.append(start)
        roots.extend(start.parents)

    seen = set()
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        if (root / "image" / "pet_login.png").exists():
            return root
    return Path(__file__).resolve().parent


_BASE = _find_project_root()
_EXTRACTED_DIR = _BASE / "assets" / "extracted"
_PET_LOGIN_IMG = _BASE / "image" / "pet_login.png"
_EXTRACTED_ANIMALS = [
    _BASE / "image" / "rabbit.png",
    _BASE / "image" / "duck.png",
    _BASE / "image" / "turtle.png",
    _BASE / "image" / "cat.png",
]

# ── Themes (4 colours matching the 4 designs) ─────────────────────────
THEMES = [
    {"name": "Rose", "bg": "#f2abb7",
     "text": "#4e352d", "text_light": "#7a5a52",
     "input_bg": "#ffffff", "input_border": "#e8c0c8",
     "btn_bg": "#4e352d", "btn_text": "#ffffff", "btn_hover": "#3a2520"},
    {"name": "Lime", "bg": "#d2e47b",
     "text": "#3d4a2e", "text_light": "#5a6640",
     "input_bg": "#ffffff", "input_border": "#c8d888",
     "btn_bg": "#3d4a2e", "btn_text": "#ffffff", "btn_hover": "#2a3620"},
    {"name": "Teal", "bg": "#6abab3",
     "text": "#2d3e3c", "text_light": "#4d605e",
     "input_bg": "#ffffff", "input_border": "#8cd0ca",
     "btn_bg": "#2d3e3c", "btn_text": "#ffffff", "btn_hover": "#1e2e2c"},
    {"name": "Gold", "bg": "#feaf42",
     "text": "#4a3d2e", "text_light": "#6e5e45",
     "input_bg": "#ffffff", "input_border": "#f5c878",
     "btn_bg": "#4a3d2e", "btn_text": "#ffffff", "btn_hover": "#362b20"},
]

# ── Helpers ────────────────────────────────────────────────────────────

def _rounded_rect_poly(
    x1: float, y1: float, x2: float, y2: float, r: float, steps: int = 8,
) -> list[float]:
    pts: list[float] = []

    def arc(cx: float, cy: float, start_deg: float, end_deg: float) -> None:
        for i in range(steps):
            a = math.radians(start_deg + (end_deg - start_deg) * i / (steps - 1))
            pts.append(cx + r * math.cos(a))
            pts.append(cy + r * math.sin(a))

    pts.extend([x1 + r, y1, x2 - r, y1])
    arc(x2 - r, y1 + r, -90, 0)
    pts.extend([x2, y2 - r])
    arc(x2 - r, y2 - r, 0, 90)
    pts.extend([x1 + r, y2])
    arc(x1 + r, y2 - r, 90, 180)
    pts.extend([x1, y1 + r])
    arc(x1 + r, y1 + r, 180, 270)
    return pts


def _extract_pets() -> None:
    """Trích xuất thú từ pet_login.png nếu chưa có."""
    if all(p.exists() for p in _EXTRACTED_ANIMALS):
        return
    if not _PET_LOGIN_IMG.exists():
        return

    _EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.open(_PET_LOGIN_IMG).convert("RGB")
    w, h = img.size
    px = list(img.getdata())

    mask = [False] * (w * h)
    for i, (r, g, b) in enumerate(px):
        mask[i] = ((r - 255) ** 2 + (g - 255) ** 2 + (b - 255) ** 2) ** 0.5 > 30

    pil = Image.new("L", (w, h))
    pil.putdata([255 if v else 0 for v in mask])
    for _ in range(3):
        pil = pil.filter(ImageFilter.MaxFilter(5))
    dilated = [v > 128 for v in pil.getdata()]

    visited = [False] * (w * h)
    comps: list[tuple[int, int, int, int, int]] = []
    for y in range(h):
        for x in range(w):
            idx = y * w + x
            if not dilated[idx] or visited[idx]:
                continue
            q: deque[tuple[int, int]] = deque()
            q.append((x, y))
            visited[idx] = True
            mx = Mx = x
            my = My = y
            cnt = 0
            while q:
                cx, cy = q.popleft()
                cnt += 1
                mx, Mx = min(mx, cx), max(Mx, cx)
                my, My = min(my, cy), max(My, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        nid = ny * w + nx
                        if dilated[nid] and not visited[nid]:
                            visited[nid] = True
                            q.append((nx, ny))
            if cnt >= 5000:
                comps.append((mx, my, Mx, My, cnt))

    valid = [(mx, my, Mx, My, c) for mx, my, Mx, My, c in comps
             if not (Mx - mx < 10 and (mx < 5 or Mx > w - 5)) and Mx - mx < w * 0.9]
    top4 = sorted(valid, key=lambda c: c[4], reverse=True)[:4]
    top4.sort(key=lambda c: (c[1], c[0]))

    for i, (mx, my, Mx, My, _) in enumerate(top4):
        crop = img.crop((mx, my, Mx + 1, My + 1))
        cw, ch = crop.size
        cp = list(crop.getdata())
        alpha = []
        for cr, cg, cb in cp:
            d = ((cr - 255) ** 2 + (cg - 255) ** 2 + (cb - 255) ** 2) ** 0.5
            t = max(0.0, min((d - 15) / 25, 1.0))
            alpha.append(int(t * t * (3 - 2 * t) * 255))
        out_img = Image.new("RGBA", (cw, ch))
        out_img.putdata([(cp[j][0], cp[j][1], cp[j][2], alpha[j]) for j in range(len(cp))])
        out_img.save(_EXTRACTED_DIR / f"animal_{i + 1}.png", "PNG")


def _db_fetch_one(query: str, params: tuple) -> dict | None:
    try:
        conn = mysql.connector.connect(
            host="localhost", port=3306, user="root",
            password="123456", database="PetHotel",
        )
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception:
        return None


# ── App ────────────────────────────────────────────────────────────────
class LoginApp:
    def __init__(self) -> None:
        _extract_pets()

        self.root = tk.Tk()
        self.root.title("Pet&Bed")

        # Fullscreen + lấy kích thước thật
        self.root.attributes("-fullscreen", True)
        self.root.update_idletasks()

        self.W = self.root.winfo_width()
        self.H = self.root.winfo_height()

        # Hệ số scale (thiết kế gốc 768px chiều cao)
        s = self.H / 768.0
        self._s = max(0.7, min(s, 2.5))

        self._idx = 0
        self._t = THEMES[0]
        self._timer_id: str | None = None
        self._auth_busy = False

        self._pet_photos: list[ImageTk.PhotoImage | None] = []
        self._load_pets()
        self._build_ui()
        self._draw_theme(0)
        self._start_slideshow()

    # ── Pet images ───────────────────────────────────────────────
    def _load_pets(self) -> None:
        target = int(280 * self._s)
        for path in _EXTRACTED_ANIMALS:
            if path.exists():
                pil = Image.open(path)
                w, h = pil.size
                nw = target if w >= h else int(w * target / h)
                nh = target if h >= w else int(h * target / w)
                pil = pil.resize((nw, nh), Image.LANCZOS)
                self._pet_photos.append(ImageTk.PhotoImage(pil))
            else:
                self._pet_photos.append(None)

    # ── Build UI ────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self._cv = tk.Canvas(
            self.root, width=self.W, height=self.H,
            highlightthickness=0,
        )
        self._cv.place(x=0, y=0)

        cx = self.W // 2
        s = self._s

        fs_t = max(14, int(50 * s))
        fs_tg = max(8, int(13 * s))
        fs_btn = max(10, int(15 * s))
        fs_msg = max(8, int(11 * s))
        fs_in = max(8, int(18 * s))

        # ── Căn giữa dọc ──
        cc = int(338 * s)
        off = max(0, self.H // 2 - cc)

        py = int(155 * s) + off
        self._pet_item = self._cv.create_image(cx, py, anchor=tk.CENTER)

        ty = py + int(130 * s)
        self._title_item = self._cv.create_text(
            cx, ty, text="Pet&Bed",
            font=("Arial Rounded MT Bold", fs_t, "bold"),
        )

        tgy = ty + int(38 * s)
        self._tagline_item = self._cv.create_text(
            cx, tgy, text="A happy place for your furry friends",
            font=("Baghdad", fs_tg),
        )

        iw = int(280 * s)
        ih = int(50 * s)
        ir = max(4, int(22 * s))
        gap = int(16 * s)
        ix1, ix2 = cx - iw // 2, cx + iw // 2
        ew = max(12, int(iw / 16))

        # Name input
        niy1 = tgy + int(35 * s)
        niy2 = niy1 + ih
        self._name_bg = self._cv.create_polygon(
            _rounded_rect_poly(ix1, niy1, ix2, niy2, ir),
            width=1, smooth=False,
        )
        self._name_entry = tk.Entry(
            self._cv, font=("Baghdad", fs_in), relief=tk.FLAT, bd=0,
            highlightthickness=0, width=ew,
        )
        self._name_entry.insert(0, "Your Full Name")
        self._name_entry.bind("<FocusIn>", self._on_focus_in_name)
        self._name_entry.bind("<FocusOut>", self._on_focus_out_name)
        self._name_win = self._cv.create_window(
            cx, niy1 + ih // 2, window=self._name_entry,
            width=iw - int(48 * s), height=int(30 * s),
        )

        # ID input
        iiy1 = niy2 + gap
        iiy2 = iiy1 + ih
        self._id_bg = self._cv.create_polygon(
            _rounded_rect_poly(ix1, iiy1, ix2, iiy2, ir),
            width=1, smooth=False,
        )
        self._id_entry = tk.Entry(
            self._cv, font=("Baghdad", fs_in), relief=tk.FLAT, bd=0,
            highlightthickness=0, width=ew,
        )
        self._id_entry.insert(0, "Your ID")
        self._id_entry.bind("<FocusIn>", self._on_focus_in_id)
        self._id_entry.bind("<FocusOut>", self._on_focus_out_id)
        self._id_win = self._cv.create_window(
            cx, iiy1 + ih // 2, window=self._id_entry,
            width=iw - int(48 * s), height=int(30 * s),
        )

        # Button
        bw = int(140 * s)
        bh = int(38 * s)
        br = max(4, int(22 * s))
        b_y1 = iiy2 + int(20 * s)
        b_y2 = b_y1 + bh
        bx1, bx2 = cx - bw // 2, cx + bw // 2
        self._btn_bg = self._cv.create_polygon(
            _rounded_rect_poly(bx1, b_y1, bx2, b_y2, br),
            width=0, smooth=False,
        )
        self._btn_txt = self._cv.create_text(
            cx, b_y1 + bh // 2, text="Log In",
            font=("Arial Rounded MT Bold", fs_btn, "bold"),
        )

        for tag in (self._btn_bg, self._btn_txt):
            self._cv.tag_bind(tag, "<Button-1>", self._on_login)
            self._cv.tag_bind(tag, "<Enter>", self._on_btn_enter)
            self._cv.tag_bind(tag, "<Leave>", self._on_btn_leave)

        # Message
        self._msg_item = self._cv.create_text(
            cx, b_y2 + int(22 * s), text="", font=("Baghdad", fs_msg),
        )

        # Key binds
        self._name_entry.bind("<Return>", lambda _e: self._id_entry.focus_set())
        self._id_entry.bind("<Return>", lambda _e: self._on_login(None))

    # ── Theme ────────────────────────────────────────────────────
    def _draw_theme(self, idx: int) -> None:
        t = THEMES[idx]
        self._t, self._idx = t, idx
        self._cv.configure(bg=t["bg"])
        self._cv.itemconfig(self._title_item, fill=t["text"])
        self._cv.itemconfig(self._tagline_item, fill=t["text_light"])

        ph = self._name_entry.get() in ("", "Your Full Name")
        self._name_entry.configure(
            bg=t["input_bg"], fg=t["text_light"] if ph else t["text"],
            insertbackground=t["text"],
        )
        self._cv.itemconfig(self._name_bg, fill=t["input_bg"], outline=t["input_border"])

        ph2 = self._id_entry.get() in ("", "Your ID")
        self._id_entry.configure(
            bg=t["input_bg"], fg=t["text_light"] if ph2 else t["text"],
            insertbackground=t["text"],
        )
        self._cv.itemconfig(self._id_bg, fill=t["input_bg"], outline=t["input_border"])

        self._cv.itemconfig(self._btn_bg, fill=t["btn_bg"])
        self._cv.itemconfig(self._btn_txt, fill=t["btn_text"])
        self._cv.itemconfig(self._msg_item, fill=t["text_light"])

        pi = idx % len(self._pet_photos)
        if self._pet_photos[pi]:
            self._cv.itemconfig(self._pet_item, image=self._pet_photos[pi])

    # ── Slideshow ────────────────────────────────────────────────
    def _start_slideshow(self) -> None:
        self._schedule_next()

    def _schedule_next(self) -> None:
        if self._timer_id:
            self._cv.after_cancel(self._timer_id)
        self._timer_id = self._cv.after(3000, self._next_slide)

    def _next_slide(self) -> None:
        self._draw_theme((self._idx + 1) % len(THEMES))
        self._schedule_next()

    # ── Focus handlers ───────────────────────────────────────────
    def _on_focus_in_name(self, _e: object) -> None:
        if self._name_entry.get() == "Your Full Name":
            self._name_entry.delete(0, tk.END)
            self._name_entry.configure(fg=self._t["text"])

    def _on_focus_out_name(self, _e: object) -> None:
        if self._name_entry.get() == "":
            self._name_entry.insert(0, "Your Full Name")
            self._name_entry.configure(fg=self._t["text_light"])

    def _on_focus_in_id(self, _e: object) -> None:
        if self._id_entry.get() == "Your ID":
            self._id_entry.delete(0, tk.END)
            self._id_entry.configure(fg=self._t["text"])

    def _on_focus_out_id(self, _e: object) -> None:
        if self._id_entry.get() == "":
            self._id_entry.insert(0, "Your ID")
            self._id_entry.configure(fg=self._t["text_light"])

    # ── Button ───────────────────────────────────────────────────
    def _on_btn_enter(self, _e: object) -> None:
        self._cv.itemconfig(self._btn_bg, fill=self._t["btn_hover"])

    def _on_btn_leave(self, _e: object) -> None:
        self._cv.itemconfig(self._btn_bg, fill=self._t["btn_bg"])

    def _on_login(self, _e: object | None = None) -> None:
        if self._auth_busy:
            return
        name = self._name_entry.get().strip()
        uid = self._id_entry.get().strip()
        if name in ("", "Your Full Name"):
            self._cv.itemconfig(self._msg_item, text="Please enter your full name")
            return
        if uid in ("", "Your ID"):
            self._cv.itemconfig(self._msg_item, text="Please enter your ID")
            return
        self._cv.itemconfig(self._msg_item, text="")
        self._auth_busy = True
        self.root.after(200, lambda: self._do_auth(name, uid))

    def _do_auth(self, name: str, uid: str) -> None:
        try:
            cust = _db_fetch_one(
                "SELECT customer_id, full_name FROM customers "
                "WHERE full_name = %s AND customer_id = %s",
                (name, uid),
            )
            if cust:
                self._cv.itemconfig(self._msg_item,
                                     text=f"Welcome, {cust['full_name']}!",
                                     fill="#2ecc71")
                self.root.after(650, self._open_dashboard)
            else:
                self._cv.itemconfig(self._msg_item,
                                     text="Account not found.",
                                     fill=self._t["text"])
        except Exception as e:
            self._cv.itemconfig(self._msg_item, text=str(e), fill=self._t["text"])
        finally:
            self._auth_busy = False

    def _open_dashboard(self) -> None:
        if self._timer_id:
            self._cv.after_cancel(self._timer_id)
            self._timer_id = None
        launch_page("Dashboard")
        self.root.destroy()

    # ── Lifecycle ────────────────────────────────────────────────
    def run(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self) -> None:
        if self._timer_id:
            self._cv.after_cancel(self._timer_id)
        self.root.destroy()


if __name__ == "__main__":
    LoginApp().run()
