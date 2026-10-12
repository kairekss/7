"""
ОКФРС. Практика 7. Задание 11.
Графики с областями и тепловые карты.
Реальные данные: метео + транспорт.
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


def lerp3(c1, c2, c3, t):
    """Трёхцветная интерполяция (для тепловой карты)."""
    if t < 0.5:
        return lerp(c1, c2, t * 2)
    else:
        return lerp(c2, c3, (t - 0.5) * 2)


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


def catmull_rom(points, segments=20):
    """Сглаженная кривая."""
    if len(points) < 2:
        return points
    p = [points[0]] + list(points) + [points[-1]]
    result = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i-1], p[i], p[i+1], p[i+2]
        for j in range(segments):
            t = j / segments
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) +
                       (-p0[0] + p2[0]) * t +
                       (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) +
                       (-p0[1] + p2[1]) * t +
                       (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
            result.append((x, y))
    result.append(points[-1])
    return result


# ============================================================
# ДАННЫЕ
# ============================================================
def make_weather_data():
    """Погода: 24 часа × 7 дней — температура."""
    # 7 дней × 24 часа
    grid = []
    for d in range(7):
        row = []
        day_base = random.uniform(10, 20)
        for h in range(24):
            # суточное колебание
            daily = 6 * math.sin((h - 6) / 24 * 2 * math.pi - math.pi / 2)
            # дневной тренд
            trend = (d - 3) * 0.8
            row.append(day_base + daily + trend + random.uniform(-1.5, 1.5))
        grid.append(row)

    # график за 1 день (сегодня)
    today = grid[3]

    return {
        "grid": grid,
        "today": today,
        "days": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "hours": list(range(24)),
    }


def make_transport_data():
    """Транспорт: 7 дней × 24 часа — пассажиропоток."""
    grid = []
    for d in range(7):
        row = []
        is_weekend = d >= 5
        for h in range(24):
            # утренний и вечерний пик
            morning = 100 * math.exp(-((h - 8) ** 2) / 6)
            evening = 120 * math.exp(-((h - 18) ** 2) / 8)
            base = 20
            if is_weekend:
                morning *= 0.4
                evening *= 0.6
            value = base + morning + evening + random.uniform(-5, 5)
            row.append(max(0, value))
        grid.append(row)

    today = grid[3]

    return {
        "grid": grid,
        "today": today,
        "days": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "hours": list(range(24)),
    }


DATASETS = {
    "Погода (температура °C)": make_weather_data,
    "Транспорт (пассажиры)": make_transport_data,
}


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.data = None
        self.dataset_name = "Погода (температура °C)"
        self.reload()

        # режимы
        self.area_style = "smooth"   # smooth | line | bar
        self.heatmap_style = "interp" # interp | discrete

        # выбранная ячейка для подсказки
        self.hover_cell = None
        self.hover_point = None

    def reload(self):
        self.data = DATASETS[self.dataset_name]()

    def set_dataset(self, name):
        if name in DATASETS:
            self.dataset_name = name
            self.reload()

    def bounds(self):
        """Минимум и максимум по всей сетке."""
        flat = [v for row in self.data["grid"] for v in row]
        if not flat:
            return 0, 1
        return min(flat), max(flat)


# ============================================================
# ОТРИСОВКА — ГРАФИК С ОБЛАСТЯМИ
# ============================================================
def draw_area_chart(canvas, x, y, w, h, values, labels, style="smooth"):
    """График с областями (заливкой под кривой)."""
    if not values:
        return

    pad_l = 65
    pad_r = 30
    pad_t = 60
    pad_b = 50
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    min_v = min(values)
    max_v = max(values)
    span = max_v - min_v if max_v > min_v else 1

    # добавляем 10% сверху/снизу
    y_lo = min_v - span * 0.1
    y_hi = max_v + span * 0.1
    y_span = y_hi - y_lo

    # сетка + подписи по Y
    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = y_lo + k * y_span
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=("Consolas", 9))

    # оси
    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)

    # точки
    n = len(values)
    step = (gx1 - gx0) / max(1, n - 1)
    pts = []
    for i, v in enumerate(values):
        px = gx0 + i * step
        py = gy1 - (v - y_lo) / y_span * (gy1 - gy0)
        pts.append((px, py))

    if style == "smooth":
        smooth = catmull_rom(pts, segments=12)
        # заливка — полигон между кривой и низом
        area = [(gx0, gy1)] + smooth + [(gx1, gy1)]
        flat = []
        for (px, py) in area:
            flat.extend([px, py])

        # многослойная заливка (градиент)
        for k in range(4):
            t = k / 3
            col = lerp(BG_GRAPH, NEON_CYAN, 0.08 + t * 0.05)
            # сжимаем полигон по вертикали — сдвигаем верх вниз
            shifted = [(gx0, gy1)]
            for (px, py) in smooth:
                py2 = py + (gy1 - py) * t * 0.4
                shifted.append((px, py2))
            shifted.append((gx1, gy1))
            flat2 = []
            for (px, py) in shifted:
                flat2.extend([px, py])
            canvas.create_polygon(flat2, fill=col, outline="")

        # основная заливка
        canvas.create_polygon(flat, fill=lerp(NEON_CYAN, BG_GRAPH, 0.7),
                              outline="")
        # свечение
        flat_s = []
        for (px, py) in smooth:
            flat_s.extend([px, py])
        canvas.create_line(*flat_s,
                           fill=lerp(NEON_CYAN, BG_GRAPH, 0.5),
                           width=6, smooth=True)
        canvas.create_line(*flat_s, fill=NEON_CYAN, width=2, smooth=True)

        # точки
        for (px, py) in pts:
            canvas.create_oval(px - 4, py - 4, px + 4, py + 4,
                               fill=NEON_CYAN, outline="#ffffff", width=1)

    elif style == "line":
        flat = []
        for (px, py) in pts:
            flat.extend([px, py])
        canvas.create_line(*flat, fill=NEON_CYAN, width=2)
        for (px, py) in pts:
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3,
                               fill=NEON_CYAN, outline="")

    elif style == "bar":
        bar_w = step * 0.7
        for i, (px, py) in enumerate(pts):
            bx = px - bar_w / 2
            canvas.create_rectangle(bx, py, bx + bar_w, gy1,
                                     fill=lerp(NEON_CYAN, BG_GRAPH, 0.4),
                                     outline=NEON_CYAN, width=1)

    # подписи часов по X
    for i in range(0, n, 3):
        px = gx0 + i * step
        canvas.create_text(px, gy1 + 15, text=f"{i:02d}",
                           fill=TEXT_DIM, font=("Consolas", 8))

    # заголовок
    canvas.create_text(gx0 + 5, y + 20, anchor="w",
                       text="ТЕМПЕРАТУРА ЗА СЕГОДНЯ · 24 часа",
                       fill=NEON_CYAN, font=FONT_LABEL)


# ============================================================
# ОТРИСОВКА — ТЕПЛОВАЯ КАРТА
# ============================================================
def draw_heatmap(canvas, x, y, w, h, grid, row_labels, col_labels,
                 style="interp", hover_cell=None):
    """Тепловая карта: grid[row][col]."""
    if not grid or not grid[0]:
        return

    n_rows = len(grid)
    n_cols = len(grid[0])

    pad_l = 70
    pad_r = 30
    pad_t = 60
    pad_b = 45
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    cell_w = (gx1 - gx0) / n_cols
    cell_h = (gy1 - gy0) / n_rows

    # глобальные min / max
    flat = [v for row in grid for v in row]
    lo = min(flat)
    hi = max(flat)
    span = hi - lo if hi > lo else 1

    # === ячейки ===
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            cx0 = gx0 + j * cell_w
            cy0 = gy0 + i * cell_h
            cx1 = cx0 + cell_w
            cy1 = cy0 + cell_h

            # нормируем 0..1
            t = (v - lo) / span
            t = max(0.0, min(1.0, t))

            # цвет — от синего через зелёный к красному
            col = lerp3("#1a3a8a", "#39ff88", "#ff3b5c", t)

            if style == "discrete":
                # дискретные уровни
                level = int(t * 6) / 6
                col = lerp3("#1a3a8a", "#39ff88", "#ff3b5c", level)

            # рисуем ячейку
            canvas.create_rectangle(cx0, cy0, cx1 - 1, cy1 - 1,
                                     fill=col, outline="")

            # подсказка при hover
            if hover_cell == (i, j):
                canvas.create_rectangle(cx0, cy0, cx1 - 1, cy1 - 1,
                                         fill="", outline="#ffffff", width=2)

    # === сетка поверх ячеек (тонкая) ===
    for j in range(n_cols + 1):
        xx = gx0 + j * cell_w
        canvas.create_line(xx, gy0, xx, gy1,
                           fill="#0a0e18", width=1)
    for i in range(n_rows + 1):
        yy = gy0 + i * cell_h
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#0a0e18", width=1)

    # === подписи дней по Y ===
    for i, lbl in enumerate(row_labels):
        yy = gy0 + i * cell_h + cell_h / 2
        canvas.create_text(gx0 - 10, yy, anchor="e",
                           text=lbl, fill=TEXT_GLOW,
                           font=("Segoe UI", 10, "bold"))

    # === подписи часов по X (каждые 3) ===
    for j in range(0, n_cols, 3):
        xx = gx0 + j * cell_w + cell_w / 2
        canvas.create_text(xx, gy1 + 15, text=f"{j:02d}",
                           fill=TEXT_DIM, font=("Consolas", 8))

    # === цветовая шкала справа ===
    cb_x = gx1 + 12
    cb_y0 = gy0
    cb_y1 = gy1
    cb_w = 14

    # градиент
    n_steps = 60
    for k in range(n_steps):
        t = k / n_steps
        yy0 = cb_y1 - t * (cb_y1 - cb_y0)
        yy1 = cb_y1 - (k + 1) / n_steps * (cb_y1 - cb_y0)
        col = lerp3("#1a3a8a", "#39ff88", "#ff3b5c", t)
        canvas.create_rectangle(cb_x, yy1, cb_x + cb_w, yy0,
                                 fill=col, outline="")

    canvas.create_rectangle(cb_x, cb_y0, cb_x + cb_w, cb_y1,
                             fill="", outline=BORDER)

    # подписи значений
    for i in range(6):
        k = i / 5
        val = lo + k * span
        yy = cb_y1 - k * (cb_y1 - cb_y0)
        canvas.create_text(cb_x + cb_w + 6, yy, anchor="w",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=("Consolas", 9))

    # заголовок
    canvas.create_text(gx0 + 5, y + 20, anchor="w",
                       text="ТЕПЛОВАЯ КАРТА · 7 дней × 24 часа",
                       fill=NEON_PINK, font=FONT_LABEL)

    # подсказка при hover
    if hover_cell:
        i, j = hover_cell
        v = grid[i][j]
        # плашка подсказки
        tip_w = 200
        tip_h = 55
        mx, my = canvas.winfo_pointerxy()
        # не знаем точных координат — ставим рядом с ячейкой
        cx0 = gx0 + j * cell_w
        cy0 = gy0 + i * cell_h
        tx = min(cx0 + cell_w + 10, gx1 - tip_w - 10)
        ty = max(cy0 - tip_h - 5, gy0 + 5)
        round_rect(canvas, tx, ty, tx + tip_w, ty + tip_h, 6,
                   fill=BG_PANEL, outline=NEON_PINK, width=1)
        canvas.create_text(tx + 10, ty + 15, anchor="w",
                           text=f"{row_labels[i]} · {j:02d}:00",
                           fill=NEON_PINK,
                           font=("Segoe UI", 9, "bold"))
        canvas.create_text(tx + 10, ty + 38, anchor="w",
                           text=f"Значение: {v:.1f}",
                           fill=NEON_CYAN,
                           font=("Consolas", 13, "bold"))


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Heatmap & Area · Дашборд")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0

        self.state = AppState()
        self.btn_zones = {}

        # геометрия для hover
        self.area_rect = None
        self.heatmap_rect = None

        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

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
        self.canvas.create_text(60, 40, text="🌡",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="HEATMAP & AREA",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(330, 44,
                                text="· РЕАЛЬНЫЕ ДАННЫЕ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    def _draw_topbar(self, w, y):
        round_rect(self.canvas, 50, y, w - 50, y + 60, 12,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 30, anchor="w",
                                text="ДАННЫЕ:",
                                fill=TEXT_DIM, font=FONT_LABEL)

        # кнопки датасетов
        keys = list(DATASETS.keys())
        btn_w = 260
        btn_h = 40
        gap = 10
        start_x = 160

        for i, name in enumerate(keys):
            bx = start_x + i * (btn_w + gap)
            active = (self.state.dataset_name == name)
            self._draw_ds_btn(bx, y + 10, btn_w, btn_h, name, active)

        # кнопка обновить
        bx = w - 60 - 160
        round_rect(self.canvas, bx, y + 10, bx + 150, y + 50, 8,
                   fill=lerp(NEON_PURP, BG_DEEP, 0.8),
                   outline=NEON_PURP, width=1)
        self.canvas.create_text(bx + 75, y + 30,
                                text="🎲 ОБНОВИТЬ",
                                fill=NEON_PURP,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones["reload"] = (bx, y + 10, bx + 150, y + 50)

    def _draw_ds_btn(self, x, y, w, h, label, active):
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
                                    font=("Segoe UI", 10, "bold"))
        self.btn_zones[f"ds_{label}"] = (x, y, x + w, y + h)

    def _draw_controls_bar(self, w, y):
        round_rect(self.canvas, 50, y, w - 50, y + 55, 12,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 27, anchor="w",
                                text="СТИЛЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL)

        # стиль графика областей
        area_styles = [("smooth", "ГЛАДКИЙ", NEON_CYAN),
                       ("line",   "ЛИНИЯ",   NEON_GREEN),
                       ("bar",    "СТОЛБ",   NEON_AMBER)]
        bx = 130
        for key, label, col in area_styles:
            active = (self.state.area_style == key)
            self._draw_ctrl_btn(bx, y + 10, 120, 35, f"area_{key}",
                                 label, col, active)
            bx += 130

        # подпись
        self.canvas.create_text(540, y + 27, anchor="w",
                                text="ЯЧЕЙКИ:",
                                fill=TEXT_DIM, font=FONT_LABEL)

        # стиль карты
        hm_styles = [("interp", "ГРАДИЕНТ", NEON_PINK),
                     ("discrete", "УРОВНИ", NEON_PURP)]
        bx = 620
        for key, label, col in hm_styles:
            active = (self.state.heatmap_style == key)
            self._draw_ctrl_btn(bx, y + 10, 120, 35, f"hm_{key}",
                                 label, col, active)
            bx += 130

    def _draw_ctrl_btn(self, x, y, w, h, key, label, color, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.6),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Segoe UI", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _draw_main(self, w, y, h):
        # две колонки: слева график с областью, справа тепловая карта
        gap = 20
        col_w = (w - 100 - gap) / 2

        # левая — график с областями
        round_rect(self.canvas, 50, y, 50 + col_w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.area_rect = (50, y, 50 + col_w, y + h)

        # правая — тепловая карта
        round_rect(self.canvas, 50 + col_w + gap, y,
                   w - 50, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)
        self.heatmap_rect = (50 + col_w + gap, y, w - 50, y + h)

        # === данные ===
        data = self.state.data
        grid = data["grid"]
        today = data["today"]
        days = data["days"]

        # подписи часов для области
        hour_labels = [f"{h:02d}" for h in range(24)]

        # === график с областями ===
        draw_area_chart(self.canvas, 50, y, col_w, h, today, hour_labels,
                        style=self.state.area_style)

        # статистика под графиком
        info_y = y + h - 70
        avg = sum(today) / len(today) if today else 0
        mx = max(today) if today else 0
        mn = min(today) if today else 0
        txt = f"Средне: {avg:.1f}   Макс: {mx:.1f}   Мин: {mn:.1f}"
        self.canvas.create_text(50 + col_w / 2, info_y,
                                text=txt,
                                fill=NEON_AMBER,
                                font=("Consolas", 11, "bold"))

        # === тепловая карта ===
        draw_heatmap(self.canvas, 50 + col_w + gap, y, col_w, h,
                     grid, days, list(range(24)),
                     style=self.state.heatmap_style,
                     hover_cell=self.state.hover_cell)

    def _redraw_all(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = self.W, self.H
        self.W, self.H = w, h

        self.btn_zones = {}

        self._draw_bg(w, h)
        self._draw_header(w)
        self._draw_topbar(w, 90)
        self._draw_controls_bar(w, 165)

        main_y = 235
        main_h = h - main_y - 20
        self._draw_main(w, main_y, main_h)

    # ---------- СОБЫТИЯ ----------
    def _on_motion(self, event):
        # hover по тепловой карте
        if not self.heatmap_rect:
            return
        x0, y0, x1, y1 = self.heatmap_rect

        # сдвигаем на padding
        pad_l = 70
        pad_r = 30
        pad_t = 60
        pad_b = 45

        gx0 = x0 + pad_l
        gy0 = y0 + pad_t
        gx1 = x1 - pad_r
        gy1 = y1 - pad_b

        if not (gx0 <= event.x <= gx1 and gy0 <= event.y <= gy1):
            self.state.hover_cell = None
            return

        grid = self.state.data["grid"]
        n_rows = len(grid)
        n_cols = len(grid[0]) if n_rows else 0

        if n_rows == 0 or n_cols == 0:
            return

        cell_w = (gx1 - gx0) / n_cols
        cell_h = (gy1 - gy0) / n_rows

        col = int((event.x - gx0) / cell_w)
        row = int((event.y - gy0) / cell_h)

        col = max(0, min(n_cols - 1, col))
        row = max(0, min(n_rows - 1, row))

        self.state.hover_cell = (row, col)

    def _on_leave(self, event):
        self.state.hover_cell = None

    def _on_click(self, event):
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self._do_action(key)
                return

    def _do_action(self, key):
        if key.startswith("ds_"):
            name = key[3:]
            self.state.set_dataset(name)
        elif key.startswith("area_"):
            self.state.area_style = key[5:]
        elif key.startswith("hm_"):
            self.state.heatmap_style = key[3:]
        elif key == "reload":
            self.state.reload()

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