"""
ОКФРС. Практика 7. Задание 10.
Загрузка своих наборов данных + визуализация
различными типами диаграмм.
Премиум-стиль 2026.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import sys, os, math, random, time, csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# ПАЛИТРА
# ============================================================
BG_DEEP    = "#08090f"
BG_GLASS   = "#131823"
BG_GRAPH   = "#050810"
BG_PANEL   = "#0f141c"
BG_CELL    = "#0e1218"
BORDER     = "#232a3d"

NEON_CYAN  = "#00f0ff"
NEON_GREEN = "#39ff88"
NEON_PINK  = "#ff3ea5"
NEON_PURP  = "#a066ff"
NEON_AMBER = "#ffb830"
NEON_RED   = "#ff4d5e"
NEON_BLUE  = "#4d8dff"
NEON_ORANGE= "#ff8c42"

CHART_COLORS = [
    NEON_CYAN, NEON_GREEN, NEON_PINK, NEON_PURP,
    NEON_AMBER, NEON_RED, NEON_BLUE, NEON_ORANGE,
]

TEXT_MAIN  = "#e8f0ff"
TEXT_DIM   = "#5a6780"
TEXT_GLOW  = "#8fa4c4"

FONT_MONO  = ("Consolas", 13, "bold")
FONT_MONO_S= ("Consolas", 10)
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_LABEL_S = ("Segoe UI", 9)


def lerp(c1, c2, t):
    t = max(0.0, min(1.0, float(t)))
    try:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    except Exception:
        return c1
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(r1 + (r2 - r1) * t))),
        max(0, min(255, int(g1 + (g2 - g1) * t))),
        max(0, min(255, int(b1 + (b2 - b1) * t))))


def round_rect(canvas, x1, y1, x2, y2, r,
               fill=None, outline=None, width=1, tags=""):
    pts = []
    steps = 8
    for i in range(steps + 1):
        a = math.pi + (math.pi / 2) * (i / steps)
        pts.extend([x1 + r + r * math.cos(a), y1 + r + r * math.sin(a)])
    for i in range(steps + 1):
        a = -math.pi/2 + (math.pi / 2) * (i / steps)
        pts.extend([x2 - r + r * math.cos(a), y1 + r + r * math.sin(a)])
    for i in range(steps + 1):
        a = 0 + (math.pi / 2) * (i / steps)
        pts.extend([x2 - r + r * math.cos(a), y2 - r + r * math.sin(a)])
    for i in range(steps + 1):
        a = math.pi/2 + (math.pi / 2) * (i / steps)
        pts.extend([x1 + r + r * math.cos(a), y2 - r + r * math.sin(a)])
    return canvas.create_polygon(pts, fill=fill or "", outline=outline or "",
                                 width=width, smooth=False, tags=tags)


# ============================================================
# ВСТРОЕННЫЕ ДАТАСЕТЫ
# ============================================================
def make_sample_data():
    datasets = {}

    months = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
              "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    sales = [random.uniform(50, 200) for _ in months]
    datasets["Продажи по месяцам"] = {
        "labels": months,
        "series": [{"name": "Продажи, тыс.₽", "values": sales}],
    }

    days = [f"Д{i+1}" for i in range(14)]
    temp_day = [random.uniform(15, 28) for _ in days]
    temp_night = [random.uniform(5, 15) for _ in days]
    datasets["Температура 2 недели"] = {
        "labels": days,
        "series": [
            {"name": "День", "values": temp_day},
            {"name": "Ночь", "values": temp_night},
        ],
    }

    cats = ["Поиск", "Соцсети", "Прямые", "Реклама", "Email"]
    vals = [random.uniform(20, 100) for _ in cats]
    datasets["Источники трафика"] = {
        "labels": cats,
        "series": [{"name": "Визиты", "values": vals}],
    }

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    revenue = [random.uniform(500, 900) for _ in quarters]
    expenses = [random.uniform(300, 600) for _ in quarters]
    profit = [r - e for r, e in zip(revenue, expenses)]
    datasets["Финансы компании"] = {
        "labels": quarters,
        "series": [
            {"name": "Доход", "values": revenue},
            {"name": "Расход", "values": expenses},
            {"name": "Прибыль", "values": profit},
        ],
    }

    hours = [f"{h:02d}:00" for h in range(0, 24, 2)]
    cpu = [random.uniform(20, 90) for _ in hours]
    ram = [random.uniform(30, 80) for _ in hours]
    datasets["Нагрузка сервера"] = {
        "labels": hours,
        "series": [
            {"name": "CPU %", "values": cpu},
            {"name": "RAM %", "values": ram},
        ],
    }

    return datasets


# ============================================================
# ТИПЫ ДИАГРАММ
# ============================================================
CHART_TYPES = [
    ("bar",     "СТОЛБ"),
    ("hbar",    "ГОРИЗ"),
    ("line",    "ЛИНИЯ"),
    ("area",    "ОБЛАСТЬ"),
    ("scatter", "ТОЧКИ"),
    ("pie",     "КРУГ"),
    ("stacked", "НАКОП"),
]


# ============================================================
# ОТРИСОВКА ДИАГРАММ
# ============================================================
def draw_chart(canvas, x, y, w, h, chart_type, labels, series):
    if not series or not labels:
        canvas.create_text(x + w / 2, y + h / 2,
                           text="Нет данных для отображения",
                           fill=TEXT_DIM, font=FONT_LABEL)
        return

    if chart_type == "bar":
        _draw_bar(canvas, x, y, w, h, labels, series)
    elif chart_type == "hbar":
        _draw_hbar(canvas, x, y, w, h, labels, series)
    elif chart_type == "line":
        _draw_lines(canvas, x, y, w, h, labels, series)
    elif chart_type == "area":
        _draw_area(canvas, x, y, w, h, labels, series)
    elif chart_type == "scatter":
        _draw_scatter(canvas, x, y, w, h, labels, series)
    elif chart_type == "pie":
        _draw_pie(canvas, x, y, w, h, labels, series[0]["values"])
    elif chart_type == "stacked":
        _draw_stacked(canvas, x, y, w, h, labels, series)


def _axes(canvas, gx0, gy0, gx1, gy1, max_v):
    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = k * max_v
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=("Consolas", 8))
    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


def _legend(canvas, x, y, w, series):
    n = len(series)
    if n == 0:
        return
    item_w = 160
    total_w = item_w * n
    start_x = x + (w - total_w) / 2
    for i, s in enumerate(series):
        lx = start_x + i * item_w
        col = CHART_COLORS[i % len(CHART_COLORS)]
        canvas.create_rectangle(lx, y - 4, lx + 16, y + 10,
                                 fill=col, outline="")
        canvas.create_text(lx + 22, y + 3, anchor="w",
                           text=s["name"],
                           fill=TEXT_MAIN, font=("Segoe UI", 9, "bold"))


def _draw_bar(canvas, x, y, w, h, labels, series):
    pad_l, pad_r, pad_t, pad_b = 55, 25, 60, 55
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    n_s = len(series)
    n_l = len(labels)
    max_v = 0
    for s in series:
        if s["values"]:
            max_v = max(max_v, max(s["values"]))
    if max_v < 1:
        max_v = 1

    _legend(canvas, x + 20, y + 25, w - 40, series)
    _axes(canvas, gx0, gy0, gx1, gy1, max_v)

    step = (gx1 - gx0) / n_l
    group_w = step * 0.75
    bar_w = group_w / n_s

    for i, lbl in enumerate(labels):
        gx = gx0 + i * step + (step - group_w) / 2
        for j, s in enumerate(series):
            v = s["values"][i] if i < len(s["values"]) else 0
            bx = gx + j * bar_w
            by_top = gy1 - (v / max_v) * (gy1 - gy0)
            col = CHART_COLORS[j % len(CHART_COLORS)]
            canvas.create_rectangle(bx, by_top, bx + bar_w - 2, gy1,
                                     fill=col,
                                     outline=lerp(col, "#ffffff", 0.3),
                                     width=1)
            canvas.create_rectangle(bx + 2, by_top + 2,
                                     bx + bar_w - 4, by_top + 5,
                                     fill=lerp(col, "#ffffff", 0.5),
                                     outline="")
        canvas.create_text(gx0 + i * step + step / 2, gy1 + 15,
                           text=lbl, fill=TEXT_DIM,
                           font=("Consolas", 9))


def _draw_hbar(canvas, x, y, w, h, labels, series):
    pad_l, pad_r, pad_t, pad_b = 100, 60, 60, 30
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    n_s = len(series)
    n_l = len(labels)
    max_v = 0
    for s in series:
        if s["values"]:
            max_v = max(max_v, max(s["values"]))
    if max_v < 1:
        max_v = 1

    _legend(canvas, x + 20, y + 25, w - 40, series)

    for i in range(6):
        k = i / 5
        xx = gx0 + k * (gx1 - gx0)
        val = k * max_v
        canvas.create_line(xx, gy0, xx, gy1,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(xx, gy1 + 15, text=f"{val:.0f}",
                           fill=TEXT_DIM, font=("Consolas", 8))

    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)

    step = (gy1 - gy0) / n_l
    group_h = step * 0.75
    bar_h = group_h / n_s

    for i, lbl in enumerate(labels):
        gy = gy0 + i * step + (step - group_h) / 2
        for j, s in enumerate(series):
            v = s["values"][i] if i < len(s["values"]) else 0
            by = gy + j * bar_h
            bx_right = gx0 + (v / max_v) * (gx1 - gx0)
            col = CHART_COLORS[j % len(CHART_COLORS)]
            canvas.create_rectangle(gx0, by, bx_right, by + bar_h - 2,
                                     fill=col,
                                     outline=lerp(col, "#ffffff", 0.3),
                                     width=1)
        canvas.create_text(gx0 - 8, gy + group_h / 2, anchor="e",
                           text=lbl, fill=TEXT_DIM,
                           font=("Consolas", 9))


def _draw_lines(canvas, x, y, w, h, labels, series):
    pad_l, pad_r, pad_t, pad_b = 55, 25, 60, 55
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = 0
    for s in series:
        if s["values"]:
            max_v = max(max_v, max(s["values"]))
    if max_v < 1:
        max_v = 1

    _legend(canvas, x + 20, y + 25, w - 40, series)
    _axes(canvas, gx0, gy0, gx1, gy1, max_v)

    n = len(labels)
    step = (gx1 - gx0) / max(1, n - 1)

    for j, s in enumerate(series):
        col = CHART_COLORS[j % len(CHART_COLORS)]
        pts = []
        for i, v in enumerate(s["values"]):
            if i >= n:
                break
            px = gx0 + i * step
            py = gy1 - (v / max_v) * (gy1 - gy0)
            pts.append((px, py))

        if len(pts) >= 2:
            flat = []
            for (px, py) in pts:
                flat.extend([px, py])
            canvas.create_line(*flat,
                               fill=lerp(col, BG_GRAPH, 0.5),
                               width=6, smooth=True)
            canvas.create_line(*flat, fill=col, width=2, smooth=True)

        for (px, py) in pts:
            canvas.create_oval(px - 4, py - 4, px + 4, py + 4,
                               fill=col, outline="#ffffff", width=1)

    for i, lbl in enumerate(labels):
        if n <= 12 or i % 2 == 0:
            px = gx0 + i * step
            canvas.create_text(px, gy1 + 15, text=lbl,
                               fill=TEXT_DIM,
                               font=("Consolas", 8))


def _draw_area(canvas, x, y, w, h, labels, series):
    pad_l, pad_r, pad_t, pad_b = 55, 25, 60, 55
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = 0
    for s in series:
        if s["values"]:
            max_v = max(max_v, max(s["values"]))
    if max_v < 1:
        max_v = 1

    _legend(canvas, x + 20, y + 25, w - 40, series)
    _axes(canvas, gx0, gy0, gx1, gy1, max_v)

    n = len(labels)
    step = (gx1 - gx0) / max(1, n - 1)

    for j, s in enumerate(series):
        col = CHART_COLORS[j % len(CHART_COLORS)]
        pts = [(gx0, gy1)]
        for i, v in enumerate(s["values"]):
            if i >= n:
                break
            px = gx0 + i * step
            py = gy1 - (v / max_v) * (gy1 - gy0)
            pts.append((px, py))
        if len(pts) > 1:
            pts.append((pts[-1][0], gy1))

        if len(pts) >= 3:
            flat = []
            for (px, py) in pts:
                flat.extend([px, py])
            canvas.create_polygon(flat,
                                  fill=lerp(col, BG_GRAPH, 0.6),
                                  outline=col, width=2)

    for i, lbl in enumerate(labels):
        if n <= 12 or i % 2 == 0:
            px = gx0 + i * step
            canvas.create_text(px, gy1 + 15, text=lbl,
                               fill=TEXT_DIM,
                               font=("Consolas", 8))


def _draw_scatter(canvas, x, y, w, h, labels, series):
    pad_l, pad_r, pad_t, pad_b = 55, 25, 60, 55
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = 0
    for s in series:
        if s["values"]:
            max_v = max(max_v, max(s["values"]))
    if max_v < 1:
        max_v = 1

    _legend(canvas, x + 20, y + 25, w - 40, series)
    _axes(canvas, gx0, gy0, gx1, gy1, max_v)

    n = len(labels)
    step = (gx1 - gx0) / max(1, n - 1)

    for j, s in enumerate(series):
        col = CHART_COLORS[j % len(CHART_COLORS)]
        for i, v in enumerate(s["values"]):
            if i >= n:
                break
            px = gx0 + i * step + (j - len(series)/2) * 5
            py = gy1 - (v / max_v) * (gy1 - gy0)
            for k in range(3, 0, -1):
                rr = 6 + k * 3
                canvas.create_oval(px - rr, py - rr, px + rr, py + rr,
                                   fill="", outline=lerp(col, BG_GRAPH,
                                                          1 - k / 4),
                                   width=1)
            canvas.create_oval(px - 6, py - 6, px + 6, py + 6,
                               fill=col, outline="#ffffff", width=2)

    for i, lbl in enumerate(labels):
        if n <= 12 or i % 2 == 0:
            px = gx0 + i * step
            canvas.create_text(px, gy1 + 15, text=lbl,
                               fill=TEXT_DIM,
                               font=("Consolas", 8))


def _draw_pie(canvas, x, y, w, h, labels, values):
    total = sum(values) if values else 1
    cx = x + w / 2
    cy = y + h / 2 - 20
    r = min(w, h) * 0.30

    canvas.create_oval(cx - r + 4, cy - r + 6, cx + r + 4, cy + r + 6,
                       fill="#000000", outline="")

    angle_start = 90
    for i, v in enumerate(values):
        extent = -(v / total) * 360
        col = CHART_COLORS[i % len(CHART_COLORS)]
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                          start=angle_start, extent=extent,
                          fill=col,
                          outline=lerp(col, "#ffffff", 0.3), width=2)
        mid = math.radians(angle_start + extent / 2)
        tx = cx + r * 0.65 * math.cos(mid)
        ty = cy - r * 0.65 * math.sin(mid)
        pct = v / total * 100
        if pct > 6:
            canvas.create_text(tx, ty, text=f"{pct:.0f}%",
                               fill="#ffffff",
                               font=("Consolas", 10, "bold"))
        angle_start += extent

    legend_y = y + h - 25
    n = len(labels)
    if n > 0:
        item_w = min(110, (w - 20) / n)
        total_w = item_w * n
        sx = x + (w - total_w) / 2
        for i in range(n):
            lx = sx + i * item_w
            col = CHART_COLORS[i % len(CHART_COLORS)]
            canvas.create_rectangle(lx, legend_y - 5,
                                     lx + 14, legend_y + 9,
                                     fill=col, outline="")
            canvas.create_text(lx + 20, legend_y + 2, anchor="w",
                               text=labels[i] if i < len(labels) else str(i),
                               fill=TEXT_DIM, font=("Consolas", 8))


def _draw_stacked(canvas, x, y, w, h, labels, series):
    pad_l, pad_r, pad_t, pad_b = 55, 25, 60, 55
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    n = len(labels)
    if n == 0:
        return

    totals = []
    for i in range(n):
        s = 0
        for ser in series:
            if i < len(ser["values"]):
                s += ser["values"][i]
        totals.append(s)
    max_v = max(totals) if totals else 1

    _legend(canvas, x + 20, y + 25, w - 40, series)
    _axes(canvas, gx0, gy0, gx1, gy1, max_v)

    step = (gx1 - gx0) / n
    bar_w = step * 0.65

    for i in range(n):
        bx = gx0 + i * step + (step - bar_w) / 2
        cum = 0
        for j, s in enumerate(series):
            v = s["values"][i] if i < len(s["values"]) else 0
            h_ = (v / max_v) * (gy1 - gy0)
            col = CHART_COLORS[j % len(CHART_COLORS)]
            canvas.create_rectangle(bx, gy1 - cum - h_,
                                     bx + bar_w, gy1 - cum,
                                     fill=col,
                                     outline=lerp(col, "#ffffff", 0.3),
                                     width=1)
            cum += h_

        canvas.create_text(bx + bar_w / 2, gy1 - cum - 10,
                           text=f"{totals[i]:.1f}",
                           fill=NEON_AMBER, font=("Consolas", 9, "bold"))

        canvas.create_text(bx + bar_w / 2, gy1 + 15,
                           text=labels[i], fill=TEXT_DIM,
                           font=("Consolas", 9))


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.datasets = make_sample_data()
        self.dataset_keys = list(self.datasets.keys())
        self.current_idx = 0
        self.chart_type = "bar"
        self.max_rows = 0

    def current(self):
        return self.datasets[self.dataset_keys[self.current_idx]]

    def labels(self):
        lbls = self.current()["labels"]
        if self.max_rows > 0:
            return lbls[:self.max_rows]
        return lbls

    def series(self):
        result = []
        for s in self.current()["series"]:
            values = s["values"]
            if self.max_rows > 0:
                values = values[:self.max_rows]
            result.append({"name": s["name"], "values": values})
        return result

    def select_dataset(self, idx):
        if 0 <= idx < len(self.dataset_keys):
            self.current_idx = idx
            self.max_rows = 0

    def add_custom_dataset(self, name, labels, series):
        self.datasets[name] = {"labels": labels, "series": series}
        self.dataset_keys = list(self.datasets.keys())
        self.current_idx = self.dataset_keys.index(name)
        self.max_rows = 0


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Data Visualization · Dashboard")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0

        self.state = AppState()
        self.btn_zones = {}
        self.slider_rect = None
        self.drag_slider = False

        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        self.root.update_idletasks()
        self._redraw_all()
        self._animate()

    def _on_resize(self, event):
        self._redraw_all()

    def _draw_bg(self, w, h):
        for i in range(40):
            y0 = int(i * h / 40)
            y1 = int((i + 1) * h / 40)
            col = lerp(BG_DEEP, "#0a0e18", i / 40)
            self.canvas.create_rectangle(0, y0, w, y1, fill=col, outline="")

    def _draw_header(self, w):
        self.canvas.create_text(60, 40, text="📊",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="DATA VISUALIZATION",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(390, 44,
                                text="· ДАШБОРД",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    def _draw_dataset_bar(self, w, y):
        round_rect(self.canvas, 50, y, w - 50, y + 60, 12,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 30, anchor="w",
                                text="ДАТАСЕТ:",
                                fill=TEXT_DIM, font=FONT_LABEL)

        n = len(self.state.dataset_keys)
        btn_w = 180
        btn_h = 40
        gap = 6
        start_x = 160

        for i, key in enumerate(self.state.dataset_keys):
            bx = start_x + i * (btn_w + gap)
            if bx + btn_w > w - 60 - 200:
                break
            active = (i == self.state.current_idx)
            self._draw_dataset_btn(bx, y + 10, btn_w, btn_h, i, key, active)

        # загрузка CSV
        bx = w - 60 - 180
        round_rect(self.canvas, bx, y + 10, bx + 170, y + 50, 8,
                   fill=lerp(NEON_GREEN, BG_DEEP, 0.8),
                   outline=NEON_GREEN, width=1)
        self.canvas.create_text(bx + 85, y + 30,
                                text="📁 ЗАГРУЗИТЬ CSV",
                                fill=NEON_GREEN,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones["load_csv"] = (bx, y + 10, bx + 170, y + 50)

    def _draw_dataset_btn(self, x, y, w, h, idx, label, active):
        if active:
            for i in range(3, 0, -1):
                round_rect(self.canvas, x - i, y - i,
                           x + w + i, y + h + i, 8 + i,
                           outline=lerp(NEON_CYAN, BG_DEEP, i / 4), width=1)
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(NEON_CYAN, BG_DEEP, 0.6),
                       outline=NEON_CYAN, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=NEON_CYAN,
                                    font=("Segoe UI", 10, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"ds_{idx}"] = (x, y, x + w, y + h)

    def _draw_type_bar(self, w, y):
        round_rect(self.canvas, 50, y, w - 50, y + 55, 12,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 27, anchor="w",
                                text="ТИП:",
                                fill=TEXT_DIM, font=FONT_LABEL)

        btn_w = 140
        btn_h = 36
        gap = 6
        start_x = 130

        for i, (key, label) in enumerate(CHART_TYPES):
            bx = start_x + i * (btn_w + gap)
            if bx + btn_w > w - 60:
                break
            active = (self.state.chart_type == key)
            self._draw_type_btn(bx, y + 9, btn_w, btn_h, key, label, active)

    def _draw_type_btn(self, x, y, w, h, key, label, active):
        color = NEON_AMBER
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.6),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Segoe UI", 10, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 10, "bold"))
        self.btn_zones[f"type_{key}"] = (x, y, x + w, y + h)

    def _draw_chart_area(self, w, y, h):
        panel_w = 340
        chart_w = w - 100 - panel_w - 20

        round_rect(self.canvas, 50, y, 50 + chart_w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        ds_name = self.state.dataset_keys[self.state.current_idx]
        t = next((x[1] for x in CHART_TYPES if x[0] == self.state.chart_type),
                 "CHART")
        self.canvas.create_text(70, y + 25, anchor="w",
                                text=f"▸ {ds_name}  ·  {t}",
                                fill=NEON_CYAN, font=FONT_LABEL)

        gx = 70
        gy = y + 50
        gw = chart_w - 40
        gh = h - 70

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        labels = self.state.labels()
        series = self.state.series()

        try:
            draw_chart(self.canvas, gx, gy, gw, gh,
                       self.state.chart_type, labels, series)
        except Exception as e:
            self.canvas.create_text(gx + gw / 2, gy + gh / 2,
                                    text=f"Ошибка: {e}",
                                    fill=NEON_RED, font=FONT_LABEL)

    def _draw_panel(self, w, y, h):
        panel_w = 340
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ ИНФО",
                                fill=NEON_PURP, font=FONT_LABEL)

        ds = self.state.current()
        n_labels = len(ds["labels"])
        n_series = len(ds["series"])

        info = [
            ("Строк",   f"{n_labels}", NEON_CYAN),
            ("Серий",   f"{n_series}", NEON_GREEN),
            ("Значений", f"{n_labels * n_series}", NEON_AMBER),
        ]

        for i, (label, value, color) in enumerate(info):
            iy = y + 55 + i * 40
            round_rect(self.canvas, panel_x + 20, iy,
                       panel_x + panel_w - 20, iy + 32, 8,
                       fill=BG_PANEL)
            self.canvas.create_text(panel_x + 30, iy + 16, anchor="w",
                                    text=label, fill=TEXT_DIM,
                                    font=FONT_MONO_S)
            self.canvas.create_text(panel_x + panel_w - 30, iy + 16,
                                    anchor="e",
                                    text=value, fill=color,
                                    font=("Consolas", 14, "bold"))

        # Слайдер строк
        ly = y + 195
        self.canvas.create_text(panel_x + 20, ly, anchor="w",
                                text="ПОКАЗАТЬ СТРОК (0 = все):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        max_show = n_labels
        current_show = self.state.max_rows if self.state.max_rows > 0 else n_labels

        self.canvas.create_text(panel_x + panel_w - 20, ly, anchor="e",
                                text=f"{current_show}",
                                fill=NEON_AMBER, font=FONT_MONO)

        bar_x0 = panel_x + 20
        bar_x1 = panel_x + panel_w - 20
        bar_y = ly + 25
        bar_h = 10

        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, 5,
                   fill="#0f141c", outline="")

        k = current_show / max(1, max_show)
        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x0 + (bar_x1 - bar_x0) * k, bar_y + bar_h/2,
                   5, fill=NEON_AMBER, outline="")
        cx_ = bar_x0 + (bar_x1 - bar_x0) * k
        self.canvas.create_oval(cx_ - 10, bar_y - 10,
                                cx_ + 10, bar_y + 10,
                                fill="#ffffff", outline=NEON_AMBER, width=2)

        self.slider_rect = (bar_x0, bar_y - 15, bar_x1, bar_y + 15, max_show)

        # Статистика
        sty = y + h - 260
        round_rect(self.canvas, panel_x + 20, sty,
                   panel_x + panel_w - 20, sty + 180, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, sty + 22,
                                text="СТАТИСТИКА СЕРИЙ",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        for j, s in enumerate(ds["series"][:3]):
            col = CHART_COLORS[j % len(CHART_COLORS)]
            sy = sty + 50 + j * 42

            vals = s["values"]
            if vals:
                avg = sum(vals) / len(vals)
                mx = max(vals)
                mn = min(vals)
            else:
                avg = mx = mn = 0

            self.canvas.create_text(panel_x + 35, sy, anchor="w",
                                    text=f"● {s['name'][:16]}",
                                    fill=col,
                                    font=("Segoe UI", 9, "bold"))
            self.canvas.create_text(panel_x + 35, sy + 18, anchor="w",
                                    text=f"ср={avg:.1f}  макс={mx:.1f}  мин={mn:.1f}",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 8))

        # Кнопки
        by = y + h - 60
        b_w = 145
        b_h = 44
        b_gap = 10

        self._draw_btn(panel_x + 20, by, b_w, b_h,
                       "🎲 ОБНОВИТЬ", NEON_PURP, "regen")
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "📷 PNG", NEON_CYAN, "save_png")

    def _draw_btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _redraw_all(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = self.W, self.H
        self.W, self.H = w, h

        self.btn_zones = {}
        self.slider_rect = None

        self._draw_bg(w, h)
        self._draw_header(w)
        self._draw_dataset_bar(w, 90)
        self._draw_type_bar(w, 165)

        chart_y = 235
        chart_h = h - chart_y - 20
        self._draw_chart_area(w, chart_y, chart_h)
        self._draw_panel(w, chart_y, chart_h)

    def _on_click(self, event):
        x, y = event.x, event.y

        # слайдер
        if self.slider_rect:
            x0, y0, x1, y1, mx = self.slider_rect
            if x0 - 10 <= x <= x1 + 10 and y0 <= y <= y1:
                self.drag_slider = True
                self._set_slider(x, x0, x1, mx)
                return

        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

    def _on_drag(self, event):
        if self.drag_slider and self.slider_rect:
            x0, y0, x1, y1, mx = self.slider_rect
            self._set_slider(event.x, x0, x1, mx)

    def _on_release(self, event):
        self.drag_slider = False

    def _set_slider(self, mouse_x, bar_x0, bar_x1, max_show):
        k = (mouse_x - bar_x0) / max(1, bar_x1 - bar_x0)
        k = max(0.0, min(1.0, k))
        n = int(round(k * max_show))
        if n >= max_show:
            n = 0
        self.state.max_rows = n

    def _do_action(self, key):
        if key.startswith("ds_"):
            self.state.select_dataset(int(key[3:]))
        elif key.startswith("type_"):
            self.state.chart_type = key[5:]
        elif key == "load_csv":
            self._load_csv()
        elif key == "regen":
            self.state.datasets = make_sample_data()
            self.state.dataset_keys = list(self.state.datasets.keys())
        elif key == "save_png":
            self._save_png()

    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=",")
                rows = list(reader)
            if len(rows) < 2:
                messagebox.showerror("Ошибка",
                    "CSV пуст или содержит только заголовки")
                return

            header = rows[0]
            labels = [r[0] for r in rows[1:]]
            series = []
            for j in range(1, min(len(header), 5)):
                name = header[j] if j < len(header) else f"Series {j}"
                values = []
                for r in rows[1:]:
                    try:
                        v = float(r[j].replace(",", ".")) if j < len(r) else 0
                    except Exception:
                        v = 0
                    values.append(v)
                series.append({"name": name, "values": values})

            if not series:
                messagebox.showerror("Ошибка",
                    "Не удалось прочитать колонки данных")
                return

            name = os.path.basename(path)[:30]
            self.state.add_custom_dataset(name, labels, series)
            messagebox.showinfo("Загружено",
                f"Датасет: {name}\nСтрок: {len(labels)}\nСерий: {len(series)}")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e))

    def _save_png(self):
        try:
            from PIL import ImageGrab
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png")],
                initialfile="chart.png")
            if not path:
                return
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            ImageGrab.grab().crop((x, y, x1, y1)).save(path)
            messagebox.showinfo("Сохранено", path)
        except ImportError:
            messagebox.showerror("Ошибка",
                "Установите Pillow: pip install pillow")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _animate(self):
        self.frame_count += 1
        now = time.time()
        if now - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = now

        self._redraw_all()
        self.root.after(60, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()