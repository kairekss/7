"""
ОКФРС. Практика 7. Задание 5.
Симуляция «Магниты и электромагниты»:
постоянные магниты + катушка с током + компас + силовые линии.
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
# МАГНИТ (постоянный)
# ============================================================
class Magnet:
    """Полосовой магнит с полюсами N (красный) и S (синий)."""
    def __init__(self, x, y, length=120, width=40, angle=0, strength=1.0):
        self.x = x
        self.y = y
        self.length = length
        self.width = width
        self.angle = angle       # в радианах
        self.strength = strength # 0.5..2.0
        self.dragging = False

    def poles(self):
        """
        Возвращает координаты двух полюсов.
        N — на одном конце, S — на другом.
        """
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        half = self.length / 2
        # N полюс — справа (по углу)
        nx = self.x + half * ca
        ny = self.y + half * sa
        # S полюс — слева
        sx = self.x - half * ca
        sy = self.y - half * sa
        return (nx, ny), (sx, sy)

    def field_at(self, px, py):
        """
        Суммарное поле от двух полюсов диполя.
        N — источник (+), S — сток (−).
        """
        (nx, ny), (sx, sy) = self.poles()
        bx, by = 0, 0
        # от N полюса
        dx, dy = px - nx, py - ny
        r = max(math.hypot(dx, dy), 12)
        b = self.strength * 8000 / (r * r)
        bx += b * dx / r
        by += b * dy / r
        # к S полюсу (отрицательный источник)
        dx, dy = px - sx, py - sy
        r = max(math.hypot(dx, dy), 12)
        b = self.strength * 8000 / (r * r)
        bx -= b * dx / r
        by -= b * dy / r
        return bx, by

    def contains_point(self, px, py, margin=10):
        # проверяем, попадает ли точка в прямоугольник магнита
        dx = px - self.x
        dy = py - self.y
        ca = math.cos(-self.angle)
        sa = math.sin(-self.angle)
        lx = dx * ca - dy * sa
        ly = dx * sa + dy * ca
        return (abs(lx) <= self.length / 2 + margin and
                abs(ly) <= self.width / 2 + margin)


# ============================================================
# ЭЛЕКТРОМАГНИТ (катушка)
# ============================================================
class Electromagnet:
    """Катушка с током. Создаёт поле вдоль оси."""
    def __init__(self, x, y, length=140, width=50, angle=0):
        self.x = x
        self.y = y
        self.length = length
        self.width = width
        self.angle = angle
        self.current = 0.0        # сила тока (-2..+2)
        self.turns = 6            # число витков (для вида)
        self.dragging = False

    def poles(self):
        """N и S полюсы катушки зависят от направления тока."""
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        half = self.length / 2
        # при положительном токе N справа
        if self.current >= 0:
            nx = self.x + half * ca
            ny = self.y + half * sa
            sx = self.x - half * ca
            sy = self.y - half * sa
        else:
            nx = self.x - half * ca
            ny = self.y - half * sa
            sx = self.x + half * ca
            sy = self.y + half * sa
        return (nx, ny), (sx, sy)

    def field_at(self, px, py):
        """Поле катушки — как от диполя, но пропорционально току."""
        if abs(self.current) < 0.01:
            return 0, 0
        (nx, ny), (sx, sy) = self.poles()
        strength = self.current * 1.0
        bx, by = 0, 0
        dx, dy = px - nx, py - ny
        r = max(math.hypot(dx, dy), 12)
        b = strength * 8000 / (r * r)
        bx += b * dx / r
        by += b * dy / r
        dx, dy = px - sx, py - sy
        r = max(math.hypot(dx, dy), 12)
        b = strength * 8000 / (r * r)
        bx -= b * dx / r
        by -= b * dy / r
        return bx, by

    def contains_point(self, px, py, margin=10):
        dx = px - self.x
        dy = py - self.y
        ca = math.cos(-self.angle)
        sa = math.sin(-self.angle)
        lx = dx * ca - dy * sa
        ly = dx * sa + dy * ca
        return (abs(lx) <= self.length / 2 + margin and
                abs(ly) <= self.width / 2 + margin)


# ============================================================
# КОМПАС
# ============================================================
class Compass:
    """Компас — стрелка, ориентируется по магнитному полю."""
    def __init__(self, x, y, r=28):
        self.x = x
        self.y = y
        self.r = r
        self.angle = 0.0          # текущий угол стрелки
        self.dragging = False

    def contains_point(self, px, py, margin=5):
        return math.hypot(px - self.x, py - self.y) <= self.r + margin


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.magnets = []
        self.electromagnet = None
        self.compasses = []

        # показ
        self.show_field_lines = True
        self.show_field_vectors = False
        self.show_grid = True

        self.pulse_t = 0.0
        self.paused = False

        # начальная сцена — 2 магнита + 1 катушка + 2 компаса
        self.reset_scene()

    def reset_scene(self):
        self.magnets = [
            Magnet(0.30, 0.35, length=140, width=45,
                    angle=0, strength=1.0),
            Magnet(0.70, 0.60, length=140, width=45,
                    angle=math.pi, strength=0.8),
        ]
        self.electromagnet = Electromagnet(0.5, 0.5, length=160, width=50,
                                             angle=math.pi/2)
        self.electromagnet.current = 1.5

        self.compasses = [
            Compass(0.20, 0.75, r=26),
            Compass(0.80, 0.25, r=26),
        ]

    def tick(self, dt):
        self.pulse_t += dt
        if self.paused:
            return

        # обновляем углы компас-стрелок по суммарному полю
        for c in self.compasses:
            # пропускаем если перетаскивается
            if c.dragging:
                continue
            bx, by = self.total_field(c.x, c.y)
            if math.hypot(bx, by) > 0.01:
                target_angle = math.atan2(by, bx)
                # плавное приближение
                diff = target_angle - c.angle
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi
                c.angle += diff * min(1.0, dt * 8)

    def total_field(self, px, py):
        """Суммарное поле от всех источников в пикселях экрана."""
        bx, by = 0, 0
        for m in self.magnets:
            fx, fy = m.field_at(px, py)
            bx += fx
            by += fy
        if self.electromagnet:
            fx, fy = self.electromagnet.field_at(px, py)
            bx += fx
            by += fy
        return bx, by

    def add_magnet(self):
        # в случайное место
        m = Magnet(random.uniform(0.2, 0.8),
                    random.uniform(0.2, 0.8),
                    length=120, width=42,
                    angle=random.uniform(0, 2 * math.pi),
                    strength=random.uniform(0.6, 1.2))
        self.magnets.append(m)

    def add_compass(self):
        c = Compass(random.uniform(0.15, 0.85),
                     random.uniform(0.15, 0.85),
                     r=24)
        self.compasses.append(c)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Magnets & Electromagnets")
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
        self.canvas.create_text(100, 40, text="MAGNETS & ELECTROMAGNETS",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(450, 44,
                                text="· МАГНИТЫ · КАТУШКА · КОМПАС",
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
                                text="ЛКМ — тащить · ПКМ — удалить",
                                fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        gx0 = x + 10
        gy0 = y + 40
        gx1 = x + scene_w - 10
        gy1 = y + h - 10

        gw = gx1 - gx0
        gh = gy1 - gy0

        self.scene_rect = (gx0, gy0, gw, gh)

        # сетка
        if self.state.show_grid:
            step = 45
            for i in range(int(gx0), int(gx1), step):
                self.canvas.create_line(i, gy0, i, gy1,
                                        fill="#0d1520", width=1)
            for j in range(int(gy0), int(gy1), step):
                self.canvas.create_line(gx0, j, gx1, j,
                                        fill="#0d1520", width=1)

        def to_px(obj):
            return (gx0 + obj.x * gw, gy0 + obj.y * gh)

        # === магнитное поле (векторы) ===
        if self.state.show_field_vectors:
            step = 50
            for sx in range(int(gx0) + step // 2, int(gx1), step):
                for sy in range(int(gy0) + step // 2, int(gy1), step):
                    bx, by = self.state.total_field(sx, sy)
                    mag = math.hypot(bx, by)
                    if mag < 0.5:
                        continue
                    # ограничим длину
                    max_len = 18
                    scale = min(max_len, mag) / mag
                    ex = bx * scale
                    ey = by * scale
                    col = lerp(NEON_CYAN, BG_DEEP,
                               1 - min(mag / 50, 1.0) * 0.7)
                    self.canvas.create_line(sx, sy, sx + ex, sy + ey,
                                            fill=col, width=1)
                    self.canvas.create_oval(sx + ex - 2, sy + ey - 2,
                                            sx + ex + 2, sy + ey + 2,
                                            fill=col, outline="")

        # === силовые линии ===
        if self.state.show_field_lines:
            # стартуем от N полюсов всех источников
            for m in self.state.magnets:
                (nx, ny), (sx, sy) = m.poles()
                npx, npy = gx0 + nx * gw, gy0 + ny * gh
                self._trace_field_line(npx, npy, gx0, gy0, gw, gh, +1)
            if self.state.electromagnet and \
               abs(self.state.electromagnet.current) > 0.05:
                em = self.state.electromagnet
                (nx, ny), (sx, sy) = em.poles()
                npx, npy = gx0 + nx * gw, gy0 + ny * gh
                self._trace_field_line(npx, npy, gx0, gy0, gw, gh, +1)

        # === магниты ===
        for m in self.state.magnets:
            self._draw_magnet(m, gx0, gy0, gw, gh)

        # === катушка ===
        if self.state.electromagnet:
            self._draw_electromagnet(self.state.electromagnet,
                                       gx0, gy0, gw, gh)

        # === компасы ===
        for c in self.state.compasses:
            self._draw_compass(c, gx0, gy0, gw, gh)

    def _trace_field_line(self, start_px, start_py, gx0, gy0, gw, gh,
                            sign=+1, max_steps=200, step=4):
        """Трассирует одну силовую линию от N полюса."""
        x, y = start_px, start_py
        # немного отступить
        bx, by = self.state.total_field(x, y)
        mag = math.hypot(bx, by)
        if mag < 0.01:
            return
        x += 12 * bx / mag
        y += 12 * by / mag

        path = [(x, y)]
        for _ in range(max_steps):
            bx, by = self.state.total_field(x, y)
            mag = math.hypot(bx, by)
            if mag < 0.01:
                break
            x += step * bx / mag * sign
            y += step * by / mag * sign
            path.append((x, y))
            # вышли за границы
            if (x < gx0 or x > gx0 + gw or y < gy0 or y > gy0 + gh):
                break
            # близко к полюсу — стоп
            hit = False
            for m in self.state.magnets:
                (nx, ny), (sx, sy) = m.poles()
                spx, spy = gx0 + sx * gw, gy0 + sy * gh
                if math.hypot(x - spx, y - spy) < 10:
                    hit = True
                    break
            if hit:
                break

        if len(path) >= 2:
            flat = []
            for (px, py) in path:
                flat.extend([px, py])
            self.canvas.create_line(*flat,
                                    fill=lerp(NEON_PURP, BG_DEEP, 0.5),
                                    width=1, smooth=True)

    def _draw_magnet(self, m, gx0, gy0, gw, gh):
        cx = gx0 + m.x * gw
        cy = gy0 + m.y * gh
        length = m.length
        width = m.width
        ca = math.cos(m.angle)
        sa = math.sin(m.angle)

        # 4 угла прямоугольника магнита
        def corner(dx, dy):
            return (cx + dx * ca - dy * sa,
                    cy + dx * sa + dy * ca)

        hl = length / 2
        hw = width / 2

        # N-половина (красная) — правая
        n_pts = [corner(0, -hw), corner(hl, -hw),
                  corner(hl, hw), corner(0, hw)]
        # S-половина (синяя) — левая
        s_pts = [corner(-hl, -hw), corner(0, -hw),
                  corner(0, hw), corner(-hl, hw)]

        # тень
        self.canvas.create_polygon([(x + 3, y + 5) for (x, y) in n_pts],
                                    fill="#000000", outline="")
        self.canvas.create_polygon([(x + 3, y + 5) for (x, y) in s_pts],
                                    fill="#000000", outline="")

        # S-половина
        self.canvas.create_polygon(s_pts,
                                    fill=lerp(NEON_BLUE, BG_DEEP, 0.3),
                                    outline="#1a3a6a", width=2)
        # N-половина
        self.canvas.create_polygon(n_pts,
                                    fill=lerp(NEON_RED, BG_DEEP, 0.3),
                                    outline="#6a1a1a", width=2)

        # буквы
        # центр N
        ncx = cx + hl * 0.5 * ca
        ncy = cy + hl * 0.5 * sa
        scx = cx - hl * 0.5 * ca
        scy = cy - hl * 0.5 * sa

        self.canvas.create_text(ncx, ncy, text="N",
                                fill="#ffffff",
                                font=("Consolas", 20, "bold"))
        self.canvas.create_text(scx, scy, text="S",
                                fill="#ffffff",
                                font=("Consolas", 20, "bold"))

        # подсветка при перетаскивании
        if m.dragging:
            self.canvas.create_polygon(n_pts, fill="", outline="#ffffff",
                                        width=2, dash=(4, 3))
            self.canvas.create_polygon(s_pts, fill="", outline="#ffffff",
                                        width=2, dash=(4, 3))

    def _draw_electromagnet(self, em, gx0, gy0, gw, gh):
        cx = gx0 + em.x * gw
        cy = gy0 + em.y * gh
        length = em.length
        width = em.width
        ca = math.cos(em.angle)
        sa = math.sin(em.angle)

        # корпус (серый стержень)
        def corner(dx, dy):
            return (cx + dx * ca - dy * sa,
                    cy + dx * sa + dy * ca)

        hl = length / 2
        hw = width / 2

        # тень
        body = [corner(-hl, -hw), corner(hl, -hw),
                corner(hl, hw), corner(-hl, hw)]
        self.canvas.create_polygon([(x + 3, y + 5) for (x, y) in body],
                                    fill="#000000", outline="")

        # корпус
        self.canvas.create_polygon(body,
                                    fill="#3a3d48",
                                    outline="#1a1c22", width=2)

        # витки катушки — вертикальные линии поперёк
        n_turns = em.turns
        for i in range(n_turns):
            t = (i + 0.5) / n_turns
            dx = -hl + t * length
            # верх
            x1, y1 = corner(dx, -hw - 4)
            x2, y2 = corner(dx, hw + 4)
            col = NEON_AMBER if em.current > 0 else NEON_CYAN
            self.canvas.create_line(x1, y1, x2, y2,
                                    fill=col, width=3)

        # полярность в зависимости от тока
        if abs(em.current) > 0.05:
            (nx, ny), (sx, sy) = em.poles()
            npx = gx0 + nx * gw
            npy = gy0 + ny * gh
            spx = gx0 + sx * gw
            spy = gy0 + sy * gh

            # N полюс
            self.canvas.create_oval(npx - 14, npy - 14,
                                     npx + 14, npy + 14,
                                     fill=lerp(NEON_RED, BG_DEEP, 0.3),
                                     outline=NEON_RED, width=2)
            self.canvas.create_text(npx, npy, text="N",
                                    fill="#ffffff",
                                    font=("Consolas", 14, "bold"))
            # S полюс
            self.canvas.create_oval(spx - 14, spy - 14,
                                     spx + 14, spy + 14,
                                     fill=lerp(NEON_BLUE, BG_DEEP, 0.3),
                                     outline=NEON_BLUE, width=2)
            self.canvas.create_text(spx, spy, text="S",
                                    fill="#ffffff",
                                    font=("Consolas", 14, "bold"))

        # подпись силы тока
        self.canvas.create_text(cx, cy + hw + 25,
                                text=f"I = {em.current:+.2f} A",
                                fill=NEON_AMBER if em.current > 0 else NEON_CYAN,
                                font=("Consolas", 10, "bold"))

    def _draw_compass(self, c, gx0, gy0, gw, gh):
        cx = gx0 + c.x * gw
        cy = gy0 + c.y * gh
        r = c.r

        # тень
        self.canvas.create_oval(cx - r + 3, cy - r + 5,
                                cx + r + 3, cy + r + 5,
                                fill="#000000", outline="")

        # корпус
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill="#1a1c22",
                                outline=NEON_AMBER, width=2)
        # внутренний круг
        self.canvas.create_oval(cx - r + 4, cy - r + 4,
                                cx + r - 4, cy + r - 4,
                                fill="#0a0d14", outline="#2a3040", width=1)

        # буквы N/S/E/W по кругу
        for letter, ang in [("N", -math.pi/2), ("E", 0),
                             ("S", math.pi/2), ("W", math.pi)]:
            lx = cx + (r - 8) * math.cos(ang)
            ly = cy + (r - 8) * math.sin(ang)
            col = NEON_RED if letter == "N" else TEXT_DIM
            self.canvas.create_text(lx, ly, text=letter,
                                    fill=col,
                                    font=("Consolas", 8, "bold"))

        # стрелка — поворачивается по углу c.angle
        a = c.angle
        # северный конец (красный) — в направлении поля
        nx = cx + (r - 8) * math.cos(a)
        ny = cy + (r - 8) * math.sin(a)
        # южный конец (белый)
        sx = cx - (r - 8) * math.cos(a)
        sy = cy - (r - 8) * math.sin(a)

        # стрелка
        self.canvas.create_line(sx, sy, nx, ny,
                                fill=NEON_RED, width=3,
                                arrow=tk.LAST,
                                arrowshape=(10, 12, 5))
        self.canvas.create_line(cx, cy, sx, sy,
                                fill="#c8c8d0", width=3)

        # центральная точка
        self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                fill="#ffffff", outline="")

        if c.dragging:
            self.canvas.create_oval(cx - r - 3, cy - r - 3,
                                    cx + r + 3, cy + r + 3,
                                    fill="", outline="#ffffff",
                                    width=2, dash=(4, 3))

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

        # === Сила тока катушки ===
        sy = y + 55

        self.canvas.create_text(panel_x + 20, sy, anchor="w",
                                text="ТОК КАТУШКИ  I (A):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        if self.state.electromagnet:
            cur = self.state.electromagnet.current
            self.canvas.create_text(panel_x + panel_w - 20, sy, anchor="e",
                                    text=f"{cur:+.2f}",
                                    fill=NEON_AMBER, font=FONT_MONO)
            # слайдер от -2 до +2
            k = (cur + 2) / 4
            self._draw_slider(panel_x + 20, sy + 30, panel_w - 40,
                                k, "current", -2.0, 2.0, NEON_AMBER,
                                center=True)
        # === Векторы поля ===
        vy = y + 140

        self.canvas.create_text(panel_x + 20, vy, anchor="w",
                                text="ПОКАЗАТЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        toggles = [
            ("field_lines",   "СИЛОВЫЕ ЛИНИИ",  NEON_PURP,
             self.state.show_field_lines),
            ("field_vectors", "ВЕКТОРЫ ПОЛЯ",   NEON_CYAN,
             self.state.show_field_vectors),
            ("grid",          "СЕТКА",          NEON_GREEN,
             self.state.show_grid),
        ]

        t_btn_w = 175
        t_btn_h = 36
        t_gap = 8
        cols = 2

        for i, (key, label, color, active) in enumerate(toggles):
            row = i // cols
            col = i % cols
            bx = panel_x + 20 + col * (t_btn_w + t_gap)
            by = vy + 20 + row * (t_btn_h + t_gap)
            self._draw_toggle_btn(bx, by, t_btn_w, t_btn_h,
                                    key, label, color, active)

        # === Добавить объекты ===
        ay = vy + 120

        self.canvas.create_text(panel_x + 20, ay, anchor="w",
                                text="ДОБАВИТЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        add_btns = [
            ("add_magnet", "🧲 МАГНИТ", NEON_RED),
            ("add_compass", "🧭 КОМПАС", NEON_AMBER),
        ]
        a_w = 175
        a_h = 42
        a_gap = 10

        for i, (key, label, color) in enumerate(add_btns):
            bx = panel_x + 20 + i * (a_w + a_gap)
            self._draw_a_btn(bx, ay + 20, a_w, a_h, key, label, color)

        # === Пресеты ===
        py = ay + 80

        self.canvas.create_text(panel_x + 20, py, anchor="w",
                                text="ПРЕСЕТЫ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        presets = [
            ("attract",  "ПРИТЯЖЕНИЕ",   NEON_GREEN),
            ("repel",    "ОТТАЛКИВАНИЕ", NEON_RED),
            ("coil",     "КАТУШКА",      NEON_AMBER),
            ("empty",    "ОЧИСТИТЬ",     NEON_PURP),
        ]
        p_w = 84
        p_h = 36
        p_gap = 6

        for i, (key, label, color) in enumerate(presets):
            bx = panel_x + 20 + i * (p_w + p_gap)
            self._draw_p_btn(bx, py + 20, p_w, p_h, key, label, color)

        # === Информационный блок ===
        iy = py + 70

        round_rect(self.canvas, panel_x + 20, iy,
                   panel_x + panel_w - 20, iy + 155, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, iy + 22,
                                text="ФИЗИКА",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        info_lines = [
            "🧲 Постоянный магнит:",
            "  N и S полюсы, поле B всегда замкнуто.",
            "",
            "⚡ Электромагнит:",
            "  Поле ∝ силе тока I.",
            "  I > 0 → N справа, I < 0 → N слева.",
            "",
            "🧭 Компас:",
            "  Север стрелки указывает по полю B.",
        ]
        ly = iy + 45
        for line in info_lines:
            if line:
                self.canvas.create_text(panel_x + 35, ly, anchor="w",
                                        text=line, fill=TEXT_DIM,
                                        font=("Consolas", 9))
            ly += 14

    def _draw_slider(self, x, y, w, k, key, vmin, vmax, color,
                     center=False):
        bar_x0 = x
        bar_x1 = x + w
        bar_y = y
        bar_h = 12

        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, 6,
                   fill="#0f141c", outline="")

        # для знаковых — заполняем от центра
        if center:
            mid = (bar_x0 + bar_x1) / 2
            if k > 0.5:
                fill_x0 = mid
                fill_x1 = bar_x0 + w * k
                col_fill = NEON_RED
            else:
                fill_x0 = bar_x0 + w * k
                fill_x1 = mid
                col_fill = NEON_BLUE
            round_rect(self.canvas, fill_x0, bar_y - bar_h/2,
                       fill_x1, bar_y + bar_h/2, 6,
                       fill=col_fill, outline="")
            # метка центра
            self.canvas.create_line(mid, bar_y - 14, mid, bar_y + 14,
                                    fill="#ffffff", width=1)
        else:
            k = max(0.0, min(1.0, k))
            if k > 0.005:
                round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                           bar_x0 + w * k, bar_y + bar_h/2,
                           6, fill=color, outline="")

        cx_ = bar_x0 + w * k
        self.canvas.create_oval(cx_ - 11, bar_y - 11,
                                cx_ + 11, bar_y + 11,
                                fill="#ffffff", outline=color, width=2)

        self.slider_zones[key] = (bar_x0 - 10, bar_y - 16,
                                    bar_x1 + 10, bar_y + 16,
                                    vmin, vmax)

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

    def _draw_a_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.75),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Segoe UI", 11, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

    def _draw_p_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 6,
                   fill=lerp(color, BG_DEEP, 0.82),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Segoe UI", 8, "bold"))
        self.btn_zones[f"preset_{key}"] = (x, y, x + w, y + h)

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

        # объекты в сцене
        self._try_drag_object(x, y)

    def _try_drag_object(self, mx, my):
        if not hasattr(self, "scene_rect"):
            return
        gx0, gy0, gw, gh = self.scene_rect

        # проверяем компасы
        for c in self.state.compasses:
            cpx = gx0 + c.x * gw
            cpy = gy0 + c.y * gh
            if math.hypot(mx - cpx, my - cpy) < c.r + 8:
                c.dragging = True
                self.dragging_object = c
                return

        # проверяем магниты
        for m in self.state.magnets:
            mpx = gx0 + m.x * gw
            mpy = gy0 + m.y * gh
            if m.contains_point(mx, my, margin=10):
                m.dragging = True
                self.dragging_object = m
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
        nx = max(0.02, min(0.98, (event.x - gx0) / gw))
        ny = max(0.02, min(0.98, (event.y - gy0) / gh))
        self.dragging_object.x = nx
        self.dragging_object.y = ny

    def _on_release(self, event):
        self.drag_slider = None
        if self.dragging_object:
            if hasattr(self.dragging_object, "dragging"):
                self.dragging_object.dragging = False
            self.dragging_object = None

    def _on_right_click(self, event):
        """ПКМ — удалить объект под курсором."""
        if not hasattr(self, "scene_rect"):
            return
        gx0, gy0, gw, gh = self.scene_rect
        mx, my = event.x, event.y

        # компасы
        for c in list(self.state.compasses):
            cpx = gx0 + c.x * gw
            cpy = gy0 + c.y * gh
            if math.hypot(mx - cpx, my - cpy) < c.r + 5:
                self.state.compasses.remove(c)
                return

        # магниты
        for m in list(self.state.magnets):
            if m.contains_point(mx, my, margin=5):
                self.state.magnets.remove(m)
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
        if key == "current" and self.state.electromagnet:
            self.state.electromagnet.current = val

    def _do_action(self, key):
        if key.startswith("toggle_"):
            name = key[7:]
            if name == "field_lines":
                self.state.show_field_lines = not self.state.show_field_lines
            elif name == "field_vectors":
                self.state.show_field_vectors = not self.state.show_field_vectors
            elif name == "grid":
                self.state.show_grid = not self.state.show_grid
        elif key == "add_magnet":
            self.state.add_magnet()
        elif key == "add_compass":
            self.state.add_compass()
        elif key.startswith("preset_"):
            preset = key[7:]
            self._apply_preset(preset)

    def _apply_preset(self, name):
        if name == "empty":
            self.state.magnets = []
            self.state.compasses = []
            self.state.electromagnet = None
        elif name == "attract":
            # два разноимённых полюса напротив друг друга
            self.state.magnets = [
                Magnet(0.30, 0.5, 140, 45, 0, 1.0),
                Magnet(0.70, 0.5, 140, 45, 0, 1.0),
            ]
            self.state.electromagnet = None
            self.state.compasses = []
        elif name == "repel":
            # два N-полюса напротив друг друга
            self.state.magnets = [
                Magnet(0.30, 0.5, 140, 45, math.pi, 1.0),  # N влево
                Magnet(0.70, 0.5, 140, 45, 0, 1.0),         # N вправо
            ]
            self.state.electromagnet = None
            self.state.compasses = []
        elif name == "coil":
            self.state.magnets = []
            self.state.compasses = [
                Compass(0.3, 0.5, 24),
                Compass(0.5, 0.5, 24),
                Compass(0.7, 0.5, 24),
            ]
            em = Electromagnet(0.5, 0.5, 160, 50, math.pi/2)
            em.current = 1.5
            self.state.electromagnet = em

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