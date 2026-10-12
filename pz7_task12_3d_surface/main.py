"""
ОКФРС. Практика 7. Задание 12.
3D-поверхности через Chart-компонент:
sin(z) в комплексной плоскости, другие функции.
Премиум-стиль 2026.
"""
import tkinter as tk
import sys, os, math, random, time

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
NEON_LIME  = "#b4ff3d"
NEON_MINT  = "#3dffa0"

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


# ============================================================
# ФУНКЦИИ ДЛЯ ПОВЕРХНОСТЕЙ
# ============================================================
def f_sin_complex(u, v):
    """
    |sin(x + iy)| в комплексной плоскости.
    sin(x + iy) = sin(x)·cosh(y) + i·cos(x)·sinh(y)
    Модуль: sqrt(sin²(x)·cosh²(y) + cos²(x)·sinh²(y))
    """
    # ограничим чтобы не улетало
    x = u * math.pi
    y = v * 1.5
    try:
        val = math.sqrt(
            (math.sin(x) * math.cosh(y)) ** 2 +
            (math.cos(x) * math.sinh(y)) ** 2
        )
        # нормируем в 0..1
        return min(1.0, val / 3.0)
    except OverflowError:
        return 1.0


def f_sinc(u, v):
    """sin(r)/r — sinc функция."""
    r = math.sqrt(u * u + v * v) * 8 + 0.0001
    return (math.sin(r) / r) * 0.5 + 0.5


def f_ripple(u, v):
    """Волны — sin(u² + v²)."""
    r2 = u * u + v * v
    return math.sin(r2 * 8) * 0.4 + 0.5


def f_saddle(u, v):
    """Седло: u² - v²."""
    val = (u * u - v * v) * 3
    return val * 0.5 + 0.5


def f_gauss(u, v):
    """Гауссов холм."""
    r2 = u * u + v * v
    return math.exp(-r2 * 15)


def f_mexican(u, v):
    """Мексиканская шляпа."""
    r2 = (u * u + v * v) * 20
    return (1 - r2) * math.exp(-r2 / 2) * 0.5 + 0.5


def f_sin_cos(u, v):
    """sin(u) * cos(v)."""
    return (math.sin(u * 6) * math.cos(v * 6) + 1) / 2


def f_mix(u, v):
    """sin(x)+cos(y) с рябью."""
    x = u * 6
    y = v * 6
    val = (math.sin(x) + math.cos(y) + math.sin(math.sqrt(x*x+y*y) * 3) * 0.5) / 3
    return (val + 1) / 2


SURFACES = [
    ("sin(z) complex",  f_sin_complex),
    ("sinc(r)",         f_sinc),
    ("ripple",          f_ripple),
    ("saddle",          f_saddle),
    ("gaussian",        f_gauss),
    ("mexican hat",     f_mexican),
    ("sin·cos",         f_sin_cos),
    ("mix waves",       f_mix),
]


# ============================================================
# 3D-РЕНДЕР
# ============================================================
class Surface3D:
    """Поверхность z = f(u, v) в 3D."""

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # параметры
        self.n = 40             # разрешение сетки (n×n точек)
        self.rot_x = math.radians(-55)  # наклон
        self.rot_z = math.radians(30)   # поворот
        self.scale = 1.0
        self.height_scale = 1.0
        self.func = f_sin_complex
        self.name = "sin(z) complex"
        self.colormap = "plasma"  # plasma | viridis | fire | ocean

    def project(self, u, v, z):
        """
        Проекция 3D точки на экран.
        u, v ∈ [-1, 1], z ∈ [0, 1] — высота.
        """
        # масштаб
        u *= 1.4
        v *= 1.4
        z = (z - 0.5) * 1.2 * self.height_scale

        # поворот по Z (горизонтальный)
        cos_z = math.cos(self.rot_z)
        sin_z = math.sin(self.rot_z)
        x1 = u * cos_z - v * sin_z
        y1 = u * sin_z + v * cos_z
        z1 = z

        # наклон по X
        cos_x = math.cos(self.rot_x)
        sin_x = math.sin(self.rot_x)
        y2 = y1 * cos_x - z1 * sin_x
        z2 = y1 * sin_x + z1 * cos_x

        # перспектива
        fov = 3.0
        factor = fov / (fov + y2 * 0.3 + 1.5)

        # экран
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2
        screen_x = cx + x1 * self.w * 0.32 * factor
        screen_y = cy - (z2 * 0.7 + y2 * 0.4) * self.h * 0.32 * factor

        return screen_x, screen_y

    def colormap_color(self, t):
        """Палитра по параметру t ∈ [0, 1]."""
        t = max(0.0, min(1.0, t))
        if self.colormap == "plasma":
            # фиолетовый → розовый → оранжевый → жёлтый
            if t < 0.33:
                return lerp("#2d1b69", "#ff2d95", t / 0.33)
            elif t < 0.66:
                return lerp("#ff2d95", "#ff7a3d", (t - 0.33) / 0.33)
            else:
                return lerp("#ff7a3d", "#ffcc33", (t - 0.66) / 0.34)
        elif self.colormap == "viridis":
            if t < 0.33:
                return lerp("#440154", "#31688e", t / 0.33)
            elif t < 0.66:
                return lerp("#31688e", "#35b779", (t - 0.33) / 0.33)
            else:
                return lerp("#35b779", "#fde725", (t - 0.66) / 0.34)
        elif self.colormap == "fire":
            if t < 0.5:
                return lerp("#0a0000", "#8b0000", t / 0.5)
            elif t < 0.8:
                return lerp("#8b0000", "#ff6600", (t - 0.5) / 0.3)
            else:
                return lerp("#ff6600", "#ffff00", (t - 0.8) / 0.2)
        elif self.colormap == "ocean":
            if t < 0.5:
                return lerp("#000033", "#0066cc", t / 0.5)
            elif t < 0.8:
                return lerp("#0066cc", "#00ffcc", (t - 0.5) / 0.3)
            else:
                return lerp("#00ffcc", "#ffffff", (t - 0.8) / 0.2)
        # fallback — от синего к красному
        return lerp3(NEON_BLUE, NEON_GREEN, NEON_RED, t)

    def render(self, canvas):
        """Рисует поверхность: считает точки, сортирует по глубине, рисует сетку."""
        n = self.n

        # === вычисляем точки ===
        points = []
        values = []
        for i in range(n):
            row_pts = []
            row_vals = []
            for j in range(n):
                u = (j / (n - 1)) * 2 - 1
                v = (i / (n - 1)) * 2 - 1
                try:
                    z = self.func(u, v)
                    z = max(0.0, min(1.0, z))
                except Exception:
                    z = 0.0
                px, py = self.project(u, v, z)
                # глубина (для сортировки) — v + z
                depth = v * 1.0 + z * 0.1
                row_pts.append((px, py, depth))
                row_vals.append(z)
            points.append(row_pts)
            values.append(row_vals)

        # === рисуем ячейки (квады), сортируя по глубине ===
        cells = []
        for i in range(n - 1):
            for j in range(n - 1):
                # центр ячейки для глубины
                depth = (points[i][j][2] +
                          points[i+1][j][2] +
                          points[i][j+1][2] +
                          points[i+1][j+1][2]) / 4
                # среднее значение высоты
                avg_v = (values[i][j] + values[i+1][j] +
                          values[i][j+1] + values[i+1][j+1]) / 4
                # 4 угла
                p1 = points[i][j]
                p2 = points[i][j+1]
                p3 = points[i+1][j+1]
                p4 = points[i+1][j]
                cells.append((depth, p1, p2, p3, p4, avg_v))

        # сортировка: дальние (большая глубина) рисуются первыми
        cells.sort(key=lambda c: -c[0])

        # рисуем
        for (depth, p1, p2, p3, p4, avg_v) in cells:
            col = self.colormap_color(avg_v)
            # небольшая вариация яркости от глубины
            depth_shade = max(0.4, min(1.0, 1.0 + depth * 0.3))
            col = lerp(BG_GRAPH, col, depth_shade)

            flat = [p1[0], p1[1],
                    p2[0], p2[1],
                    p3[0], p3[1],
                    p4[0], p4[1]]

            # цвет полигона — интерполяция между углами для гладкости
            canvas.create_polygon(flat,
                                   fill=col,
                                   outline=lerp(col, BG_DEEP, 0.5),
                                   width=1,
                                   smooth=False)

    def draw_axes(self, canvas):
        """Рисует оси X, Y, Z."""
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2

        # ось X — красная
        p0 = self.project(-1, -1, 0)
        p1 = self.project(1, -1, 0)
        canvas.create_line(p0[0], p0[1], p1[0], p1[1],
                           fill=NEON_RED, width=2,
                           arrow=tk.LAST, arrowshape=(8, 10, 4))
        canvas.create_text(p1[0] + 15, p1[1], text="X",
                           fill=NEON_RED, font=FONT_LABEL)

        # ось Y — зелёная
        p0 = self.project(-1, -1, 0)
        p1 = self.project(-1, 1, 0)
        canvas.create_line(p0[0], p0[1], p1[0], p1[1],
                           fill=NEON_GREEN, width=2,
                           arrow=tk.LAST, arrowshape=(8, 10, 4))
        canvas.create_text(p1[0] - 15, p1[1] + 15, text="Y",
                           fill=NEON_GREEN, font=FONT_LABEL)

        # ось Z — синяя
        p0 = self.project(-1, -1, 0)
        p1 = self.project(-1, -1, 1)
        canvas.create_line(p0[0], p0[1], p1[0], p1[1],
                           fill=NEON_BLUE, width=2,
                           arrow=tk.LAST, arrowshape=(8, 10, 4))
        canvas.create_text(p1[0] - 15, p1[1] - 15, text="Z",
                           fill=NEON_BLUE, font=FONT_LABEL)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("3D Surface · sin(z) в комплексной плоскости")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0

        # 4 поверхности на экране
        self.surfaces = []
        self.current_view = 0   # для большой центральной

        # состояние
        self.auto_rotate = False
        self.rot_speed = 0.01

        self.btn_zones = {}
        self.drag_slider = None
        self.slider_rect = None

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

    # ---------- ФОН ----------
    def _draw_bg(self, w, h):
        for i in range(40):
            y0 = int(i * h / 40)
            y1 = int((i + 1) * h / 40)
            col = lerp(BG_DEEP, "#0a0e18", i / 40)
            self.canvas.create_rectangle(0, y0, w, y1, fill=col, outline="")

    # ---------- ЗАГОЛОВОК ----------
    def _draw_header(self, w):
        self.canvas.create_text(60, 40, text="∿",
                                fill=NEON_CYAN,
                                font=("Segoe UI", 30, "bold"))
        self.canvas.create_text(100, 40, text="3D SURFACE",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(280, 44,
                                text="· sin(z) в комплексной плоскости",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ПАНЕЛЬ ПОВЕРХНОСТЕЙ СЛЕВА ----------
    def _draw_panel(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text="▸ ПОВЕРХНОСТИ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # список кнопок
        btn_h = 44
        gap = 6
        start_y = y + 55

        for i, (name, func) in enumerate(SURFACES):
            by = start_y + i * (btn_h + gap)
            active = (self.current_view == i)
            self._draw_surface_btn(x + 15, by, w - 30, btn_h,
                                     i, name, active)

        # режим сетки
        ny = start_y + len(SURFACES) * (btn_h + gap) + 10

        self.canvas.create_text(x + 20, ny, anchor="w",
                                text="ЦВЕТОВАЯ СХЕМА:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        colormaps = [
            ("plasma",  "PLASMA",  NEON_PINK),
            ("viridis", "VIRIDIS", NEON_GREEN),
            ("fire",    "FIRE",    NEON_RED),
            ("ocean",   "OCEAN",   NEON_CYAN),
        ]

        cm_w = (w - 30 - 3 * 6) / 2
        cm_h = 34

        for i, (key, label, col) in enumerate(colormaps):
            row = i // 2
            col_idx = i % 2
            bx = x + 15 + col_idx * (cm_w + 6)
            by = ny + 20 + row * (cm_h + 6)
            active = (self.surfaces and self.surfaces[0].colormap == key)
            self._draw_cm_btn(bx, by, cm_w, cm_h, key, label, col, active)

        # слайдеры
        sy = ny + 20 + 2 * (cm_h + 6) + 15

        # высота
        self.canvas.create_text(x + 20, sy, anchor="w",
                                text="ВЫСОТА:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        h_val = self.surfaces[0].height_scale if self.surfaces else 1.0
        self.canvas.create_text(x + w - 20, sy, anchor="e",
                                text=f"{h_val:.2f}",
                                fill=NEON_AMBER, font=FONT_MONO)

        bx0 = x + 20
        bx1 = x + w - 20
        by = sy + 22
        round_rect(self.canvas, bx0, by - 5, bx1, by + 5, 5,
                   fill="#0f141c", outline="")
        k = h_val / 2.0
        round_rect(self.canvas, bx0, by - 5, bx0 + (bx1 - bx0) * k,
                   by + 5, 5, fill=NEON_AMBER, outline="")
        cx_ = bx0 + (bx1 - bx0) * k
        self.canvas.create_oval(cx_ - 9, by - 9, cx_ + 9, by + 9,
                                fill="#ffffff", outline=NEON_AMBER, width=2)
        self.slider_rect = (bx0, by - 12, bx1, by + 12, "height")

        # разрешение сетки
        sy2 = sy + 60
        self.canvas.create_text(x + 20, sy2, anchor="w",
                                text="ДЕТАЛИЗАЦИЯ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        n_val = self.surfaces[0].n if self.surfaces else 30
        self.canvas.create_text(x + w - 20, sy2, anchor="e",
                                text=f"{n_val}×{n_val}",
                                fill=NEON_CYAN, font=FONT_MONO)

        by2 = sy2 + 22
        round_rect(self.canvas, bx0, by2 - 5, bx1, by2 + 5, 5,
                   fill="#0f141c", outline="")
        k = (n_val - 15) / 55
        round_rect(self.canvas, bx0, by2 - 5, bx0 + (bx1 - bx0) * k,
                   by2 + 5, 5, fill=NEON_CYAN, outline="")
        cx_ = bx0 + (bx1 - bx0) * k
        self.canvas.create_oval(cx_ - 9, by2 - 9, cx_ + 9, by2 + 9,
                                fill="#ffffff", outline=NEON_CYAN, width=2)
        self.slider_rect2 = (bx0, by2 - 12, bx1, by2 + 12, "res")

        # кнопка авто-вращения
        ay = sy2 + 60
        active = self.auto_rotate
        col = NEON_GREEN if active else TEXT_DIM
        round_rect(self.canvas, x + 15, ay, x + w - 15, ay + 42, 8,
                   fill=lerp(col, BG_DEEP, 0.8),
                   outline=col, width=1)
        self.canvas.create_text(x + w / 2, ay + 21,
                                text="⏸ СТОП" if active else "▶ АВТО-ВРАЩЕНИЕ",
                                fill=col, font=("Segoe UI", 10, "bold"))
        self.btn_zones["auto"] = (x + 15, ay, x + w - 15, ay + 42)

    def _draw_surface_btn(self, x, y, w, h, idx, name, active):
        if active:
            for i in range(3, 0, -1):
                round_rect(self.canvas, x - i, y - i,
                           x + w + i, y + h + i, 8 + i,
                           outline=lerp(NEON_PURP, BG_DEEP, i / 4), width=1)
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(NEON_PURP, BG_DEEP, 0.6),
                       outline=NEON_PURP, width=2)
            self.canvas.create_text(x + 15, y + h / 2, anchor="w",
                                    text=f"{idx+1:02d}  {name}",
                                    fill=NEON_PURP,
                                    font=("Segoe UI", 10, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + 15, y + h / 2, anchor="w",
                                    text=f"{idx+1:02d}  {name}",
                                    fill=TEXT_DIM,
                                    font=("Segoe UI", 10, "bold"))
        self.btn_zones[f"surf_{idx}"] = (x, y, x + w, y + h)

    def _draw_cm_btn(self, x, y, w, h, key, label, col, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(col, BG_DEEP, 0.6),
                       outline=col, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=col,
                                    font=("Segoe UI", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"cm_{key}"] = (x, y, x + w, y + h)

    # ---------- ГЛАВНАЯ СЦЕНА 3D ----------
    def _draw_3d_view(self, x, y, w, h):
        round_rect(self.canvas, x, y, x + w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        # заголовок
        name = SURFACES[self.current_view][0]
        colormap = self.surfaces[0].colormap if self.surfaces else "plasma"
        self.canvas.create_text(x + 20, y + 25, anchor="w",
                                text=f"▸ z = {name}   ·   {colormap.upper()}",
                                fill=NEON_CYAN, font=FONT_LABEL)

        # подпись цветовой шкалы
        self.canvas.create_text(x + w - 20, y + 25, anchor="e",
                                text="ЛКМ — вращать · КОЛЕСО — масштаб",
                                fill=TEXT_DIM,
                                font=("Segoe UI", 9, "italic"))

        # фон для 3D
        gx = x + 15
        gy = y + 50
        gw = w - 30
        gh = h - 65

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        # создаём/обновляем поверхность
        self._create_surfaces(gx, gy, gw, gh)
        self.surfaces[0].render(self.canvas)
        self.surfaces[0].draw_axes(self.canvas)

        # цветовая шкала внизу
        self._draw_colorbar(gx + gw - 240, gy + gh - 30, 220, 16,
                             self.surfaces[0])

    def _create_surfaces(self, x, y, w, h):
        """Создаёт объекты Surface3D если их нет, или обновляет размеры."""
        if not self.surfaces:
            for _ in range(1):
                s = Surface3D(x, y, w, h)
                s.func = SURFACES[self.current_view][1]
                s.name = SURFACES[self.current_view][0]
                self.surfaces.append(s)
        else:
            for s in self.surfaces:
                s.x = x
                s.y = y
                s.w = w
                s.h = h

    def _draw_colorbar(self, x, y, w, h, surface):
        """Цветовая шкала под поверхностью."""
        n_steps = 60
        for k in range(n_steps):
            t = k / n_steps
            col = surface.colormap_color(t)
            xx0 = x + t * w
            xx1 = x + (k + 1) / n_steps * w
            self.canvas.create_rectangle(xx0, y, xx1, y + h,
                                          fill=col, outline="")

        # подписи
        self.canvas.create_text(x - 8, y + h / 2, anchor="e", text="0",
                                fill=TEXT_DIM, font=FONT_MONO_S)
        self.canvas.create_text(x + w + 8, y + h / 2, anchor="w", text="1",
                                fill=TEXT_DIM, font=FONT_MONO_S)
        self.canvas.create_text(x + w / 2, y + h + 14,
                                text="значение",
                                fill=TEXT_DIM,
                                font=("Segoe UI", 8, "italic"))

    # ---------- ПЕРЕРИСОВКА ----------
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

        # слева — панель управления
        panel_w = 300
        self._draw_panel(50, 90, panel_w, h - 110)

        # справа — 3D сцена
        scene_x = 50 + panel_w + 20
        scene_w = w - scene_x - 50
        self._draw_3d_view(scene_x, 90, scene_w, h - 110)

    # ---------- СОБЫТИЯ ----------
    def _on_click(self, event):
        x, y = event.x, event.y

        # слайдеры
        for rect in (self.slider_rect, getattr(self, "slider_rect2", None)):
            if rect:
                x0, y0, x1, y1, kind = rect
                if x0 - 10 <= x <= x1 + 10 and y0 <= y <= y1:
                    self.drag_slider = kind
                    self._set_slider(x, rect)
                    return

        # кнопки
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

        # вращение мышью
        if self.surfaces:
            s = self.surfaces[0]
            # проверяем, что клик в области 3D
            if s.x <= x <= s.x + s.w and s.y <= y <= s.y + s.h:
                self._drag_rot = (x, y, s.rot_z, s.rot_x)

    def _on_drag(self, event):
        if self.drag_slider:
            # какой слайдер
            if self.drag_slider == "height":
                self._set_slider(event.x, self.slider_rect)
            elif self.drag_slider == "res":
                self._set_slider(event.x, self.slider_rect2)
            return

        if hasattr(self, "_drag_rot") and self._drag_rot:
            x0, y0, rz0, rx0 = self._drag_rot
            dx = event.x - x0
            dy = event.y - y0
            if self.surfaces:
                s = self.surfaces[0]
                s.rot_z = rz0 + dx * 0.01
                s.rot_x = max(math.radians(-85),
                               min(math.radians(-10),
                                    rx0 + dy * 0.005))

    def _on_release(self, event):
        self.drag_slider = None
        self._drag_rot = None

    def _set_slider(self, mouse_x, rect):
        x0, y0, x1, y1, kind = rect
        k = (mouse_x - x0) / max(1, x1 - x0)
        k = max(0.0, min(1.0, k))
        if self.surfaces:
            s = self.surfaces[0]
            if kind == "height":
                s.height_scale = k * 2.0
            elif kind == "res":
                new_n = int(15 + k * 55)
                if abs(new_n - s.n) >= 2:
                    s.n = new_n

    def _do_action(self, key):
        if key.startswith("surf_"):
            idx = int(key[5:])
            self.current_view = idx
            if self.surfaces:
                self.surfaces[0].func = SURFACES[idx][1]
                self.surfaces[0].name = SURFACES[idx][0]
        elif key.startswith("cm_"):
            cm = key[3:]
            if self.surfaces:
                self.surfaces[0].colormap = cm
        elif key == "auto":
            self.auto_rotate = not self.auto_rotate

    # ---------- АНИМАЦИЯ ----------
    def _animate(self):
        self.frame_count += 1
        now = time.time()
        if now - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = now

        if self.auto_rotate and self.surfaces:
            self.surfaces[0].rot_z += self.rot_speed

        self._redraw_all()
        self.root.after(40, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()