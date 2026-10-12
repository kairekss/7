"""
ОКФРС. Практика 7. Задание 6.
Симуляция «Circuit Construction Kit: AC» —
конструктор электрических цепей с переменным током.
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
BORDER     = "#232a3d"

NEON_CYAN  = "#00f0ff"
NEON_GREEN = "#39ff88"
NEON_PINK  = "#ff3ea5"
NEON_PURP  = "#a066ff"
NEON_AMBER = "#ffb830"
NEON_RED   = "#ff4d5e"
NEON_BLUE  = "#4d8dff"

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
# ЭЛЕМЕНТЫ ЦЕПИ
# ============================================================
class CircuitElement:
    """Базовый элемент цепи."""
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind    # "source" | "resistor" | "capacitor" | "inductor" | "lamp" | "wire" | "ground"
        self.value = 1.0    # номинал (Ом, Ф, Гн, В)
        self.angle = 0      # для поворотов
        self.dragging = False
        self.selected = False

    def contains_point(self, mx, my, r=35):
        return math.hypot(mx - self.x, my - self.y) < r


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.elements = []
        self.wires = []       # список кортежей (elem1_idx, elem2_idx)

        # параметры источника
        self.source_voltage = 10.0     # амплитуда, В
        self.source_frequency = 1.0    # Гц
        self.source_type = "AC"         # "AC" | "DC"
        self.source_phase = 0.0

        # время моделирования
        self.time = 0.0
        self.paused = False

        # показ
        self.show_current_flow = True
        self.show_vectors = False

        self.pulse_t = 0.0

        # сцена по умолчанию
        self.load_default_circuit()

    def load_default_circuit(self):
        """Базовая RC-цепь: источник → резистор → конденсатор."""
        self.elements = []
        # источник в левом нижнем углу
        src = CircuitElement(0.2, 0.7, "source")
        src.value = self.source_voltage
        self.elements.append(src)

        # резистор сверху
        r = CircuitElement(0.5, 0.3, "resistor")
        r.value = 100
        self.elements.append(r)

        # конденсатор справа
        c = CircuitElement(0.8, 0.7, "capacitor")
        c.value = 0.01
        self.elements.append(c)

        # провода — соединяем попарно
        self.wires = [
            (0, 1),  # source → resistor
            (1, 2),  # resistor → capacitor
            (2, 0),  # capacitor → source (замыкание)
        ]

    def add_element(self, kind, x, y):
        el = CircuitElement(x, y, kind)
        if kind == "source":
            el.value = self.source_voltage
        elif kind == "resistor":
            el.value = 100
        elif kind == "capacitor":
            el.value = 0.01
        elif kind == "inductor":
            el.value = 0.1
        elif kind == "lamp":
            el.value = 50
        elif kind == "ground":
            pass
        self.elements.append(el)
        return el

    def remove_element(self, el):
        if el in self.elements:
            idx = self.elements.index(el)
            self.elements.remove(el)
            # удаляем связанные провода
            self.wires = [(a, b) for (a, b) in self.wires
                           if a != idx and b != idx]
            # сдвигаем индексы
            new_wires = []
            for a, b in self.wires:
                na = a if a < idx else a - 1
                nb = b if b < idx else b - 1
                new_wires.append((na, nb))
            self.wires = new_wires

    def clear(self):
        self.elements = []
        self.wires = []

    def add_wire(self, i, j):
        """Добавляет провод между двумя элементами."""
        if i == j: return
        if i >= len(self.elements) or j >= len(self.elements): return
        # избегаем дубликатов
        for (a, b) in self.wires:
            if (a == i and b == j) or (a == j and b == i):
                return
        self.wires.append((i, j))

    def source_current_at_time(self):
        """Мгновенное значение напряжения источника."""
        if self.source_type == "DC":
            return self.source_voltage
        return self.source_voltage * math.sin(
            2 * math.pi * self.source_frequency * self.time + self.source_phase)

    def tick(self, dt):
        self.pulse_t += dt
        if not self.paused:
            self.time += dt

    def stats(self):
        # мгновенное напряжение источника
        u = self.source_current_at_time()
        # частота, период
        freq = self.source_frequency
        period = 1.0 / freq if freq > 0 else 0
        return {
            "voltage": u,
            "freq": freq,
            "period": period,
            "elements": len(self.elements),
            "wires": len(self.wires),
        }


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ AC Circuit Kit · Конструктор переменного тока")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0
        self.last_time = time.time()

        self.state = AppState()
        self.btn_zones = {}
        self.slider_zones = {}
        self.drag_slider = None
        self.dragging_object = None
        self.selected_for_wire = None    # для соединения проводами

        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)

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
        self.canvas.create_text(60, 40, text="⚡",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="AC CIRCUIT KIT",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(340, 44,
                                text="· КОНСТРУКТОР ЭЛЕКТРИЧЕСКИХ ЦЕПЕЙ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- СЦЕНА ----------
    def _draw_scene(self, x, y, w, h):
        panel_w = 400
        scene_w = w - 100 - panel_w - 20

        round_rect(self.canvas, x, y, x + scene_w, y + h, 14,
                   fill=BG_GRAPH, outline=BORDER, width=1)

        self.canvas.create_text(x + scene_w / 2, y + 20,
                                text="ЛКМ тащить · ПКМ удалить · двойной клик — соединить проводом",
                                fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        gx0 = x + 10
        gy0 = y + 40
        gx1 = x + scene_w - 10
        gy1 = y + h - 10

        gw = gx1 - gx0
        gh = gy1 - gy0

        self.scene_rect = (gx0, gy0, gw, gh)

        # сетка
        step = 40
        for i in range(int(gx0), int(gx1), step):
            self.canvas.create_line(i, gy0, i, gy1,
                                    fill="#0d1520", width=1)
        for j in range(int(gy0), int(gy1), step):
            self.canvas.create_line(gx0, j, gx1, j,
                                    fill="#0d1520", width=1)

        def to_px(el):
            return (gx0 + el.x * gw, gy0 + el.y * gh)

        # === провода ===
        for (a, b) in self.state.wires:
            if a >= len(self.state.elements) or b >= len(self.state.elements):
                continue
            e1 = self.state.elements[a]
            e2 = self.state.elements[b]
            p1 = to_px(e1)
            p2 = to_px(e2)

            # цвет провода по току (упрощённо — по полярности)
            u = self.state.source_current_at_time()
            if self.state.show_current_flow:
                # толщина и цвет зависят от |u|
                mag = min(1.0, abs(u) / max(0.1, self.state.source_voltage))
                col = lerp("#3a3d48", NEON_AMBER, mag)
                width = 3 + int(mag * 3)
            else:
                col = "#3a3d48"
                width = 4

            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=col, width=width,
                                    capstyle="round")

        # === элементы ===
        for el in self.state.elements:
            px, py = to_px(el)
            self._draw_element(el, px, py)

        # индикатор «выбран для соединения»
        if self.selected_for_wire is not None and \
           self.selected_for_wire < len(self.state.elements):
            el = self.state.elements[self.selected_for_wire]
            px, py = to_px(el)
            self.canvas.create_oval(px - 42, py - 42,
                                    px + 42, py + 42,
                                    outline="#ffffff", width=2,
                                    dash=(4, 3))

    def _draw_element(self, el, px, py):
        # обводка выделения
        if el.dragging or el.selected:
            self.canvas.create_oval(px - 40, py - 40, px + 40, py + 40,
                                    outline="#ffffff", width=1,
                                    dash=(3, 3))

        if el.kind == "source":
            self._draw_source(el, px, py)
        elif el.kind == "resistor":
            self._draw_resistor(el, px, py)
        elif el.kind == "capacitor":
            self._draw_capacitor(el, px, py)
        elif el.kind == "inductor":
            self._draw_inductor(el, px, py)
        elif el.kind == "lamp":
            self._draw_lamp(el, px, py)
        elif el.kind == "ground":
            self._draw_ground(el, px, py)

    def _draw_source(self, el, px, py):
        """Источник напряжения (AC/DC)."""
        r = 30
        # тень
        self.canvas.create_oval(px - r + 3, py - r + 5,
                                px + r + 3, py + r + 5,
                                fill="#000000", outline="")
        # тело
        self.canvas.create_oval(px - r, py - r, px + r, py + r,
                                fill="#1a1c22",
                                outline=NEON_AMBER, width=3)

        # символ — синусоида или =
        if self.state.source_type == "AC":
            pts = []
            for i in range(40):
                t = i / 39
                x = px - 18 + 36 * t
                y = py - 8 * math.sin(2 * math.pi * t)
                pts.extend([x, y])
            self.canvas.create_line(*pts, fill=NEON_AMBER, width=2,
                                    smooth=True)
        else:
            self.canvas.create_line(px - 15, py - 6, px + 15, py - 6,
                                    fill=NEON_AMBER, width=2)
            self.canvas.create_line(px - 15, py + 6, px + 15, py + 6,
                                    fill=NEON_AMBER, width=2)

        # значение
        u = self.state.source_current_at_time()
        col = NEON_GREEN if u > 0 else (NEON_RED if u < 0 else TEXT_DIM)
        self.canvas.create_text(px, py + r + 18,
                                text=f"{u:+.2f} В",
                                fill=col,
                                font=("Consolas", 10, "bold"))

        # подпись
        self.canvas.create_text(px, py - r - 12,
                                text=f"{self.state.source_type} "
                                     f"{self.state.source_voltage:.1f}В",
                                fill=NEON_AMBER,
                                font=("Consolas", 8))

    def _draw_resistor(self, el, px, py):
        r = 28
        # тень
        self.canvas.create_rectangle(px - r + 3, py - 12 + 5,
                                      px + r + 3, py + 12 + 5,
                                      fill="#000000", outline="")
        # тело
        self.canvas.create_rectangle(px - r, py - 12, px + r, py + 12,
                                      fill="#2a2d38", outline=NEON_GREEN,
                                      width=2)
        # зигзаг
        pts = []
        n = 6
        for i in range(n + 1):
            t = i / n
            x = px - r + 2 * r * t
            y = py + (8 if i % 2 == 0 else -8)
            pts.extend([x, y])
        self.canvas.create_line(*pts, fill=NEON_GREEN, width=2)

        self.canvas.create_text(px, py + 28,
                                text=f"{el.value:.0f} Ом",
                                fill=NEON_GREEN,
                                font=("Consolas", 9, "bold"))

    def _draw_capacitor(self, el, px, py):
        r = 28
        # две пластины
        self.canvas.create_line(px - 10, py - 20, px - 10, py + 20,
                                fill=NEON_CYAN, width=3)
        self.canvas.create_line(px + 10, py - 20, px + 10, py + 20,
                                fill=NEON_CYAN, width=3)
        # выводы
        self.canvas.create_line(px - r, py, px - 10, py,
                                fill=NEON_CYAN, width=2)
        self.canvas.create_line(px + 10, py, px + r, py,
                                fill=NEON_CYAN, width=2)

        self.canvas.create_text(px, py + 32,
                                text=f"{el.value*1000:.0f} мФ",
                                fill=NEON_CYAN,
                                font=("Consolas", 9, "bold"))

    def _draw_inductor(self, el, px, py):
        r = 28
        # выводы
        self.canvas.create_line(px - r, py, px - 20, py,
                                fill=NEON_PURP, width=2)
        self.canvas.create_line(px + 20, py, px + r, py,
                                fill=NEON_PURP, width=2)
        # катушка — 3 дуги
        for i in range(3):
            x0 = px - 20 + i * 13
            self.canvas.create_arc(x0, py - 10, x0 + 13, py + 10,
                                    start=0, extent=180,
                                    style="arc",
                                    outline=NEON_PURP, width=3)

        self.canvas.create_text(px, py + 28,
                                text=f"{el.value*1000:.0f} мГн",
                                fill=NEON_PURP,
                                font=("Consolas", 9, "bold"))

    def _draw_lamp(self, el, px, py):
        r = 24
        # яркость лампы зависит от тока
        u = abs(self.state.source_current_at_time()) / \
            max(0.1, self.state.source_voltage)
        bright = min(1.0, u)
        # свечение
        for i in range(6, 0, -1):
            rr = r + i * 3
            col = lerp(BG_GRAPH, NEON_AMBER, bright * (1 - i / 8))
            self.canvas.create_oval(px - rr, py - rr, px + rr, py + rr,
                                    fill="", outline=col, width=1)
        # тело
        self.canvas.create_oval(px - r, py - r, px + r, py + r,
                                fill=lerp("#1a1c22", NEON_AMBER, bright * 0.5),
                                outline=NEON_AMBER, width=2)
        # крест
        self.canvas.create_line(px - 14, py - 14, px + 14, py + 14,
                                fill=NEON_AMBER, width=2)
        self.canvas.create_line(px - 14, py + 14, px + 14, py - 14,
                                fill=NEON_AMBER, width=2)
        # выводы
        self.canvas.create_line(px - r, py, px - r - 8, py,
                                fill=NEON_AMBER, width=2)
        self.canvas.create_line(px + r, py, px + r + 8, py,
                                fill=NEON_AMBER, width=2)

    def _draw_ground(self, el, px, py):
        # три линии уменьшающейся длины
        for i, w in enumerate([20, 14, 8]):
            y = py + i * 6
            self.canvas.create_line(px - w, y, px + w, y,
                                    fill=NEON_AMBER, width=2)
        self.canvas.create_line(px, py - 10, px, py,
                                fill=NEON_AMBER, width=2)

    # ---------- ПАНЕЛЬ ----------
    def _draw_panel(self, w, y, h):
        panel_w = 400
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ ЭЛЕМЕНТЫ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # === Палитра элементов ===
        tools = [
            ("source",    "ИСТОЧНИК",  NEON_AMBER),
            ("resistor",  "РЕЗИСТОР",  NEON_GREEN),
            ("capacitor", "КОНДЕНСАТОР", NEON_CYAN),
            ("inductor",  "КАТУШКА",   NEON_PURP),
            ("lamp",      "ЛАМПА",     NEON_RED),
            ("ground",    "ЗЕМЛЯ",     NEON_BLUE),
        ]
        t_w = 120
        t_h = 48
        t_gap = 8
        cols = 3
        start_x = panel_x + 20

        for i, (key, label, color) in enumerate(tools):
            row = i // cols
            col = i % cols
            bx = start_x + col * (t_w + t_gap)
            by = y + 50 + row * (t_h + t_gap)
            self._draw_tool_btn(bx, by, t_w, t_h, key, label, color)

        # === Настройки источника ===
        sy = y + 180

        self.canvas.create_text(panel_x + 20, sy, anchor="w",
                                text="ИСТОЧНИК:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        # AC/DC
        st = self.state.source_type
        for i, (name, color) in enumerate([("DC", NEON_BLUE), ("AC", NEON_AMBER)]):
            bx = panel_x + 100 + i * 80
            active = (st == name)
            self._draw_mini_btn(bx, sy - 14, 70, 28, name, color, active,
                                 f"src_type_{name}")

        # === Амплитуда ===
        ay = y + 210
        self.canvas.create_text(panel_x + 20, ay, anchor="w",
                                text="АМПЛИТУДА (В):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w - 20, ay, anchor="e",
                                text=f"{self.state.source_voltage:.1f}",
                                fill=NEON_AMBER, font=FONT_MONO)
        self._draw_slider(panel_x + 20, ay + 25, panel_w - 40,
                           (self.state.source_voltage - 1) / 29,
                           "source_v", 1, 30, NEON_AMBER)

        # === Частота ===
        fy = y + 280
        self.canvas.create_text(panel_x + 20, fy, anchor="w",
                                text="ЧАСТОТА (Гц):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w - 20, fy, anchor="e",
                                text=f"{self.state.source_frequency:.2f}",
                                fill=NEON_CYAN, font=FONT_MONO)
        self._draw_slider(panel_x + 20, fy + 25, panel_w - 40,
                           (self.state.source_frequency - 0.1) / 4.9,
                           "source_f", 0.1, 5.0, NEON_CYAN)

        # === Показ ===
        vy = y + 350
        self.canvas.create_text(panel_x + 20, vy, anchor="w",
                                text="ПОКАЗ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        toggles = [
            ("current_flow", "ТОК В ПРОВОДАХ", NEON_AMBER,
             self.state.show_current_flow),
        ]
        for i, (key, label, color, active) in enumerate(toggles):
            bx = panel_x + 20 + i * 190
            self._draw_toggle_btn(bx, vy + 20, 180, 34, key, label,
                                    color, active)

        # === Статистика ===
        sty = y + 410
        stats = self.state.stats()

        round_rect(self.canvas, panel_x + 20, sty,
                   panel_x + panel_w - 20, sty + 160, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, sty + 22,
                                text="СОСТОЯНИЕ ЦЕПИ",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        lines = [
            ("Мгновенное U",  f"{stats['voltage']:+.2f} В",       NEON_GREEN),
            ("Частота",       f"{stats['freq']:.2f} Гц",           NEON_CYAN),
            ("Период",        f"{stats['period']:.3f} с",          NEON_AMBER),
            ("Элементов",     f"{stats['elements']}",              NEON_PURP),
            ("Соединений",    f"{stats['wires']}",                 NEON_PINK),
        ]

        for i, (label, value, color) in enumerate(lines):
            ly = sty + 50 + i * 22
            self.canvas.create_text(panel_x + 35, ly, anchor="w",
                                    text=label, fill=TEXT_DIM,
                                    font=FONT_MONO_S)
            self.canvas.create_text(panel_x + panel_w - 35, ly, anchor="e",
                                    text=value, fill=color,
                                    font=FONT_MONO_S)

        # === Кнопки ===
        by = y + h - 60
        b_w = 175
        b_h = 44
        b_gap = 10

        self._draw_btn(panel_x + 20, by, b_w, b_h,
                       "⏸ ПАУЗА" if not self.state.paused else "▶ СТАРТ",
                       NEON_AMBER, "pause",
                       active=self.state.paused)
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "🗑 ОЧИСТИТЬ", NEON_RED, "clear")

    def _draw_slider(self, x, y, w, k, key, vmin, vmax, color):
        bar_x0 = x
        bar_x1 = x + w
        bar_y = y
        bar_h = 10
        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, 5,
                   fill="#0f141c", outline="")
        k = max(0.0, min(1.0, k))
        if k > 0.005:
            round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                       bar_x0 + w * k, bar_y + bar_h/2,
                       5, fill=color, outline="")
        cx_ = bar_x0 + w * k
        self.canvas.create_oval(cx_ - 10, bar_y - 10,
                                cx_ + 10, bar_y + 10,
                                fill="#ffffff", outline=color, width=2)
        self.slider_zones[key] = (bar_x0 - 10, bar_y - 15,
                                    bar_x1 + 10, bar_y + 15,
                                    vmin, vmax)

    def _draw_tool_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.82),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"tool_{key}"] = (x, y, x + w, y + h)

    def _draw_mini_btn(self, x, y, w, h, label, color, active, key):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.5),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Consolas", 12, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Consolas", 12, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _draw_toggle_btn(self, x, y, w, h, key, label, color, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(color, BG_DEEP, 0.6),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=f"✓ {label}", fill=color,
                                    font=("Segoe UI", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"toggle_{key}"] = (x, y, x + w, y + h)

    def _draw_btn(self, x, y, w, h, text, color, key, active=False):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(color, BG_DEEP, 0.5),
                       outline=color, width=2)
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(color, BG_DEEP, 0.8),
                       outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    # ---------- ПЕРЕРИСОВКА ----------
    def _redraw_all(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = self.W, self.H
        self.W, self.H = w, h

        self.btn_zones = {}
        self.slider_zones = {}

        self._draw_bg(w, h)
        self._draw_header(w)
        self._draw_scene(50, 90, w, h - 110)
        self._draw_panel(w, 90, h - 110)

    # ---------- СОБЫТИЯ ----------
    def _on_click(self, event):
        x, y = event.x, event.y

        # слайдеры
        for key, (x0, y0, x1, y1, vmin, vmax) in self.slider_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.drag_slider = key
                self._set_slider_from_mouse(key, x)
                return

        # кнопки
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

        # клик по элементу сцены — с ВОЗВРАТОМ
        if self._try_start_drag(x, y):
            return

    def _try_start_drag(self, mx, my):
        """Пытается найти элемент в точке и начать drag."""
        if not hasattr(self, "scene_rect"):
            return False
        gx0, gy0, gw, gh = self.scene_rect

        # ищем под курсором (сверху вниз — последний элемент самый верхний)
        for el in reversed(self.state.elements):
            px = gx0 + el.x * gw
            py = gy0 + el.y * gh
            if math.hypot(mx - px, my - py) < 42:
                # двойной клик — соединение
                now = time.time()
                if (hasattr(self, "_last_click_time")
                        and hasattr(self, "_last_click_el")
                        and self._last_click_el is el
                        and now - self._last_click_time < 0.4):
                    idx = self.state.elements.index(el)
                    if self.selected_for_wire is None:
                        self.selected_for_wire = idx
                    else:
                        self.state.add_wire(self.selected_for_wire, idx)
                        self.selected_for_wire = None
                    self._last_click_time = 0
                    return True

                # начало перетаскивания
                el.dragging = True
                self.dragging_object = el
                self._last_click_time = now
                self._last_click_el = el
                return True
        return False

    def _click_scene(self, mx, my, event):
        if not hasattr(self, "scene_rect"):
            return
        gx0, gy0, gw, gh = self.scene_rect

        # ищем элемент
        for el in self.state.elements:
            px = gx0 + el.x * gw
            py = gy0 + el.y * gh
            if el.contains_point(mx, my, 38):
                # двойной клик — соединить проводом
                # определяем по времени
                now = time.time()
                if hasattr(self, "_last_click_time") and \
                   hasattr(self, "_last_click_el") and \
                   self._last_click_el is el and \
                   now - self._last_click_time < 0.4:
                    # соединяем
                    idx = self.state.elements.index(el)
                    if self.selected_for_wire is None:
                        self.selected_for_wire = idx
                    else:
                        self.state.add_wire(self.selected_for_wire, idx)
                        self.selected_for_wire = None
                    self._last_click_time = 0
                    return
                # одиночный клик — начало drag
                el.dragging = True
                self.dragging_object = el
                self._last_click_time = now
                self._last_click_el = el
                return

    def _on_drag(self, event):
        if self.drag_slider:
            self._set_slider_from_mouse(self.drag_slider, event.x)
            return

        if self.dragging_object is None:
            return
        if not hasattr(self, "scene_rect"):
            return

        gx0, gy0, gw, gh = self.scene_rect
        nx = (event.x - gx0) / gw
        ny = (event.y - gy0) / gh
        nx = max(0.02, min(0.98, nx))
        ny = max(0.02, min(0.98, ny))
        self.dragging_object.x = nx
        self.dragging_object.y = ny

    def _on_release(self, event):
        self.drag_slider = None
        if self.dragging_object is not None:
            self.dragging_object.dragging = False
            self.dragging_object = None
    def _on_right_click(self, event):
        if not hasattr(self, "scene_rect"):
            return
        gx0, gy0, gw, gh = self.scene_rect
        mx, my = event.x, event.y
        for el in list(self.state.elements):
            px = gx0 + el.x * gw
            py = gy0 + el.y * gh
            if el.contains_point(mx, my, 38):
                self.state.remove_element(el)
                if self.selected_for_wire is not None:
                    self.selected_for_wire = None
                return

    def _set_slider_from_mouse(self, key, mouse_x):
        if key not in self.slider_zones:
            return
        x0, y0, x1, y1, vmin, vmax = self.slider_zones[key]
        bar_x0 = x0 + 10
        bar_x1 = x1 - 10
        if bar_x1 <= bar_x0:
            return
        k = (mouse_x - bar_x0) / (bar_x1 - bar_x0)
        k = max(0.0, min(1.0, k))
        val = vmin + k * (vmax - vmin)
        if key == "source_v":
            self.state.source_voltage = val
        elif key == "source_f":
            self.state.source_frequency = val

    def _do_action(self, key):
        if key == "pause":
            self.state.paused = not self.state.paused
        elif key == "clear":
            self.state.clear()
            self.selected_for_wire = None
        elif key == "src_type_DC":
            self.state.source_type = "DC"
        elif key == "src_type_AC":
            self.state.source_type = "AC"
        elif key.startswith("toggle_"):
            name = key[7:]
            if name == "current_flow":
                self.state.show_current_flow = not self.state.show_current_flow
        elif key.startswith("tool_"):
            kind = key[5:]
            # добавляем в центр сцены
            if hasattr(self, "scene_rect"):
                # случайная позиция чтобы не накладывались
                ex = random.uniform(0.25, 0.75)
                ey = random.uniform(0.25, 0.75)
                self.state.add_element(kind, ex, ey)

    # ---------- АНИМАЦИЯ ----------
    def _animate(self):
        self.frame_count += 1
        now = time.time()
        if now - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = now

        dt = min(0.05, now - self.last_time)
        self.last_time = now

        self.state.tick(dt)

        self._redraw_all()
        self.root.after(35, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()