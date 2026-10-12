"""
ОКФРС. Практика 7. Задание 8.
Симуляция электромагнитного поля (ЭМП) — расширенная версия:
провод с током, катушка, магнит, заряд в поле, индукция.
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
# ИСТОЧНИКИ ПОЛЯ
# ============================================================
class Wire:
    """Прямой провод с током (для поля B)."""
    def __init__(self, x, y, angle=0, length=400):
        self.x = x
        self.y = y
        self.angle = angle      # в радианах
        self.length = length
        self.current = 1.0      # сила тока, А
        self.dragging = False

    def field_at(self, px, py):
        """Поле бесконечного прямого провода: B = μ₀I/2πr, направление ⊥ проводу."""
        # вектор от провода до точки
        dx = px - self.x
        dy = py - self.y
        r2 = dx * dx + dy * dy
        r = math.sqrt(r2)
        if r < 10:
            r = 10
            r2 = 100
        # B = k*I/r, направление — тангенциальное
        # перпендикуляр к вектору (dx, dy) → (-dy, dx) или (dy, -dx)
        # по правилу правой руки — при токе "вверх" поле идёт по окружности
        b = 3000 * self.current / r2
        # вектор перпендикулярный
        bx = -dy * b
        by = dx * b
        return bx, by

    def contains_point(self, mx, my, margin=15):
        # расстояние от точки до отрезка провода
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        dx = mx - self.x
        dy = my - self.y
        lx = dx * ca + dy * sa
        ly = -dx * sa + dy * ca
        return abs(lx) <= self.length / 2 + margin and abs(ly) <= margin


class Magnet:
    """Полосовой магнит."""
    def __init__(self, x, y, length=140, width=40, angle=0, strength=1.0):
        self.x = x
        self.y = y
        self.length = length
        self.width = width
        self.angle = angle
        self.strength = strength
        self.dragging = False

    def poles(self):
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        half = self.length / 2
        nx = self.x + half * ca
        ny = self.y + half * sa
        sx = self.x - half * ca
        sy = self.y - half * sa
        return (nx, ny), (sx, sy)

    def field_at(self, px, py):
        (nx, ny), (sx, sy) = self.poles()
        bx, by = 0, 0
        dx, dy = px - nx, py - ny
        r = max(math.hypot(dx, dy), 14)
        b = self.strength * 12000 / (r * r)
        bx += b * dx / r
        by += b * dy / r
        dx, dy = px - sx, py - sy
        r = max(math.hypot(dx, dy), 14)
        b = self.strength * 12000 / (r * r)
        bx -= b * dx / r
        by -= b * dy / r
        return bx, by

    def contains_point(self, mx, my, margin=10):
        dx = mx - self.x
        dy = my - self.y
        ca = math.cos(-self.angle)
        sa = math.sin(-self.angle)
        lx = dx * ca - dy * sa
        ly = dx * sa + dy * ca
        return abs(lx) <= self.length / 2 + margin and \
               abs(ly) <= self.width / 2 + margin


class Coil:
    """Катушка с током (создаёт поле как магнит)."""
    def __init__(self, x, y, length=140, width=50, angle=0):
        self.x = x
        self.y = y
        self.length = length
        self.width = width
        self.angle = angle
        self.current = 1.0
        self.turns = 6
        self.dragging = False

    def poles(self):
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        half = self.length / 2
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
        if abs(self.current) < 0.01:
            return 0, 0
        (nx, ny), (sx, sy) = self.poles()
        strength = self.current * 1.2
        bx, by = 0, 0
        dx, dy = px - nx, py - ny
        r = max(math.hypot(dx, dy), 14)
        b = strength * 12000 / (r * r)
        bx += b * dx / r
        by += b * dy / r
        dx, dy = px - sx, py - sy
        r = max(math.hypot(dx, dy), 14)
        b = strength * 12000 / (r * r)
        bx -= b * dx / r
        by -= b * dy / r
        return bx, by

    def contains_point(self, mx, my, margin=10):
        dx = mx - self.x
        dy = my - self.y
        ca = math.cos(-self.angle)
        sa = math.sin(-self.angle)
        lx = dx * ca - dy * sa
        ly = dx * sa + dy * ca
        return abs(lx) <= self.length / 2 + margin and \
               abs(ly) <= self.width / 2 + margin


class MovingCharge:
    """Заряженная частица, движется в поле."""
    def __init__(self, x, y, q=1.0, mass=1.0):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.q = q          # заряд
        self.mass = mass
        self.trail = []
        self.trail_max = 100
        self.dragging = False

    def contains_point(self, mx, my, r=12):
        return math.hypot(mx - self.x, my - self.y) <= r


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.wires = []
        self.magnets = []
        self.coils = []
        self.charges = []

        # глобальные параметры
        self.show_field = True
        self.show_field_lines = True
        self.show_field_vectors = True
        self.show_vectors = False   # отдельные векторы — детально
        self.show_compass = False
        self.show_grid = True

        self.field_strength = 1.0   # общий множитель
        self.time = 0.0
        self.paused = False

        # начальная сцена
        self.load_scene("wire")

    def total_field(self, px, py):
        bx, by = 0, 0
        k = self.field_strength
        for w in self.wires:
            fx, fy = w.field_at(px, py)
            bx += fx * k
            by += fy * k
        for m in self.magnets:
            fx, fy = m.field_at(px, py)
            bx += fx * k
            by += fy * k
        for c in self.coils:
            fx, fy = c.field_at(px, py)
            bx += fx * k
            by += fy * k
        return bx, by

    def load_scene(self, name):
        self.wires = []
        self.magnets = []
        self.coils = []
        self.charges = []

        if name == "wire":
            # прямой провод + 4 заряда, движущихся вокруг
            self.wires.append(Wire(0.5, 0.5, angle=math.pi/2, length=500))
            for _ in range(4):
                q = MovingCharge(random.uniform(0.2, 0.8),
                                  random.uniform(0.2, 0.8),
                                  q=random.choice([+1, -1]))
                q.vx = random.uniform(-1, 1)
                q.vy = random.uniform(-1, 1)
                self.charges.append(q)

        elif name == "dipole":
            # два разноимённых полюса
            self.magnets.append(Magnet(0.35, 0.5, 140, 40, 0, 1.0))
            self.magnets.append(Magnet(0.65, 0.5, 140, 40, math.pi, 1.0))

        elif name == "coil":
            # катушка с током
            c = Coil(0.5, 0.5, 160, 50, 0)
            c.current = 1.5
            self.coils.append(c)

        elif name == "attract_repel":
            # магнит + заряд
            self.magnets.append(Magnet(0.5, 0.4, 140, 40, 0, 1.0))
            self.charges.append(MovingCharge(0.5, 0.7, q=+1))

        elif name == "ring":
            # много магнитных моментов по кругу
            for i in range(6):
                a = 2 * math.pi * i / 6
                x = 0.5 + 0.25 * math.cos(a)
                y = 0.5 + 0.25 * math.sin(a)
                self.magnets.append(Magnet(x, y, 80, 25, a, 0.7))

    def tick(self, dt):
        if self.paused:
            return
        self.time += dt
        # движение зарядов в магнитном поле
        for q in self.charges:
            if q.dragging:
                continue
            # сила Лоренца: F = q·v × B
            # F = q·(v_y·B_z - 0, 0 - v_x·B_z)
            # в 2D магнитное поле B считается перпендикулярным плоскости
            # поэтому B_z влияет на движение в плоскости xy
            # но у нас поле от полюсов — это вектор в плоскости
            # упростим: сила F = q·(v × B) где B в 2D
            # F = q·(v_x·B_y - v_y·B_x) по оси z — не двигает
            # Правильно: F = q·v × B требует 3D
            # В 2D: поле от катушки/магнита перпендикулярно, но у нас нет Bz
            # сделаем упрощённо: сила от E, а B не влияет на движение
            # Более интересно: сила притяжения к полюсам магнита
            fx, fy = 0, 0
            for m in self.magnets:
                (nx, ny), (sx, sy) = m.poles()
                # от N — отталкивает (если q>0), от S — притягивает
                dx, dy = q.x - nx * 1.0, q.y - ny * 1.0
                r = max(math.hypot(dx, dy), 20)
                f = 200 * q.q * m.strength / (r * r)
                fx += f * dx / r
                fy += f * dy / r
                dx, dy = q.x - sx, q.y - sy
                r = max(math.hypot(dx, dy), 20)
                f = -200 * q.q * m.strength / (r * r)
                fx += f * dx / r
                fy += f * dy / r

            # скорость
            q.vx += fx * dt
            q.vy += fy * dt
            # затухание
            q.vx *= 0.995
            q.vy *= 0.995
            # движение
            q.x += q.vx * dt * 0.5
            q.y += q.vy * dt * 0.5

            # границы
            if q.x < 0.05: q.x = 0.05; q.vx = -q.vx * 0.8
            elif q.x > 0.95: q.x = 0.95; q.vx = -q.vx * 0.8
            if q.y < 0.05: q.y = 0.05; q.vy = -q.vy * 0.8
            elif q.y > 0.95: q.y = 0.95; q.vy = -q.vy * 0.8

            # трейл
            q.trail.append((q.x, q.y))
            if len(q.trail) > q.trail_max:
                q.trail.pop(0)

    def stats(self):
        return {
            "wires": len(self.wires),
            "magnets": len(self.magnets),
            "coils": len(self.coils),
            "charges": len(self.charges),
        }


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ EM Field · Электромагнитное поле")
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
        self.canvas.create_text(100, 40, text="EM FIELD",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(240, 44,
                                text="· ЭЛЕКТРОМАГНИТНОЕ ПОЛЕ · РАСШИРЕННОЕ",
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
                                text="ЛКМ — тащить · ПКМ — удалить · клик по пустому — создать заряд",
                                fill=TEXT_DIM, font=("Segoe UI", 9, "italic"))

        gx0 = x + 15
        gy0 = y + 40
        gx1 = x + scene_w - 15
        gy1 = y + h - 15
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

        # === ВЕКТОРЫ ПОЛЯ (сетка стрелок) ===
        if self.state.show_field_vectors:
            step = 55
            for sx in range(int(gx0) + step // 2, int(gx1), step):
                for sy in range(int(gy0) + step // 2, int(gy1), step):
                    bx, by = self.state.total_field(sx, sy)
                    mag = math.hypot(bx, by)
                    if mag < 1:
                        continue
                    max_len = 20
                    scale = min(max_len, mag) / mag
                    ex = bx * scale
                    ey = by * scale
                    col = lerp(NEON_PURP, BG_DEEP,
                               1 - min(mag / 100, 1.0) * 0.7)
                    self.canvas.create_line(sx, sy, sx + ex, sy + ey,
                                            fill=col, width=1)
                    self.canvas.create_oval(sx + ex - 2, sy + ey - 2,
                                            sx + ex + 2, sy + ey + 2,
                                            fill=col, outline="")

        # === СИЛОВЫЕ ЛИНИИ ===
        if self.state.show_field_lines:
            for m in self.state.magnets:
                (nx, ny), (sx, sy) = m.poles()
                npx, npy = gx0 + nx * gw, gy0 + ny * gh
                self._trace_field_line(npx, npy, gx0, gy0, gw, gh, +1)
            for c in self.state.coils:
                if abs(c.current) < 0.05:
                    continue
                (nx, ny), (sx, sy) = c.poles()
                npx, npy = gx0 + nx * gw, gy0 + ny * gh
                self._trace_field_line(npx, npy, gx0, gy0, gw, gh, +1)

        # === ПРОВОДА (с током) ===
        for w_ in self.state.wires:
            self._draw_wire(w_, gx0, gy0, gw, gh)

        # === МАГНИТЫ ===
        for m in self.state.magnets:
            self._draw_magnet(m, gx0, gy0, gw, gh)

        # === КАТУШКИ ===
        for c in self.state.coils:
            self._draw_coil(c, gx0, gy0, gw, gh)

        # === ДВИЖУЩИЕСЯ ЗАРЯДЫ ===
        for q in self.state.charges:
            self._draw_charge(q, gx0, gy0, gw, gh)

    def _trace_field_line(self, start_px, start_py, gx0, gy0, gw, gh,
                          sign=+1, max_steps=200, step=4):
        x, y = start_px, start_py
        bx, by = self.state.total_field(x, y)
        mag = math.hypot(bx, by)
        if mag < 0.01:
            return
        x += 14 * bx / mag
        y += 14 * by / mag
        path = [(x, y)]
        for _ in range(max_steps):
            bx, by = self.state.total_field(x, y)
            mag = math.hypot(bx, by)
            if mag < 0.01:
                break
            x += step * bx / mag * sign
            y += step * by / mag * sign
            path.append((x, y))
            if x < gx0 or x > gx0 + gw or y < gy0 or y > gy0 + gh:
                break
            hit = False
            for m in self.state.magnets:
                (nx, ny), (sx, sy) = m.poles()
                spx, spy = gx0 + sx * gw, gy0 + sy * gh
                if math.hypot(x - spx, y - spy) < 12:
                    hit = True
                    break
            if hit:
                break
        if len(path) >= 2:
            flat = []
            for (px, py) in path:
                flat.extend([px, py])
            self.canvas.create_line(*flat,
                                    fill=lerp(NEON_PURP, BG_DEEP, 0.55),
                                    width=1, smooth=True)

    def _draw_wire(self, w_, gx0, gy0, gw, gh):
        cx = gx0 + w_.x * gw
        cy = gy0 + w_.y * gh
        hl = w_.length / 2
        ca = math.cos(w_.angle)
        sa = math.sin(w_.angle)

        # концы
        x1 = cx - hl * ca
        y1 = cy - hl * sa
        x2 = cx + hl * ca
        y2 = cy + hl * sa

        # цвет по току (красный при большом, синий при малом)
        t = min(1.0, abs(w_.current) / 2.0)
        col = lerp("#2a2d38", NEON_AMBER, t) if w_.current > 0 \
              else lerp("#2a2d38", NEON_BLUE, t)

        # сам провод
        self.canvas.create_line(x1, y1, x2, y2,
                                fill=col, width=6, capstyle="round")
        self.canvas.create_line(x1, y1, x2, y2,
                                fill=lerp(col, "#ffffff", 0.5),
                                width=2, capstyle="round")

        # стрелки направления тока
        if abs(w_.current) > 0.1:
            for k in [-0.25, 0, 0.25]:
                mx = cx + k * w_.length * ca
                my = cy + k * w_.length * sa
                # направление
                sign = 1 if w_.current > 0 else -1
                ax = mx + 15 * ca * sign
                ay = my + 15 * sa * sign
                # стрелка — маленький треугольник
                perp_x = -sa * 5
                perp_y = ca * 5
                self.canvas.create_polygon(
                    ax, ay,
                    mx + perp_x, my + perp_y,
                    mx - perp_x, my - perp_y,
                    fill=NEON_RED, outline="")

        # подпись
        self.canvas.create_text(cx + 20 * sa, cy - 20 * ca,
                                text=f"I={w_.current:+.1f} А",
                                fill=col,
                                font=("Consolas", 10, "bold"))

        # выделение
        if w_.dragging:
            self.canvas.create_line(x1, y1, x2, y2,
                                    fill="#ffffff", width=1,
                                    dash=(4, 3))

    def _draw_magnet(self, m, gx0, gy0, gw, gh):
        cx = gx0 + m.x * gw
        cy = gy0 + m.y * gh
        length = m.length
        width = m.width
        ca = math.cos(m.angle)
        sa = math.sin(m.angle)

        def corner(dx, dy):
            return (cx + dx * ca - dy * sa,
                    cy + dx * sa + dy * ca)

        hl = length / 2
        hw = width / 2

        n_pts = [corner(0, -hw), corner(hl, -hw),
                  corner(hl, hw), corner(0, hw)]
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

        if m.dragging:
            self.canvas.create_polygon(n_pts, fill="", outline="#ffffff",
                                        width=2, dash=(4, 3))
            self.canvas.create_polygon(s_pts, fill="", outline="#ffffff",
                                        width=2, dash=(4, 3))

    def _draw_coil(self, c, gx0, gy0, gw, gh):
        cx = gx0 + c.x * gw
        cy = gy0 + c.y * gh
        length = c.length
        width = c.width
        ca = math.cos(c.angle)
        sa = math.sin(c.angle)

        def corner(dx, dy):
            return (cx + dx * ca - dy * sa,
                    cy + dx * sa + dy * ca)

        hl = length / 2
        hw = width / 2

        body = [corner(-hl, -hw), corner(hl, -hw),
                corner(hl, hw), corner(-hl, hw)]

        # тень
        self.canvas.create_polygon([(x + 3, y + 5) for (x, y) in body],
                                    fill="#000000", outline="")

        # корпус
        self.canvas.create_polygon(body,
                                    fill="#3a3d48",
                                    outline="#1a1c22", width=2)

        # витки
        for i in range(c.turns):
            t = (i + 0.5) / c.turns
            dx = -hl + t * length
            x1, y1 = corner(dx, -hw - 5)
            x2, y2 = corner(dx, hw + 5)
            col = NEON_AMBER if c.current > 0 else NEON_CYAN
            self.canvas.create_line(x1, y1, x2, y2, fill=col, width=3)

        # полюсы
        if abs(c.current) > 0.05:
            (nx, ny), (sx, sy) = c.poles()
            npx = gx0 + nx * gw
            npy = gy0 + ny * gh
            spx = gx0 + sx * gw
            spy = gy0 + sy * gh

            self.canvas.create_oval(npx - 14, npy - 14,
                                     npx + 14, npy + 14,
                                     fill=lerp(NEON_RED, BG_DEEP, 0.3),
                                     outline=NEON_RED, width=2)
            self.canvas.create_text(npx, npy, text="N",
                                    fill="#ffffff",
                                    font=("Consolas", 14, "bold"))
            self.canvas.create_oval(spx - 14, spy - 14,
                                     spx + 14, spy + 14,
                                     fill=lerp(NEON_BLUE, BG_DEEP, 0.3),
                                     outline=NEON_BLUE, width=2)
            self.canvas.create_text(spx, spy, text="S",
                                    fill="#ffffff",
                                    font=("Consolas", 14, "bold"))

    def _draw_charge(self, q, gx0, gy0, gw, gh):
        px = gx0 + q.x * gw
        py = gy0 + q.y * gh

        # трейл
        if len(q.trail) > 2:
            for i in range(1, len(q.trail)):
                t = i / len(q.trail)
                x0 = gx0 + q.trail[i-1][0] * gw
                y0 = gy0 + q.trail[i-1][1] * gh
                x1 = gx0 + q.trail[i][0] * gw
                y1 = gy0 + q.trail[i][1] * gh
                col = NEON_RED if q.q > 0 else NEON_BLUE
                col = lerp(BG_GRAPH, col, t * 0.6)
                self.canvas.create_line(x0, y0, x1, y1,
                                        fill=col, width=1)

        # свечение
        col = NEON_RED if q.q > 0 else NEON_BLUE
        for i in range(6, 0, -1):
            rr = 10 + i * 3
            self.canvas.create_oval(px - rr, py - rr, px + rr, py + rr,
                                    fill="", outline=lerp(col, BG_GRAPH,
                                                           1 - i / 8),
                                    width=1)

        # тело
        self.canvas.create_oval(px - 10, py - 10, px + 10, py + 10,
                                fill=col, outline="#ffffff", width=2)

        # знак
        text = "+" if q.q > 0 else "−"
        self.canvas.create_text(px, py, text=text,
                                fill="#ffffff",
                                font=("Consolas", 14, "bold"))

        # вектор скорости
        speed = math.hypot(q.vx, q.vy)
        if speed > 0.5:
            vx_end = px + q.vx * 15
            vy_end = py + q.vy * 15
            self.canvas.create_line(px, py, vx_end, vy_end,
                                     fill=lerp(col, "#ffffff", 0.6),
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
                                text="▸ СЦЕНАРИИ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # пресеты сцен
        scenes = [
            ("wire",    "ПРОВОД",     NEON_AMBER),
            ("dipole",  "ДИПОЛЬ",     NEON_PINK),
            ("coil",    "КАТУШКА",    NEON_CYAN),
            ("attract", "ПРИТЯЖ.",    NEON_GREEN),
            ("ring",    "КРУГ",       NEON_PURP),
        ]
        s_w = 68
        s_h = 36
        s_gap = 6

        for i, (key, label, color) in enumerate(scenes):
            bx = panel_x + 20 + i * (s_w + s_gap)
            self._draw_small_btn(bx, y + 50, s_w, s_h,
                                   f"scene_{key}", label, color)

        # === Ток провода ===
        if self.state.wires:
            wy = y + 110
            self.canvas.create_text(panel_x + 20, wy, anchor="w",
                                    text="ТОК ПРОВОДА (А):",
                                    fill=TEXT_DIM, font=FONT_LABEL_S)
            w_ = self.state.wires[0]
            self.canvas.create_text(panel_x + panel_w - 20, wy, anchor="e",
                                    text=f"{w_.current:+.1f}",
                                    fill=NEON_AMBER, font=FONT_MONO)
            self._draw_slider(panel_x + 20, wy + 25, panel_w - 40,
                               (w_.current + 3) / 6,
                               "wire_current", -3.0, 3.0, NEON_AMBER,
                               center=True)

        # === Общий множитель поля ===
        fy = y + 180
        self.canvas.create_text(panel_x + 20, fy, anchor="w",
                                text="СИЛА ПОЛЯ ×:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w - 20, fy, anchor="e",
                                text=f"{self.state.field_strength:.2f}",
                                fill=NEON_GREEN, font=FONT_MONO)
        self._draw_slider(panel_x + 20, fy + 25, panel_w - 40,
                           (self.state.field_strength - 0.2) / 2.8,
                           "field_strength", 0.2, 3.0, NEON_GREEN)

        # === Ток катушки (если есть) ===
        if self.state.coils:
            cy2 = y + 250
            self.canvas.create_text(panel_x + 20, cy2, anchor="w",
                                    text="ТОК КАТУШКИ (А):",
                                    fill=TEXT_DIM, font=FONT_LABEL_S)
            c = self.state.coils[0]
            self.canvas.create_text(panel_x + panel_w - 20, cy2, anchor="e",
                                    text=f"{c.current:+.1f}",
                                    fill=NEON_CYAN, font=FONT_MONO)
            self._draw_slider(panel_x + 20, cy2 + 25, panel_w - 40,
                               (c.current + 3) / 6,
                               "coil_current", -3.0, 3.0, NEON_CYAN,
                               center=True)

        # === Переключатели ===
        ty = y + 320
        self.canvas.create_text(panel_x + 20, ty, anchor="w",
                                text="ПОКАЗАТЬ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        toggles = [
            ("field_lines",   "СИЛОВЫЕ ЛИНИИ", NEON_PURP,
             self.state.show_field_lines),
            ("field_vectors", "ВЕКТОРЫ ПОЛЯ",  NEON_CYAN,
             self.state.show_field_vectors),
            ("grid",          "СЕТКА",         NEON_GREEN,
             self.state.show_grid),
        ]
        t_w = 175
        t_h = 36
        t_gap = 8
        cols = 2

        for i, (key, label, color, active) in enumerate(toggles):
            row = i // cols
            col = i % cols
            bx = panel_x + 20 + col * (t_w + t_gap)
            by = ty + 20 + row * (t_h + t_gap)
            self._draw_toggle_btn(bx, by, t_w, t_h,
                                    key, label, color, active)

        # === Статистика ===
        sty = y + 460
        stats = self.state.stats()

        round_rect(self.canvas, panel_x + 20, sty,
                   panel_x + panel_w - 20, sty + 150, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, sty + 22,
                                text="СОСТОЯНИЕ СИСТЕМЫ",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        lines = [
            ("Проводов",       f"{stats['wires']}",    NEON_AMBER),
            ("Магнитов",       f"{stats['magnets']}",  NEON_RED),
            ("Катушек",        f"{stats['coils']}",    NEON_CYAN),
            ("Зарядов",        f"{stats['charges']}",  NEON_GREEN),
            ("Время",          f"{self.state.time:.2f} с", NEON_PURP),
        ]

        for i, (label, value, color) in enumerate(lines):
            ly = sty + 50 + i * 20
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
                       "⏸ ПАУЗА" if not self.state.paused else "▶ ПУСК",
                       NEON_AMBER, "pause",
                       active=self.state.paused)
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "🎲 ДОБАВИТЬ ЗАРЯД", NEON_PURP, "add_charge")

    def _draw_slider(self, x, y, w, k, key, vmin, vmax, color,
                     center=False):
        bar_x0 = x
        bar_x1 = x + w
        bar_y = y
        bar_h = 10
        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, 5,
                   fill="#0f141c", outline="")

        k = max(0.0, min(1.0, k))

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
                       fill_x1, bar_y + bar_h/2, 5,
                       fill=col_fill, outline="")
            self.canvas.create_line(mid, bar_y - 14, mid, bar_y + 14,
                                    fill="#ffffff", width=1)
        else:
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

    def _draw_small_btn(self, x, y, w, h, key, label, color):
        round_rect(self.canvas, x, y, x + w, y + h, 6,
                   fill=lerp(color, BG_DEEP, 0.82),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=label, fill=color,
                                font=("Segoe UI", 8, "bold"))
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

        for key, (x0, y0, x1, y1, vmin, vmax) in self.slider_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.drag_slider = key
                self._set_slider_from_mouse(key, x)
                return

        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self._do_action(key)
                return

        if self._try_start_drag(x, y):
            return

    def _try_start_drag(self, mx, my):
        if not hasattr(self, "scene_rect"):
            return False
        gx0, gy0, gw, gh = self.scene_rect

        # заряды (верхний приоритет — они поверх)
        for q in reversed(self.state.charges):
            px = gx0 + q.x * gw
            py = gy0 + q.y * gh
            if q.contains_point(px and mx or mx, my, 15):
                if math.hypot(mx - px, my - py) < 15:
                    q.dragging = True
                    self.dragging_object = q
                    q.vx = 0
                    q.vy = 0
                    return True

        # катушки
        for c in self.state.coils:
            if c.contains_point(mx, my, 20):
                c.dragging = True
                self.dragging_object = c
                return True

        # магниты
        for m in self.state.magnets:
            if m.contains_point(mx, my, 15):
                m.dragging = True
                self.dragging_object = m
                return True

        # провода
        for w_ in self.state.wires:
            if w_.contains_point(mx, my, 20):
                w_.dragging = True
                self.dragging_object = w_
                return True

        # пустое место — создаём заряд
        if gx0 + 10 < mx < gx0 + gw - 10 and \
           gy0 + 10 < my < gy0 + gh - 10:
            nx = (mx - gx0) / gw
            ny = (my - gy0) / gh
            q = MovingCharge(nx, ny,
                             q=random.choice([+1, -1]))
            self.state.charges.append(q)
            return True

        return False

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
            if hasattr(self.dragging_object, "dragging"):
                self.dragging_object.dragging = False
            self.dragging_object = None

    def _on_right_click(self, event):
        if not hasattr(self, "scene_rect"):
            return
        gx0, gy0, gw, gh = self.scene_rect
        mx, my = event.x, event.y

        for q in list(self.state.charges):
            px = gx0 + q.x * gw
            py = gy0 + q.y * gh
            if math.hypot(mx - px, my - py) < 15:
                self.state.charges.remove(q)
                return
        for m in list(self.state.magnets):
            if m.contains_point(mx, my, 10):
                self.state.magnets.remove(m)
                return
        for c in list(self.state.coils):
            if c.contains_point(mx, my, 10):
                self.state.coils.remove(c)
                return
        for w_ in list(self.state.wires):
            if w_.contains_point(mx, my, 10):
                self.state.wires.remove(w_)
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
        if key == "wire_current" and self.state.wires:
            self.state.wires[0].current = val
        elif key == "field_strength":
            self.state.field_strength = val
        elif key == "coil_current" and self.state.coils:
            self.state.coils[0].current = val

    def _do_action(self, key):
        if key == "pause":
            self.state.paused = not self.state.paused
        elif key == "add_charge":
            if hasattr(self, "scene_rect"):
                gx0, gy0, gw, gh = self.scene_rect
                q = MovingCharge(random.uniform(0.3, 0.7),
                                  random.uniform(0.3, 0.7),
                                  q=random.choice([+1, -1]))
                q.vx = random.uniform(-1, 1)
                q.vy = random.uniform(-1, 1)
                self.state.charges.append(q)
        elif key.startswith("scene_"):
            scene = key[6:]
            mapping = {
                "wire": "wire",
                "dipole": "dipole",
                "coil": "coil",
                "attract": "attract_repel",
                "ring": "ring",
            }
            self.state.load_scene(mapping.get(scene, "wire"))
        elif key.startswith("toggle_"):
            name = key[7:]
            if name == "field_lines":
                self.state.show_field_lines = not self.state.show_field_lines
            elif name == "field_vectors":
                self.state.show_field_vectors = not self.state.show_field_vectors
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

        dt = min(0.033, now - self.last_time)
        self.last_time = now

        self.state.tick(dt)

        self._redraw_all()
        self.root.after(30, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()