"""
ОКФРС. Практика 7. Задание 7.
Физический движок — моделирование движения твёрдых тел:
гравитация, столкновения, упругость, трение.
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

# 8 ярких цветов для шариков
BALL_COLORS = [
    NEON_CYAN, NEON_GREEN, NEON_PINK, NEON_PURP,
    NEON_AMBER, NEON_RED, NEON_BLUE, "#ff8c42",
]


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
# ФИЗИЧЕСКОЕ ТЕЛО
# ============================================================
class Ball:
    """Упругое тело — круг."""
    def __init__(self, x, y, r=18, mass=None, color=None):
        self.x = x                # позиция (в пикселях сцены)
        self.y = y
        self.vx = 0.0             # скорость
        self.vy = 0.0
        self.r = r
        # масса пропорциональна площади
        self.mass = mass if mass is not None else (r ** 2) / 400.0
        self.color = color or random.choice(BALL_COLORS)
        self.restitution = 0.85   # упругость (0..1)
        self.friction = 0.999     # трение воздуха
        self.trail = []
        self.trail_max = 20
        self.pinned = False       # закреплён (не двигается)
        self.dragging = False
        self.drag_offset = (0, 0)
        self.flash_t = 0.0        # вспышка при столкновении

    def kinetic_energy(self):
        return 0.5 * self.mass * (self.vx ** 2 + self.vy ** 2)


# ============================================================
# СЦЕНА
# ============================================================
class PhysicsWorld:
    def __init__(self):
        self.balls = []
        self.gravity = 500.0      # px/s²
        self.restitution = 0.85   # по умолчанию
        self.air_friction = 0.999
        self.bounds = (0, 0, 800, 600)   # (x, y, w, h)
        self.stopped = False

        # счётчики
        self.collision_count = 0
        self.last_collision_time = 0.0

    def add_ball(self, x, y, r=None):
        r = r if r is not None else random.randint(12, 30)
        b = Ball(x, y, r=r)
        b.restitution = self.restitution
        b.friction = self.air_friction
        self.balls.append(b)
        return b

    def clear(self):
        self.balls = []
        self.collision_count = 0

    def step(self, dt):
        """Один шаг симуляции."""
        if self.stopped:
            return

        bx, by, bw, bh = self.bounds

        # === интеграция + стены ===
        for b in self.balls:
            if b.pinned or b.dragging:
                continue

            # сила тяжести
            b.vy += self.gravity * dt

            # трение воздуха
            b.vx *= b.friction
            b.vy *= b.friction

            # обновление позиции
            b.x += b.vx * dt
            b.y += b.vy * dt

            # отскок от стен
            if b.x - b.r < bx:
                b.x = bx + b.r
                b.vx = -b.vx * b.restitution
                b.flash_t = 0.2
            elif b.x + b.r > bx + bw:
                b.x = bx + bw - b.r
                b.vx = -b.vx * b.restitution
                b.flash_t = 0.2

            if b.y - b.r < by:
                b.y = by + b.r
                b.vy = -b.vy * b.restitution
                b.flash_t = 0.2
            elif b.y + b.r > by + bh:
                b.y = by + bh - b.r
                b.vy = -b.vy * b.restitution
                # трение о пол
                b.vx *= 0.98
                b.flash_t = 0.2

            # затухание вспышки
            if b.flash_t > 0:
                b.flash_t = max(0.0, b.flash_t - dt)

            # трейл
            b.trail.append((b.x, b.y))
            if len(b.trail) > b.trail_max:
                b.trail.pop(0)

        # === столкновения шар-шар ===
        n = len(self.balls)
        for i in range(n):
            for j in range(i + 1, n):
                self._resolve_collision(self.balls[i], self.balls[j])

    def _resolve_collision(self, a, b):
        """Упругое столкновение двух шаров."""
        dx = b.x - a.x
        dy = b.y - a.y
        dist = math.hypot(dx, dy)
        min_dist = a.r + b.r

        if dist < min_dist and dist > 0.001:
            # нормаль столкновения
            nx = dx / dist
            ny = dy / dist

            # взаимное проникновение
            overlap = min_dist - dist

            # расталкиваем (пропорционально массам)
            total_m = a.mass + b.mass
            if total_m > 0:
                a.x -= nx * overlap * (b.mass / total_m)
                a.y -= ny * overlap * (b.mass / total_m)
                b.x += nx * overlap * (a.mass / total_m)
                b.y += ny * overlap * (a.mass / total_m)

            # относительная скорость
            rvx = b.vx - a.vx
            rvy = b.vy - a.vy

            # проекция на нормаль
            vn = rvx * nx + rvy * ny

            if vn > 0:
                return    # уже расходятся

            # коэффициент восстановления — среднее двух
            e = (a.restitution + b.restitution) / 2.0

            # импульс
            j_imp = -(1 + e) * vn / (1 / a.mass + 1 / b.mass)

            # применяем
            a.vx -= j_imp * nx / a.mass
            a.vy -= j_imp * ny / a.mass
            b.vx += j_imp * nx / b.mass
            b.vy += j_imp * ny / b.mass

            # вспышка
            a.flash_t = 0.3
            b.flash_t = 0.3

            self.collision_count += 1
            self.last_collision_time = time.time()

    def total_kinetic(self):
        return sum(b.kinetic_energy() for b in self.balls)

    def stats(self):
        n = len(self.balls)
        ke = self.total_kinetic()
        avg_v = 0
        if n > 0:
            avg_v = sum(math.hypot(b.vx, b.vy) for b in self.balls) / n
        return {
            "n": n,
            "kinetic": ke,
            "avg_v": avg_v,
            "collisions": self.collision_count,
        }


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Physics Engine · 2D Bodies")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0
        self.last_time = time.time()

        self.world = PhysicsWorld()
        self.btn_zones = {}
        self.slider_zones = {}
        self.drag_slider = None
        self.dragging_ball = None

        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)

        # начальная сцена
        self._spawn_default()

        self.root.update_idletasks()
        self._redraw_all()
        self._animate()

    def _spawn_default(self):
        """Начальная сцена — несколько шариков."""
        w = 800
        h = 600
        for i in range(8):
            x = random.uniform(100, w - 100)
            y = random.uniform(50, h / 3)
            self.world.add_ball(x, y, r=random.randint(14, 28))

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
        self.canvas.create_text(100, 40, text="PHYSICS ENGINE",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(340, 44,
                                text="· 2D ФИЗИЧЕСКИЙ ДВИЖОК",
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
                                text="ЛКМ — тащить шар · ПКМ — удалить · клик по сцене — создать",
                                fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        # внутренняя область — bounds
        bx = x + 15
        by = y + 40
        bw = scene_w - 30
        bh = h - 55

        self.world.bounds = (bx, by, bw, bh)
        self.scene_rect = (bx, by, bw, bh)

        # сетка внутри
        step = 40
        for i in range(int(bx), int(bx + bw), step):
            self.canvas.create_line(i, by, i, by + bh,
                                    fill="#0d1520", width=1)
        for j in range(int(by), int(by + bh), step):
            self.canvas.create_line(bx, j, bx + bw, j,
                                    fill="#0d1520", width=1)

        # стены
        self.canvas.create_rectangle(bx, by, bx + bw, by + bh,
                                      fill="", outline=NEON_AMBER, width=2)

        # === шарики ===
        for ball in self.world.balls:
            self._draw_ball(ball)

    def _draw_ball(self, b):
        px = b.x
        py = b.y
        r = b.r

        # трейл
        if len(b.trail) > 2:
            for i in range(1, len(b.trail)):
                t = i / len(b.trail)
                x0, y0 = b.trail[i-1]
                x1, y1 = b.trail[i]
                col = lerp(BG_GRAPH, b.color, t * 0.4)
                self.canvas.create_line(x0, y0, x1, y1,
                                         fill=col, width=1)

        # свечение при столкновении
        if b.flash_t > 0:
            glow_r = r + 10 + int(b.flash_t * 30)
            for i in range(4, 0, -1):
                rr = glow_r + i * 3
                self.canvas.create_oval(px - rr, py - rr,
                                         px + rr, py + rr,
                                         fill="",
                                         outline=lerp(b.color, BG_GRAPH,
                                                      1 - i / 5),
                                         width=1)

        # тень снизу
        self.canvas.create_oval(px - r + 3, py - r + 6,
                                 px + r + 3, py + r + 6,
                                 fill="#000000", outline="")

        # тело
        self.canvas.create_oval(px - r, py - r, px + r, py + r,
                                 fill=lerp(b.color, BG_DEEP, 0.3),
                                 outline=b.color, width=3)

        # блик
        self.canvas.create_oval(px - r * 0.6, py - r * 0.7,
                                 px - r * 0.15, py - r * 0.25,
                                 fill=lerp(b.color, "#ffffff", 0.5),
                                 outline="")

        # если pinned — крестик
        if b.pinned:
            self.canvas.create_line(px - 6, py - 6, px + 6, py + 6,
                                     fill="#ffffff", width=2)
            self.canvas.create_line(px - 6, py + 6, px + 6, py - 6,
                                     fill="#ffffff", width=2)

        # выделение при перетаскивании
        if b.dragging:
            self.canvas.create_oval(px - r - 4, py - r - 4,
                                     px + r + 4, py + r + 4,
                                     fill="", outline="#ffffff", width=2,
                                     dash=(4, 3))

        # вектор скорости при быстром движении
        speed = math.hypot(b.vx, b.vy)
        if speed > 50 and not b.dragging:
            k = min(1.5, speed / 400)
            vx_end = px + b.vx * 0.15
            vy_end = py + b.vy * 0.15
            self.canvas.create_line(px, py, vx_end, vy_end,
                                     fill=lerp(b.color, "#ffffff", 0.7),
                                     width=2, arrow=tk.LAST,
                                     arrowshape=(8, 10, 4))

    # ---------- ПАНЕЛЬ ----------
    def _draw_panel(self, w, y, h):
        panel_w = 400
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ УПРАВЛЕНИЕ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # === Пресеты сцен ===
        self.canvas.create_text(panel_x + 20, y + 55, anchor="w",
                                text="СЦЕНАРИИ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        scenes = [
            ("basic",    "СТАНДАРТ",  NEON_CYAN),
            ("pyramid",  "ПИРАМИДА",  NEON_GREEN),
            ("rain",     "ДОЖДЬ",     NEON_AMBER),
            ("collision","СТОЛКНОВЕНИЕ", NEON_PINK),
            ("trampoline","БАТУТ",    NEON_PURP),
        ]
        s_w = 68
        s_h = 36
        s_gap = 6

        for i, (key, label, color) in enumerate(scenes):
            bx = panel_x + 20 + i * (s_w + s_gap)
            self._draw_small_btn(bx, y + 75, s_w, s_h,
                                   f"scene_{key}", label, color)

        # === Гравитация ===
        gy = y + 140

        self.canvas.create_text(panel_x + 20, gy, anchor="w",
                                text="ГРАВИТАЦИЯ (px/s²):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w - 20, gy, anchor="e",
                                text=f"{self.world.gravity:.0f}",
                                fill=NEON_AMBER, font=FONT_MONO)
        self._draw_slider(panel_x + 20, gy + 25, panel_w - 40,
                           self.world.gravity / 2000.0,
                           "gravity", 0, 2000, NEON_AMBER)

        # === Упругость ===
        uy = y + 205

        self.canvas.create_text(panel_x + 20, uy, anchor="w",
                                text="УПРУГОСТЬ (0..1):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w - 20, uy, anchor="e",
                                text=f"{self.world.restitution:.2f}",
                                fill=NEON_GREEN, font=FONT_MONO)
        self._draw_slider(panel_x + 20, uy + 25, panel_w - 40,
                           self.world.restitution,
                           "restitution", 0.0, 1.0, NEON_GREEN)

        # === Трение воздуха ===
        fy = y + 270

        self.canvas.create_text(panel_x + 20, fy, anchor="w",
                                text="ТРЕНИЕ ВОЗДУХА (0.9..1.0):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w - 20, fy, anchor="e",
                                text=f"{self.world.air_friction:.3f}",
                                fill=NEON_CYAN, font=FONT_MONO)
        self._draw_slider(panel_x + 20, fy + 25, panel_w - 40,
                           (self.world.air_friction - 0.9) / 0.1,
                           "friction", 0.9, 1.0, NEON_CYAN)

        # === Добавить шар ===
        ay = y + 340

        self.canvas.create_text(panel_x + 20, ay, anchor="w",
                                text="ДОБАВИТЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        add_btns = [
            ("add_small", "🔵 МАЛЫЙ",  NEON_CYAN),
            ("add_med",   "🟢 СРЕДНИЙ", NEON_GREEN),
            ("add_big",   "🟠 БОЛЬШОЙ", NEON_AMBER),
            ("add_random","🎲 СЛУЧАЙНО", NEON_PURP),
        ]
        a_w = 84
        a_h = 42
        a_gap = 6

        for i, (key, label, color) in enumerate(add_btns):
            bx = panel_x + 20 + i * (a_w + a_gap)
            self._draw_small_btn(bx, ay + 20, a_w, a_h, key, label, color)

        # === Статистика ===
        sty = y + 420
        stats = self.world.stats()

        round_rect(self.canvas, panel_x + 20, sty,
                   panel_x + panel_w - 20, sty + 165, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, sty + 22,
                                text="СТАТИСТИКА СИСТЕМЫ",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        lines = [
            ("Шаров",            f"{stats['n']}",                     NEON_CYAN),
            ("Кинетическая E",   f"{stats['kinetic']:.1f}",          NEON_AMBER),
            ("Средняя скорость", f"{stats['avg_v']:.1f} px/s",       NEON_GREEN),
            ("Столкновений",     f"{stats['collisions']}",           NEON_PINK),
        ]

        for i, (label, value, color) in enumerate(lines):
            ly = sty + 55 + i * 24
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
                       "⏸ ПАУЗА" if not self.world.stopped else "▶ ПУСК",
                       NEON_AMBER, "pause",
                       active=self.world.stopped)
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

    def _draw_small_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 6,
                   fill=lerp(color, BG_DEEP, 0.82),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Segoe UI", 8, "bold"))
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

        # шары — с ВОЗВРАТОМ
        self._try_start_ball_drag(x, y)

    def _try_start_ball_drag(self, mx, my):
        # ищем шар под курсором (сверху вниз)
        for b in reversed(self.world.balls):
            if math.hypot(mx - b.x, my - b.y) <= b.r:
                b.dragging = True
                b.drag_offset = (b.x - mx, b.y - my)
                self.dragging_ball = b
                # остановим его
                b.vx = 0
                b.vy = 0
                return
        # нет шара под курсором — создать новый
        # но только если клик внутри сцены
        if hasattr(self, "scene_rect"):
            bx, by, bw, bh = self.scene_rect
            if bx + 5 < mx < bx + bw - 5 and by + 5 < my < by + bh - 5:
                new_ball = self.world.add_ball(mx, my,
                                                r=random.randint(14, 24))
                new_ball.vx = random.uniform(-100, 100)
                new_ball.vy = random.uniform(-50, 50)

    def _on_drag(self, event):
        if self.drag_slider:
            self._set_slider_from_mouse(self.drag_slider, event.x)
            return

        if self.dragging_ball is None:
            return
        ox, oy = self.dragging_ball.drag_offset
        self.dragging_ball.x = event.x + ox
        self.dragging_ball.y = event.y + oy

    def _on_release(self, event):
        self.drag_slider = None
        if self.dragging_ball:
            self.dragging_ball.dragging = False
            # при отпускании даём импульс в направлении движения
            self.dragging_ball.vx = 0
            self.dragging_ball.vy = 0
            self.dragging_ball = None

    def _on_right_click(self, event):
        # удалить шар под курсором
        mx, my = event.x, event.y
        for b in list(self.world.balls):
            if math.hypot(mx - b.x, my - b.y) <= b.r:
                self.world.balls.remove(b)
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
        if key == "gravity":
            self.world.gravity = val
        elif key == "restitution":
            self.world.restitution = val
            for b in self.world.balls:
                b.restitution = val
        elif key == "friction":
            self.world.air_friction = val
            for b in self.world.balls:
                b.friction = val

    def _do_action(self, key):
        if key == "pause":
            self.world.stopped = not self.world.stopped
        elif key == "clear":
            self.world.clear()
        elif key.startswith("scene_"):
            self._apply_scene(key[6:])
        elif key == "add_small":
            self._add_random_ball(r=14)
        elif key == "add_med":
            self._add_random_ball(r=22)
        elif key == "add_big":
            self._add_random_ball(r=32)
        elif key == "add_random":
            self._add_random_ball(r=random.randint(10, 36))

    def _add_random_ball(self, r=None):
        if not hasattr(self, "scene_rect"):
            return
        bx, by, bw, bh = self.scene_rect
        x = random.uniform(bx + 50, bx + bw - 50)
        y = random.uniform(by + 50, by + 100)
        b = self.world.add_ball(x, y, r=r)
        b.vx = random.uniform(-150, 150)
        b.vy = random.uniform(-50, 50)

    def _apply_scene(self, name):
        self.world.clear()
        bx, by, bw, bh = self.scene_rect

        if name == "basic":
            for _ in range(8):
                x = random.uniform(bx + 50, bx + bw - 50)
                y = random.uniform(by + 50, by + bh / 3)
                self.world.add_ball(x, y, r=random.randint(14, 26))

        elif name == "pyramid":
            # пирамида шаров
            cols = 6
            rows = 4
            r = 16
            start_x = bx + bw / 2 - (cols * r * 2) / 2
            start_y = by + 100
            for i in range(rows):
                n_in_row = cols - i
                for j in range(n_in_row):
                    x = start_x + j * r * 2 + i * r
                    y = by + bh - 50 - i * r * 2
                    self.world.add_ball(x, y, r=r)

        elif name == "rain":
            for _ in range(20):
                x = random.uniform(bx + 20, bx + bw - 20)
                y = by + 30
                b = self.world.add_ball(x, y, r=random.randint(8, 16))
                b.vy = random.uniform(100, 300)

        elif name == "collision":
            # два шара летят навстречу
            b1 = self.world.add_ball(bx + 100, by + bh / 2, r=25)
            b1.vx = 400
            b2 = self.world.add_ball(bx + bw - 100, by + bh / 2, r=25)
            b2.vx = -400

        elif name == "trampoline":
            for _ in range(10):
                x = random.uniform(bx + 30, bx + bw - 30)
                y = random.uniform(by + 30, by + bh / 2)
                b = self.world.add_ball(x, y, r=random.randint(10, 20))
                b.restitution = 0.98   # очень упругие
                b.vy = random.uniform(-300, -100)

    # ---------- АНИМАЦИЯ ----------
    def _animate(self):
        self.frame_count += 1
        now = time.time()
        if now - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = now

        dt = min(0.033, now - self.last_time)
        self.last_time = now

        # 4 подшага для точности
        substeps = 4
        sub_dt = dt / substeps
        for _ in range(substeps):
            self.world.step(sub_dt)

        self._redraw_all()
        self.root.after(16, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()