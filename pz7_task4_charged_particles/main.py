"""
ОКФРС. Практика 7. Задание 4.
Модель движения заряженных частиц в разных средах:
металл · электролит · газ (плазма).
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
# СРЕДЫ
# ============================================================
# Параметры: (цвет фона, трение/вязкость, скорость дрейфа, коэффициент диффузии)
MEDIUMS = {
    "metal": {
        "name": "МЕТАЛЛ",
        "desc": "Свободные электроны в кристаллической решётке",
        "bg": "#0a0a18",
        "viscosity": 0.92,      # высокое трение (много столкновений)
        "drift_speed": 1.2,     # электроны дрейфуют
        "diffusion": 0.3,
        "particle_color": NEON_CYAN,
        "particle_type": "electron",
        "lattice": True,        # показать кристаллическую решётку
    },
    "electrolyte": {
        "name": "ЭЛЕКТРОЛИТ",
        "desc": "Ионы в растворе (соль, кислота, щёлочь)",
        "bg": "#0a0a16",
        "viscosity": 0.86,      # умеренное трение (жидкость)
        "drift_speed": 0.6,
        "diffusion": 0.6,
        "particle_color": NEON_GREEN,
        "particle_type": "ion",
        "lattice": False,
    },
    "gas": {
        "name": "ГАЗ / ПЛАЗМА",
        "desc": "Ионизированный газ — свободные ионы и электроны",
        "bg": "#100818",
        "viscosity": 0.99,      # минимальное трение
        "drift_speed": 2.5,
        "diffusion": 1.5,
        "particle_color": NEON_PURP,
        "particle_type": "mixed",
        "lattice": False,
    },
}


# ============================================================
# ЧАСТИЦА
# ============================================================
class Particle:
    def __init__(self, x, y, kind="electron"):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.kind = kind       # "electron" | "positive_ion" | "negative_ion"
        self.charge = 0
        if kind == "electron":
            self.charge = -1
        elif kind == "positive_ion":
            self.charge = +1
        elif kind == "negative_ion":
            self.charge = -1

        self.size = 3 if kind == "electron" else 5
        self.mass = 1.0 if kind == "electron" else 4.0

        # случайная начальная скорость (тепловое движение)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)

        self.trail = []        # след из последних точек
        self.trail_max = 25


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.medium = "metal"
        self.field_strength = 1.0     # напряжённость поля E (0..2)
        self.temperature = 1.0        # температура (влияет на диффузию)
        self.particles = []
        self.n_particles = 60

        self.paused = False
        self.pulse_t = 0.0

        self.spawn_particles()

    def get_medium(self):
        return MEDIUMS[self.medium]

    def spawn_particles(self):
        self.particles = []
        m = self.get_medium()
        for _ in range(self.n_particles):
            x = random.uniform(0.05, 0.95)
            y = random.uniform(0.05, 0.95)

            if m["particle_type"] == "electron":
                kind = "electron"
            elif m["particle_type"] == "ion":
                # ионы: 50% положительные, 50% отрицательные
                kind = random.choice(["positive_ion", "negative_ion"])
            else:  # mixed
                kind = random.choice(["electron", "positive_ion", "negative_ion"])

            self.particles.append(Particle(x, y, kind))

    def set_medium(self, medium):
        self.medium = medium
        self.spawn_particles()

    def tick(self, dt):
        self.pulse_t += dt

        if self.paused:
            return

        m = self.get_medium()
        E = self.field_strength

        for p in self.particles:
            # === сила от поля ===
            # F = q·E, положительный заряд → вправо, отрицательный → влево
            fx = p.charge * E * 0.01 / p.mass
            fy = 0

            # === тепловая диффузия ===
            diff = m["diffusion"] * self.temperature * 0.005
            fx += random.uniform(-diff, diff)
            fy += random.uniform(-diff, diff)

            # === вязкость (трение среды) ===
            p.vx = (p.vx + fx) * m["viscosity"]
            p.vy = (p.vy + fy) * m["viscosity"]

            # движение
            p.x += p.vx * dt * 20
            p.y += p.vy * dt * 20

            # отскок от границ
            if p.x < 0.02:
                p.x = 0.02
                p.vx = -p.vx * 0.9
            elif p.x > 0.98:
                p.x = 0.98
                p.vx = -p.vx * 0.9
            if p.y < 0.02:
                p.y = 0.02
                p.vy = -p.vy * 0.9
            elif p.y > 0.98:
                p.y = 0.98
                p.vy = -p.vy * 0.9

            # след
            p.trail.append((p.x, p.y))
            if len(p.trail) > p.trail_max:
                p.trail.pop(0)

    def stats(self):
        n_e = sum(1 for p in self.particles if p.kind == "electron")
        n_pi = sum(1 for p in self.particles if p.kind == "positive_ion")
        n_ni = sum(1 for p in self.particles if p.kind == "negative_ion")

        # средняя скорость
        avg_vx = sum(p.vx for p in self.particles) / max(1, len(self.particles))
        avg_vy = sum(p.vy for p in self.particles) / max(1, len(self.particles))

        # средняя кинетическая энергия
        ke = sum(p.mass * (p.vx ** 2 + p.vy ** 2) / 2
                  for p in self.particles) / max(1, len(self.particles))

        return {
            "n_electrons": n_e,
            "n_pos_ions": n_pi,
            "n_neg_ions": n_ni,
            "avg_vx": avg_vx,
            "avg_vy": avg_vy,
            "avg_ke": ke,
        }


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Charged Particles · Движение в разных средах")
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
        self.canvas.create_text(60, 40, text="⚡",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="CHARGED PARTICLES",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(390, 44,
                                text="· ДВИЖЕНИЕ В РАЗНЫХ СРЕДАХ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- СЦЕНА ----------
    def _draw_scene(self, x, y, w, h):
        panel_w = 400
        scene_w = w - 100 - panel_w - 20

        m = self.state.get_medium()

        round_rect(self.canvas, x, y, x + scene_w, y + h, 14,
                   fill=m["bg"], outline=BORDER, width=1)

        # верхняя подсказка
        self.canvas.create_text(x + scene_w / 2, y + 20,
                                text=f"{m['name']} · {m['desc']}",
                                fill=NEON_CYAN, font=FONT_LABEL)

        # === рабочая область ===
        gx0 = x + 20
        gy0 = y + 40
        gx1 = x + scene_w - 20
        gy1 = y + h - 40

        gw = gx1 - gx0
        gh = gy1 - gy0

        # --- кристаллическая решётка (для металла) ---
        if m["lattice"]:
            step = 55
            for i in range(int(gx0) + 20, int(gx1), step):
                for j in range(int(gy0) + 20, int(gy1), step):
                    self.canvas.create_oval(i - 3, j - 3, i + 3, j + 3,
                                            fill=lerp(NEON_AMBER, BG_DEEP, 0.6),
                                            outline="")
                    # маленькая связь
                    self.canvas.create_line(i, j, i + step, j,
                                            fill="#1a1428", width=1)
                    self.canvas.create_line(i, j, i, j + step,
                                            fill="#1a1428", width=1)

        # --- электроды при ненулевом поле ---
        E = self.state.field_strength
        if E > 0.05:
            # левый электрод (−)
            col_neg = lerp(NEON_BLUE, BG_DEEP, 0.3)
            self.canvas.create_rectangle(gx0, gy0 + 20,
                                          gx0 + 6, gy1 - 20,
                                          fill=col_neg, outline=NEON_BLUE)
            self.canvas.create_text(gx0 - 12, (gy0 + gy1) / 2,
                                    text="−", fill=NEON_BLUE,
                                    font=("Consolas", 22, "bold"))
            # правый электрод (+)
            col_pos = lerp(NEON_RED, BG_DEEP, 0.3)
            self.canvas.create_rectangle(gx1 - 6, gy0 + 20,
                                          gx1, gy1 - 20,
                                          fill=col_pos, outline=NEON_RED)
            self.canvas.create_text(gx1 + 12, (gy0 + gy1) / 2,
                                    text="+", fill=NEON_RED,
                                    font=("Consolas", 22, "bold"))

            # стрелки поля между электродами
            n_arrows = 5
            for i in range(n_arrows):
                ay = gy0 + (i + 1) * gh / (n_arrows + 1)
                self.canvas.create_line(gx0 + 15, ay, gx1 - 15, ay,
                                        fill=lerp(NEON_AMBER, BG_DEEP, 0.75),
                                        dash=(4, 6), width=1)
                # стрелка направления
                self.canvas.create_polygon(gx1 - 25, ay,
                                            gx1 - 35, ay - 4,
                                            gx1 - 35, ay + 4,
                                            fill=lerp(NEON_AMBER, BG_DEEP, 0.5))

        # --- частицы ---
        for p in self.state.particles:
            px = gx0 + p.x * gw
            py = gy0 + p.y * gh

            # цвет по типу
            if p.kind == "electron":
                col = NEON_CYAN
                glyph = "e⁻"
            elif p.kind == "positive_ion":
                col = NEON_RED
                glyph = "+"
            else:
                col = NEON_BLUE
                glyph = "−"

            # след
            if len(p.trail) > 2:
                flat = []
                for i, (tx, ty) in enumerate(p.trail):
                    tx_px = gx0 + tx * gw
                    ty_px = gy0 + ty * gh
                    flat.extend([tx_px, ty_px])
                # рисуем как polyline с уменьшающейся прозрачностью
                for i in range(1, len(p.trail)):
                    t = i / len(p.trail)
                    x0 = gx0 + p.trail[i-1][0] * gw
                    y0 = gy0 + p.trail[i-1][1] * gh
                    x1 = gx0 + p.trail[i][0] * gw
                    y1 = gy0 + p.trail[i][1] * gh
                    col_trail = lerp(m["bg"], col, t * 0.5)
                    self.canvas.create_line(x0, y0, x1, y1,
                                            fill=col_trail, width=1)

            # свечение
            glow_r = p.size * 4
            for i in range(4, 0, -1):
                r = glow_r + i * 2
                self.canvas.create_oval(px - r, py - r, px + r, py + r,
                                        fill="", outline=lerp(col, m["bg"], 1 - i / 5),
                                        width=1)

            # тело
            self.canvas.create_oval(px - p.size, py - p.size,
                                    px + p.size, py + p.size,
                                    fill=col, outline="#ffffff", width=1)

        # --- подписи по краям ---
        self.canvas.create_text(gx0 + 10, gy1 + 20, anchor="w",
                                text="− к +  (направление поля E)",
                                fill=TEXT_DIM,
                                font=("Segoe UI", 9, "italic"))
        self.canvas.create_text(gx1 - 10, gy1 + 20, anchor="e",
                                text="красные → движутся вправо · синие → влево",
                                fill=TEXT_DIM,
                                font=("Segoe UI", 9, "italic"))

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

        # === ВЫБОР СРЕДЫ ===
        self.canvas.create_text(panel_x + 20, y + 55, anchor="w",
                                text="СРЕДА:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        medium_btns = [
            ("metal",       "МЕТАЛЛ",       NEON_CYAN),
            ("electrolyte", "ЭЛЕКТРОЛИТ",   NEON_GREEN),
            ("gas",         "ГАЗ / ПЛАЗМА", NEON_PURP),
        ]

        m_btn_w = 115
        m_btn_h = 44
        m_gap = 8

        for i, (key, label, color) in enumerate(medium_btns):
            bx = panel_x + 20 + i * (m_btn_w + m_gap)
            active = (self.state.medium == key)
            self._draw_medium_btn(bx, y + 75, m_btn_w, m_btn_h,
                                    key, label, color, active)

        # === ОПИСАНИЕ СРЕДЫ ===
        info_y = y + 135
        m = self.state.get_medium()

        round_rect(self.canvas, panel_x + 20, info_y,
                   panel_x + panel_w - 20, info_y + 55, 8,
                   fill=BG_PANEL,
                   outline=lerp(m["particle_color"], BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + 30, info_y + 18, anchor="w",
                                text=f"● {m['name']}",
                                fill=m["particle_color"],
                                font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(panel_x + 30, info_y + 38, anchor="w",
                                text=m["desc"],
                                fill=TEXT_DIM,
                                font=("Segoe UI", 9))

        # === Ползунок напряжённости поля ===
        sy = y + 210

        self.canvas.create_text(panel_x + 20, sy, anchor="w",
                                text="НАПРЯЖЁННОСТЬ ПОЛЯ E:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        self.canvas.create_text(panel_x + panel_w - 20, sy, anchor="e",
                                text=f"{self.state.field_strength:.2f}",
                                fill=NEON_AMBER, font=FONT_MONO)

        self._draw_slider(panel_x + 20, sy + 30, panel_w - 40,
                           self.state.field_strength / 2.0,
                           "field_strength", 0.0, 2.0,
                           NEON_AMBER)

        # === Ползунок температуры ===
        sy2 = y + 290

        self.canvas.create_text(panel_x + 20, sy2, anchor="w",
                                text="ТЕМПЕРАТУРА (диффузия):",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        self.canvas.create_text(panel_x + panel_w - 20, sy2, anchor="e",
                                text=f"{self.state.temperature:.2f}",
                                fill=NEON_PINK, font=FONT_MONO)

        self._draw_slider(panel_x + 20, sy2 + 30, panel_w - 40,
                           self.state.temperature / 3.0,
                           "temperature", 0.0, 3.0,
                           NEON_PINK)

        # === Ползунок количества частиц ===
        sy3 = y + 370

        self.canvas.create_text(panel_x + 20, sy3, anchor="w",
                                text="КОЛИЧЕСТВО ЧАСТИЦ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        self.canvas.create_text(panel_x + panel_w - 20, sy3, anchor="e",
                                text=f"{len(self.state.particles)}",
                                fill=NEON_GREEN, font=FONT_MONO)

        self._draw_slider(panel_x + 20, sy3 + 30, panel_w - 40,
                           (len(self.state.particles) - 10) / 140.0,
                           "n_particles", 10, 150,
                           NEON_GREEN)

        # === СТАТИСТИКА ===
        stat_y = y + 455
        stats = self.state.stats()

        round_rect(self.canvas, panel_x + 20, stat_y,
                   panel_x + panel_w - 20, stat_y + 175, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, stat_y + 22,
                                text="СТАТИСТИКА",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        lines = [
            ("Электронов",     f"{stats['n_electrons']}",     NEON_CYAN),
            ("+ Ионов",        f"{stats['n_pos_ions']}",      NEON_RED),
            ("− Ионов",        f"{stats['n_neg_ions']}",      NEON_BLUE),
            ("Ср. скорость Vx", f"{stats['avg_vx']:+.3f}",     NEON_AMBER),
            ("Ср. кин. энергия", f"{stats['avg_ke']:.4f}",     NEON_PINK),
        ]

        for i, (label, value, color) in enumerate(lines):
            ly = stat_y + 50 + i * 24
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
                       "⏸ ПАУЗА" if not self.state.paused else "▶ ЗАПУСК",
                       NEON_AMBER, "pause",
                       active=self.state.paused)
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "↺ ПЕРЕСОЗДАТЬ", NEON_PURP, "respawn")

    def _draw_slider(self, x, y, w, k, key, vmin, vmax, color):
        bar_x0 = x
        bar_x1 = x + w
        bar_y = y
        bar_h = 12

        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, 6,
                   fill="#0f141c", outline="")

        k = max(0.0, min(1.0, k))
        if k > 0.005:
            round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                       bar_x0 + (bar_x1 - bar_x0) * k, bar_y + bar_h/2,
                       6, fill=color, outline="")

        cx_ = bar_x0 + (bar_x1 - bar_x0) * k
        self.canvas.create_oval(cx_ - 11, bar_y - 11,
                                cx_ + 11, bar_y + 11,
                                fill="#ffffff", outline=color, width=2)

        self.slider_zones[key] = (bar_x0 - 10, bar_y - 16,
                                    bar_x1 + 10, bar_y + 16,
                                    vmin, vmax)

        # деления
        for j in range(5):
            kk = j / 4
            xx = bar_x0 + (bar_x1 - bar_x0) * kk
            self.canvas.create_line(xx, bar_y + 14, xx, bar_y + 18,
                                    fill=TEXT_DIM, width=1)

    def _draw_medium_btn(self, x, y, w, h, key, label, color, active):
        if active:
            for i in range(4, 0, -1):
                round_rect(self.canvas, x - i, y - i,
                           x + w + i, y + h + i, 8 + i,
                           outline=lerp(color, BG_DEEP, i / 5), width=1)
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(color, BG_DEEP, 0.6),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Segoe UI", 10, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 10, "bold"))
        self.btn_zones[f"medium_{key}"] = (x, y, x + w, y + h)

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

    def _on_drag(self, event):
        if self.drag_slider:
            self._set_slider_from_mouse(self.drag_slider, event.x)

    def _on_release(self, event):
        self.drag_slider = None

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

        if key == "field_strength":
            self.state.field_strength = val
        elif key == "temperature":
            self.state.temperature = val
        elif key == "n_particles":
            new_n = int(val)
            if new_n != self.state.n_particles:
                self.state.n_particles = new_n
                self.state.spawn_particles()

    def _do_action(self, key):
        if key == "pause":
            self.state.paused = not self.state.paused
        elif key == "respawn":
            self.state.spawn_particles()
        elif key.startswith("medium_"):
            medium = key[7:]
            self.state.set_medium(medium)

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