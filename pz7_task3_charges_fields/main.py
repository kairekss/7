"""
ОКФРС. Практика 7. Задание 3.
Повторение симуляции Charges and Fields (PhET):
интерактивная модель электрических зарядов и поля.
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
# МОДЕЛЬ ЗАРЯДОВ
# ============================================================
class Charge:
    """Точечный заряд."""
    def __init__(self, x, y, q):
        self.x = x         # в пикселях канваса
        self.y = y
        self.q = q         # заряд: +1, -1, +2 и т.д. (в ед. e)
        self.dragging = False

    def potential_at(self, px, py, k=1.0):
        """Потенциал в точке от этого заряда."""
        r = math.hypot(px - self.x, py - self.y)
        r = max(r, 8)   # ограничение снизу чтобы не делить на 0
        return k * self.q / r

    def field_at(self, px, py, k=1.0):
        """Вектор поля в точке."""
        dx = px - self.x
        dy = py - self.y
        r2 = dx * dx + dy * dy
        r = math.sqrt(r2)
        if r < 8:
            r = 8
            r2 = 64
        # E = k*q / r², направление — от заряда
        e = k * self.q / r2
        return (e * dx / r, e * dy / r)


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        # заряды в относительных координатах (0..1)
        self.charges = []
        self.grid_size = (800, 600)   # будет переопределено

        # показ
        self.show_field_lines = True
        self.show_vectors = True
        self.show_equipotential = False
        self.show_potential = True
        self.show_grid = True

        self.selected_charge = None
        self.hover_pos = None

        self.pulse_t = 0.0

        # начальные заряды (только после установки размеров)
        self._init_charges()

    def _init_charges(self):
        # + заряд слева, - заряд справа
        self.charges = [
            Charge(0.35, 0.5, +1),
            Charge(0.65, 0.5, -1),
        ]

    def tick(self, dt):
        self.pulse_t += dt

    def set_grid(self, w, h):
        self.grid_size = (w, h)

    def add_charge(self, x, y, q=1):
        # координаты в 0..1
        self.charges.append(Charge(x, y, q))

    def remove_charge(self, charge):
        if charge in self.charges:
            self.charges.remove(charge)

    def clear(self):
        self.charges = []

    def preset(self, name):
        self.charges = []
        if name == "dipole":
            self.charges = [Charge(0.35, 0.5, +1),
                             Charge(0.65, 0.5, -1)]
        elif name == "single_plus":
            self.charges = [Charge(0.5, 0.5, +1)]
        elif name == "single_minus":
            self.charges = [Charge(0.5, 0.5, -1)]
        elif name == "two_plus":
            self.charges = [Charge(0.35, 0.5, +1),
                             Charge(0.65, 0.5, +1)]
        elif name == "quadrupole":
            self.charges = [Charge(0.4, 0.35, +1),
                             Charge(0.6, 0.35, -1),
                             Charge(0.4, 0.65, -1),
                             Charge(0.6, 0.65, +1)]
        elif name == "capacitor":
            # ряд плюсов и ряд минусов
            for i in range(4):
                x = 0.3 + i * 0.13
                self.charges.append(Charge(x, 0.35, +1))
                self.charges.append(Charge(x, 0.65, -1))

    def total_charge(self):
        return sum(c.q for c in self.charges)

    def potential_energy(self):
        """Энергия системы зарядов (сумма по парам)."""
        e = 0.0
        n = len(self.charges)
        for i in range(n):
            for j in range(i+1, n):
                c1 = self.charges[i]
                c2 = self.charges[j]
                r = max(math.hypot(c1.x - c2.x, c1.y - c2.y) * 500, 8)
                e += c1.q * c2.q / r
        return e


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Charges & Fields · PhET Simulation")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0

        self.state = AppState()
        self.btn_zones = {}
        self.slider_zones = {}
        self.drag_slider = None

        self.dragging_charge = None

        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

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
        self.canvas.create_text(100, 40, text="CHARGES & FIELDS",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(370, 44,
                                text="· ЭЛЕКТРИЧЕСКИЕ ЗАРЯДЫ И ПОЛЯ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ОСНОВНАЯ СЦЕНА ----------
    def _draw_scene(self, x, y, w, h):
        panel_w = 400
        scene_w = w - 100 - panel_w - 20

        round_rect(self.canvas, x, y, x + scene_w, y + h, 14,
                   fill=BG_GRAPH, outline=BORDER, width=1)

        # подсказка
        self.canvas.create_text(x + scene_w / 2, y + 20,
                                text="ЛКМ — тащить заряд · ПКМ — удалить · 2×ЛКМ — сменить знак",
                                fill=TEXT_DIM,
                                font=("Segoe UI", 9, "italic"))

        # рабочая область
        gx0 = x + 10
        gy0 = y + 35
        gx1 = x + scene_w - 10
        gy1 = y + h - 10

        gw = gx1 - gx0
        gh = gy1 - gy0

        # сетка
        if self.state.show_grid:
            step = 40
            for i in range(int(gx0), int(gx1), step):
                self.canvas.create_line(i, gy0, i, gy1,
                                        fill="#0d1520", width=1)
            for j in range(int(gy0), int(gy1), step):
                self.canvas.create_line(gx0, j, gx1, j,
                                        fill="#0d1520", width=1)

        # переводим координаты зарядов (0..1) в пиксели
        def to_screen(c):
            return (gx0 + c.x * gw, gy0 + c.y * gh)

        # === силовые линии ===
        if self.state.show_field_lines and self.state.charges:
            # проходим лучи от каждого положительного заряда
            for i, c in enumerate(self.state.charges):
                if c.q > 0:
                    self._draw_field_lines_from_charge(
                        c, gx0, gy0, gw, gh, max_lines=12)

        # === карта потенциала ===
        if self.state.show_potential:
            self._draw_potential_map(gx0, gy0, gw, gh)

        # === векторы поля ===
        if self.state.show_vectors:
            self._draw_field_vectors(gx0, gy0, gw, gh)

        # === эквипотенциали ===
        if self.state.show_equipotential:
            self._draw_equipotentials(gx0, gy0, gw, gh)

        # === заряды ===
        self.charge_screen_positions = []
        for c in self.state.charges:
            sx, sy = to_screen(c)
            self.charge_screen_positions.append((c, sx, sy))
            self._draw_charge(sx, sy, c.q,
                               selected=(c is self.dragging_charge))

        # === панель-инфо внизу ===
        info_y = gy1 - 30
        if self.state.hover_pos:
            hx, hy = self.state.hover_pos
            px = (hx - gx0) / gw
            py = (hy - gy0) / gh
            total_v = 0
            total_e = (0, 0)
            for c in self.state.charges:
                cx, cy = to_screen(c)
                total_v += c.potential_at(hx, hy)
                ex, ey = c.field_at(hx, hy)
                total_e = (total_e[0] + ex, total_e[1] + ey)
            e_mag = math.hypot(*total_e)

            self.canvas.create_text(gx0 + 10, info_y, anchor="w",
                                    text=f"V = {total_v:+.1f} В   |E| = {e_mag:.3f}",
                                    fill=NEON_CYAN,
                                    font=("Consolas", 10, "bold"))

    def _draw_charge(self, cx, cy, q, selected=False):
        r = 22
        # цвет по знаку
        if q > 0:
            base = NEON_RED
        elif q < 0:
            base = NEON_BLUE
        else:
            base = TEXT_DIM

        # свечение
        for i in range(8, 0, -1):
            col = lerp(base, BG_DEEP, 1 - i / 10)
            self.canvas.create_oval(cx - r - i * 2, cy - r - i * 2,
                                    cx + r + i * 2, cy + r + i * 2,
                                    fill="", outline=col, width=1)

        # тень
        self.canvas.create_oval(cx - r + 2, cy - r + 4,
                                cx + r + 2, cy + r + 4,
                                fill="#000000", outline="")
        # тело
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill=lerp(base, BG_DEEP, 0.3),
                                outline=base, width=3)

        # обводка выделения
        if selected:
            self.canvas.create_oval(cx - r - 4, cy - r - 4,
                                    cx + r + 4, cy + r + 4,
                                    fill="", outline="#ffffff",
                                    width=2, dash=(4, 3))

        # символ
        if q > 0:
            text = f"+{int(q)}" if q > 1 else "+"
        else:
            text = f"{int(q)}" if q < -1 else "−"
        self.canvas.create_text(cx, cy, text=text,
                                fill="#ffffff",
                                font=("Consolas", 22, "bold"))

    def _draw_field_lines_from_charge(self, c, gx0, gy0, gw, gh, max_lines=12):
        """Строит силовые линии от положительного заряда."""
        # позиция заряда
        cx = gx0 + c.x * gw
        cy = gy0 + c.y * gh

        # начальный радиус
        start_r = 25
        step = 5
        max_steps = 300

        for i in range(max_lines):
            angle = 2 * math.pi * i / max_lines
            x = cx + start_r * math.cos(angle)
            y = cy + start_r * math.sin(angle)

            path = [(x, y)]

            for s in range(max_steps):
                # вычисляем суммарное поле в точке
                ex, ey = 0, 0
                for ch in self.state.charges:
                    chx = gx0 + ch.x * gw
                    chy = gy0 + ch.y * gh
                    dx = x - chx
                    dy = y - chy
                    r2 = dx * dx + dy * dy
                    r = math.sqrt(r2)
                    if r < 8:
                        r = 8
                        r2 = 64
                    e = ch.q / r2
                    ex += e * dx / r
                    ey += e * dy / r

                mag = math.hypot(ex, ey)
                if mag < 0.001:
                    break
                # нормируем
                x += step * ex / mag
                y += step * ey / mag

                path.append((x, y))

                # если вышли за пределы
                if (x < gx0 or x > gx0 + gw or
                    y < gy0 or y > gy0 + gh):
                    break

                # если попали в другой заряд
                stopped = False
                for ch in self.state.charges:
                    if ch is c:
                        continue
                    chx = gx0 + ch.x * gw
                    chy = gy0 + ch.y * gh
                    if math.hypot(x - chx, y - chy) < 20:
                        stopped = True
                        break
                if stopped:
                    break

            # рисуем линию с градиентом
            if len(path) >= 2:
                flat = []
                for (px, py) in path:
                    flat.extend([px, py])
                # свечение
                self.canvas.create_line(*flat,
                                        fill=lerp(NEON_PURP, BG_DEEP, 0.7),
                                        width=2, smooth=True)
                # основная
                self.canvas.create_line(*flat,
                                        fill=lerp(NEON_PURP, "#ffffff", 0.3),
                                        width=1, smooth=True)

    def _draw_potential_map(self, gx0, gy0, gw, gh):
        """Карта потенциала — цветные области."""
        # сетка ячеек
        cell = 20
        cols = int(gw / cell)
        rows = int(gh / cell)

        for i in range(cols):
            for j in range(rows):
                px = gx0 + i * cell + cell / 2
                py = gy0 + j * cell + cell / 2

                # суммарный потенциал
                v = 0
                for c in self.state.charges:
                    cx = gx0 + c.x * gw
                    cy = gy0 + c.y * gh
                    v += c.potential_at(px, py, k=15)

                # нормируем в диапазон -1..1
                # v может быть от -inf до +inf, используем tanh
                v_norm = math.tanh(v * 0.3)

                if abs(v_norm) < 0.05:
                    continue

                # цвет
                if v_norm > 0:
                    col = lerp(BG_GRAPH, NEON_RED, v_norm * 0.5)
                else:
                    col = lerp(BG_GRAPH, NEON_BLUE, -v_norm * 0.5)

                self.canvas.create_rectangle(
                    px - cell/2, py - cell/2,
                    px + cell/2, py + cell/2,
                    fill=col, outline="")

    def _draw_field_vectors(self, gx0, gy0, gw, gh):
        """Сетка векторов поля."""
        step = 60
        for x in range(int(gx0) + step, int(gx0 + gw), step):
            for y in range(int(gy0) + step, int(gy0 + gh), step):
                ex, ey = 0, 0
                for c in self.state.charges:
                    cx = gx0 + c.x * gw
                    cy = gy0 + c.y * gh
                    dx, dy = c.field_at(x, y)
                    ex += dx * 5000
                    ey += dy * 5000

                mag = math.hypot(ex, ey)
                if mag < 0.1:
                    continue

                # ограничим длину
                max_len = 22
                scale = min(mag, max_len) / mag
                ex *= scale
                ey *= scale

                # линия
                col = lerp(NEON_CYAN, BG_DEEP, 1 - min(mag / max_len, 1.0) * 0.5)
                self.canvas.create_line(x, y, x + ex, y + ey,
                                        fill=col, width=1)
                # точка-конец
                self.canvas.create_oval(x + ex - 2, y + ey - 2,
                                        x + ex + 2, y + ey + 2,
                                        fill=col, outline="")

    def _draw_equipotentials(self, gx0, gy0, gw, gh):
        """Упрощённые эквипотенциальные линии — уровни V = const."""
        # только если есть заряды
        if not self.state.charges:
            return
        # рисуем уровни как концентрические окружности вокруг каждого
        # значимого заряда — упрощённый вид
        for c in self.state.charges:
            cx = gx0 + c.x * gw
            cy = gy0 + c.y * gh
            # уровни по расстояниям
            for i, r_dist in enumerate([40, 80, 130, 190]):
                col = lerp(NEON_AMBER, BG_DEEP, 0.6 + i * 0.05)
                self.canvas.create_oval(cx - r_dist, cy - r_dist,
                                        cx + r_dist, cy + r_dist,
                                        fill="", outline=col,
                                        width=1, dash=(3, 4))

    # ---------- ПАНЕЛЬ УПРАВЛЕНИЯ ----------
    def _draw_panel(self, w, y, h):
        panel_w = 400
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ ПАНЕЛЬ УПРАВЛЕНИЯ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # === Пресеты ===
        self.canvas.create_text(panel_x + 20, y + 55, anchor="w",
                                text="ПРЕСЕТЫ СИСТЕМ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        presets = [
            ("dipole",       "ДИПОЛЬ",         NEON_CYAN),
            ("single_plus",  "+ ОДИН",         NEON_RED),
            ("single_minus", "− ОДИН",         NEON_BLUE),
            ("two_plus",     "+ +",            NEON_RED),
            ("quadrupole",   "КВАДРУПОЛЬ",     NEON_PURP),
            ("capacitor",    "КОНДЕНСАТОР",    NEON_GREEN),
        ]

        p_btn_w = 115
        p_btn_h = 38
        p_gap = 8
        cols = 3
        start_x = panel_x + 20

        for i, (key, label, color) in enumerate(presets):
            row = i // cols
            col = i % cols
            bx = start_x + col * (p_btn_w + p_gap)
            by = y + 75 + row * (p_btn_h + p_gap)
            self._draw_p_btn(bx, by, p_btn_w, p_btn_h,
                              key, label, color)

        # === Добавить заряд ===
        ay = y + 175

        self.canvas.create_text(panel_x + 20, ay, anchor="w",
                                text="ДОБАВИТЬ ЗАРЯД:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        add_btns = [
            ("add_plus",  "+1", NEON_RED),
            ("add_minus", "−1", NEON_BLUE),
        ]
        a_btn_w = 175
        a_btn_h = 42
        a_gap = 10

        for i, (key, label, color) in enumerate(add_btns):
            bx = panel_x + 20 + i * (a_btn_w + a_gap)
            self._draw_a_btn(bx, ay + 20, a_btn_w, a_btn_h,
                              key, label, color)

        # === Отображение ===
        vy = y + 265

        self.canvas.create_text(panel_x + 20, vy, anchor="w",
                                text="ЧТО ПОКАЗАТЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        toggles = [
            ("field_lines",     "СИЛОВЫЕ ЛИНИИ",     NEON_PURP,
             self.state.show_field_lines),
            ("vectors",         "ВЕКТОРЫ ПОЛЯ",      NEON_CYAN,
             self.state.show_vectors),
            ("potential",       "КАРТА ПОТЕНЦИАЛА",  NEON_RED,
             self.state.show_potential),
            ("equipotential",   "ЭКВИПОТЕНЦИАЛИ",    NEON_AMBER,
             self.state.show_equipotential),
            ("grid",            "СЕТКА",             NEON_GREEN,
             self.state.show_grid),
        ]

        t_btn_w = 175
        t_btn_h = 36
        t_gap = 8
        cols_t = 2

        for i, (key, label, color, active) in enumerate(toggles):
            row = i // cols_t
            col = i % cols_t
            bx = panel_x + 20 + col * (t_btn_w + t_gap)
            by = vy + 20 + row * (t_btn_h + t_gap)
            self._draw_toggle_btn(bx, by, t_btn_w, t_btn_h,
                                   key, label, color, active)

        # === Информация ===
        iy = vy + 200

        round_rect(self.canvas, panel_x + 20, iy,
                   panel_x + panel_w - 20, iy + 180, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, iy + 22,
                                text="СТАТИСТИКА СИСТЕМЫ",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        n_pos = sum(1 for c in self.state.charges if c.q > 0)
        n_neg = sum(1 for c in self.state.charges if c.q < 0)
        total_q = self.state.total_charge()
        energy = self.state.potential_energy()

        lines = [
            ("Зарядов всего",       f"{len(self.state.charges)}",       NEON_CYAN),
            ("Положительных",       f"{n_pos}",                          NEON_RED),
            ("Отрицательных",       f"{n_neg}",                          NEON_BLUE),
            ("Суммарный заряд",     f"{total_q:+d} e",                   NEON_AMBER),
            ("Энергия системы",     f"{energy:+.3f}",                    NEON_GREEN),
        ]

        for i, (label, value, color) in enumerate(lines):
            ly = iy + 55 + i * 24
            self.canvas.create_text(panel_x + 35, ly, anchor="w",
                                    text=label, fill=TEXT_DIM,
                                    font=FONT_MONO_S)
            self.canvas.create_text(panel_x + panel_w - 35, ly, anchor="e",
                                    text=value, fill=color,
                                    font=FONT_MONO_S)

        # === Кнопки внизу ===
        by = y + h - 60
        b_w = 175
        b_h = 44
        b_gap = 10

        self._draw_btn(panel_x + 20, by, b_w, b_h,
                       "✕ ОЧИСТИТЬ", NEON_RED, "clear")
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "🎲 СЛУЧАЙНО", NEON_PURP, "random")

    def _draw_p_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.82),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[f"preset_{key}"] = (x, y, x + w, y + h)

    def _draw_a_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.7),
                   outline=color, width=2)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Consolas", 20, "bold"))
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
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"toggle_{key}"] = (x, y, x + w, y + h)

    def _draw_btn(self, x, y, w, h, text, color, key):
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

        self._draw_bg(w, h)
        self._draw_header(w)

        # сцена слева
        scene_y = 90
        scene_h = h - 110
        self._draw_scene(50, scene_y, w, scene_h)

        # панель справа
        self._draw_panel(w, 90, h - 110)

    # ---------- СОБЫТИЯ ----------
    def _on_motion(self, event):
        self.state.hover_pos = (event.x, event.y)

    def _on_leave(self, event):
        self.state.hover_pos = None

    def _on_click(self, event):
        x, y = event.x, event.y

        # кнопки
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

        # клик по заряду?
        if hasattr(self, "charge_screen_positions"):
            for c, cx, cy in self.charge_screen_positions:
                if math.hypot(x - cx, y - cy) < 25:
                    if event.num == 3:   # правая кнопка мыши
                        self.state.remove_charge(c)
                        return
                    # ПКМ через Windows — Button-3, мышь выдаёт через состояние
                    self.dragging_charge = c
                    return

        # правый клик — удалить под мышью
        if event.num == 3:
            if hasattr(self, "charge_screen_positions"):
                for c, cx, cy in self.charge_screen_positions:
                    if math.hypot(x - cx, y - cy) < 25:
                        self.state.remove_charge(c)
                        return

    def _on_drag(self, event):
        if self.dragging_charge is None:
            return

        # обновляем координаты заряда
        panel_w = 400
        scene_w = self.W - 100 - panel_w - 20
        gx0 = 50 + 10
        gy0 = 90 + 35
        gx1 = 50 + scene_w - 10
        gy1 = 90 + (self.H - 110) - 10
        gw = gx1 - gx0
        gh = gy1 - gy0

        # переводим пиксель → 0..1
        nx = (event.x - gx0) / gw
        ny = (event.y - gy0) / gh
        self.dragging_charge.x = max(0.02, min(0.98, nx))
        self.dragging_charge.y = max(0.02, min(0.98, ny))

    def _on_release(self, event):
        self.dragging_charge = None

    def _do_action(self, key):
        if key == "clear":
            self.state.clear()
        elif key == "random":
            self.state.charges = []
            n = random.randint(2, 5)
            for _ in range(n):
                q = random.choice([+1, -1, +2, -2])
                self.state.add_charge(random.uniform(0.15, 0.85),
                                       random.uniform(0.15, 0.85), q)
        elif key.startswith("preset_"):
            name = key[7:]
            self.state.preset(name)
        elif key == "add_plus":
            self.state.add_charge(random.uniform(0.2, 0.8),
                                   random.uniform(0.2, 0.8), +1)
        elif key == "add_minus":
            self.state.add_charge(random.uniform(0.2, 0.8),
                                   random.uniform(0.2, 0.8), -1)
        elif key.startswith("toggle_"):
            name = key[7:]
            if name == "field_lines":
                self.state.show_field_lines = not self.state.show_field_lines
            elif name == "vectors":
                self.state.show_vectors = not self.state.show_vectors
            elif name == "potential":
                self.state.show_potential = not self.state.show_potential
            elif name == "equipotential":
                self.state.show_equipotential = not self.state.show_equipotential
            elif name == "grid":
                self.state.show_grid = not self.state.show_grid

    # ---------- АНИМАЦИЯ ----------
    def _animate(self):
        self.frame_count += 1
        now = time.time()
        if now - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = now

        dt = 0.033
        self.state.tick(dt)

        self._redraw_all()
        self.root.after(60, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()