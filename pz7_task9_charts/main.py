"""
ОКФРС. Практика 7. Задание 9.
Chart-компонент для построения диаграмм:
столбчатые, круговые, линейные, областные, точечные, кольцевые.
Исследование возможностей компонента.
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
NEON_ORANGE= "#ff8c42"

# палитра для диаграмм
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
FONT_BIG   = ("Consolas", 22, "bold")


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
# ТИПЫ ДИАГРАММ
# ============================================================
CHART_TYPES = [
    ("bar",       "СТОЛБЧАТАЯ",   "bar"),
    ("hbar",      "ГОРИЗОНТ.",    "hbar"),
    ("pie",       "КРУГОВАЯ",     "pie"),
    ("donut",     "КОЛЬЦЕВАЯ",    "donut"),
    ("line",      "ЛИНЕЙНАЯ",     "line"),
    ("area",      "ОБЛАСТЬ",      "area"),
    ("scatter",   "ТОЧЕЧНАЯ",     "scatter"),
    ("radar",     "РАДАР",        "radar"),
    ("stacked",   "С НАКОПЛ.",    "stacked"),
]


# ============================================================
# ДИАГРАММЫ (функции отрисовки)
# ============================================================
def draw_bar_chart(canvas, x, y, w, h, data, labels, colors):
    """Вертикальные столбцы."""
    pad_l = 55
    pad_r = 20
    pad_t = 30
    pad_b = 50
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = max(data) if data else 1
    n = len(data)
    if n == 0:
        return

    bar_w = (gx1 - gx0) / n * 0.7
    step = (gx1 - gx0) / n

    # сетка по Y
    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = k * max_v
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=FONT_MONO_S)

    # столбцы
    for i, v in enumerate(data):
        bx = gx0 + i * step + (step - bar_w) / 2
        by_top = gy1 - (v / max_v) * (gy1 - gy0)
        col = colors[i % len(colors)]

        # свечение
        canvas.create_rectangle(bx - 2, by_top - 2,
                                 bx + bar_w + 2, gy1 + 2,
                                 fill="", outline=lerp(col, BG_GRAPH, 0.7),
                                 width=1)
        # тело
        canvas.create_rectangle(bx, by_top, bx + bar_w, gy1,
                                 fill=col, outline=lerp(col, "#ffffff", 0.3),
                                 width=1)
        # блик
        canvas.create_rectangle(bx + 2, by_top + 2,
                                 bx + bar_w - 2, by_top + 6,
                                 fill=lerp(col, "#ffffff", 0.5), outline="")

        # значение сверху
        canvas.create_text(bx + bar_w / 2, by_top - 10,
                           text=f"{v:.1f}",
                           fill=col, font=FONT_MONO_S)

        # подпись
        canvas.create_text(bx + bar_w / 2, gy1 + 15,
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    # оси
    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


def draw_hbar_chart(canvas, x, y, w, h, data, labels, colors):
    """Горизонтальные столбцы."""
    pad_l = 90
    pad_r = 60
    pad_t = 30
    pad_b = 30
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = max(data) if data else 1
    n = len(data)
    if n == 0:
        return

    bar_h = (gy1 - gy0) / n * 0.7
    step = (gy1 - gy0) / n

    # сетка по X
    for i in range(6):
        k = i / 5
        xx = gx0 + k * (gx1 - gx0)
        val = k * max_v
        canvas.create_line(xx, gy0, xx, gy1,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(xx, gy1 + 15,
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=FONT_MONO_S)

    # столбцы
    for i, v in enumerate(data):
        by = gy0 + i * step + (step - bar_h) / 2
        bx_right = gx0 + (v / max_v) * (gx1 - gx0)
        col = colors[i % len(colors)]

        canvas.create_rectangle(gx0, by, bx_right, by + bar_h,
                                 fill=col,
                                 outline=lerp(col, "#ffffff", 0.3),
                                 width=1)
        canvas.create_rectangle(gx0 + 2, by + 2, bx_right - 2, by + 5,
                                 fill=lerp(col, "#ffffff", 0.5), outline="")

        canvas.create_text(bx_right + 10, by + bar_h / 2,
                           text=f"{v:.1f}", anchor="w",
                           fill=col, font=FONT_MONO_S)

        canvas.create_text(gx0 - 8, by + bar_h / 2, anchor="e",
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


def draw_pie_chart(canvas, x, y, w, h, data, labels, colors):
    """Круговая диаграмма."""
    total = sum(data) if data else 1
    cx = x + w / 2
    cy = y + h / 2 - 10
    r = min(w, h) * 0.32

    # тень под кругом
    canvas.create_oval(cx - r + 4, cy - r + 6, cx + r + 4, cy + r + 6,
                       fill="#000000", outline="")

    angle_start = 90
    for i, v in enumerate(data):
        extent = -(v / total) * 360
        col = colors[i % len(colors)]

        canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                          start=angle_start, extent=extent,
                          fill=col,
                          outline=lerp(col, "#ffffff", 0.3),
                          width=2)

        # процент в центре сектора
        mid_angle = math.radians(angle_start + extent / 2)
        tx = cx + r * 0.65 * math.cos(mid_angle)
        ty = cy - r * 0.65 * math.sin(mid_angle)
        pct = v / total * 100
        if pct > 5:
            canvas.create_text(tx, ty, text=f"{pct:.0f}%",
                               fill="#ffffff",
                               font=("Consolas", 10, "bold"))

        angle_start += extent

    # легенда снизу
    legend_y = y + h - 30
    n = len(data)
    if n > 0:
        item_w = min(90, (w - 20) / n)
        total_w = item_w * n
        start_x = x + (w - total_w) / 2
        for i in range(n):
            lx = start_x + i * item_w
            col = colors[i % len(colors)]
            canvas.create_rectangle(lx, legend_y - 5,
                                     lx + 14, legend_y + 9,
                                     fill=col, outline="")
            canvas.create_text(lx + 20, legend_y + 2, anchor="w",
                               text=labels[i] if i < len(labels) else str(i),
                               fill=TEXT_DIM, font=("Consolas", 8))


def draw_donut_chart(canvas, x, y, w, h, data, labels, colors):
    """Кольцевая."""
    total = sum(data) if data else 1
    cx = x + w / 2
    cy = y + h / 2 - 10
    r_out = min(w, h) * 0.32
    r_in = r_out * 0.55

    angle_start = 90
    for i, v in enumerate(data):
        extent = -(v / total) * 360
        col = colors[i % len(colors)]

        # используем толстую дугу
        canvas.create_arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                          start=angle_start, extent=extent,
                          style="arc",
                          outline=col,
                          width=int(r_out - r_in))

        # тонкая обводка цветом
        canvas.create_arc(cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                          start=angle_start, extent=extent,
                          style="arc",
                          outline=lerp(col, "#ffffff", 0.3),
                          width=2)

        angle_start += extent

    # процент в центре для каждого — вычислим
    angle_start = 90
    for i, v in enumerate(data):
        extent = -(v / total) * 360
        mid = math.radians(angle_start + extent / 2)
        rm = (r_out + r_in) / 2
        tx = cx + rm * math.cos(mid)
        ty = cy - rm * math.sin(mid)
        pct = v / total * 100
        if pct > 7:
            canvas.create_text(tx, ty, text=f"{pct:.0f}%",
                               fill="#ffffff",
                               font=("Consolas", 10, "bold"))
        angle_start += extent

    # центральное значение
    canvas.create_text(cx, cy, text=f"{total:.0f}",
                       fill=NEON_CYAN, font=("Consolas", 24, "bold"))
    canvas.create_text(cx, cy + 25, text="ВСЕГО",
                       fill=TEXT_DIM, font=("Consolas", 9))

    # легенда
    legend_y = y + h - 30
    n = len(data)
    if n > 0:
        item_w = min(90, (w - 20) / n)
        total_w = item_w * n
        start_x = x + (w - total_w) / 2
        for i in range(n):
            lx = start_x + i * item_w
            col = colors[i % len(colors)]
            canvas.create_rectangle(lx, legend_y - 5,
                                     lx + 14, legend_y + 9,
                                     fill=col, outline="")
            canvas.create_text(lx + 20, legend_y + 2, anchor="w",
                               text=labels[i] if i < len(labels) else str(i),
                               fill=TEXT_DIM, font=("Consolas", 8))


def draw_line_chart(canvas, x, y, w, h, data, labels, colors):
    """Линейный график."""
    pad_l = 55
    pad_r = 25
    pad_t = 30
    pad_b = 50
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = max(data) if data else 1
    n = len(data)
    if n == 0:
        return

    # сетка
    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = k * max_v
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=FONT_MONO_S)

    # точки
    step = (gx1 - gx0) / max(1, n - 1)
    pts = []
    for i, v in enumerate(data):
        px = gx0 + i * step
        py = gy1 - (v / max_v) * (gy1 - gy0)
        pts.append((px, py))

    # область под графиком
    area_pts = [(gx0, gy1)] + pts + [(gx1, gy1)]
    flat_area = []
    for (px, py) in area_pts:
        flat_area.extend([px, py])
    canvas.create_polygon(flat_area,
                          fill=lerp(colors[0], BG_GRAPH, 0.7),
                          outline="")

    # линия
    if len(pts) >= 2:
        flat = []
        for (px, py) in pts:
            flat.extend([px, py])
        canvas.create_line(*flat,
                           fill=lerp(colors[0], BG_GRAPH, 0.5),
                           width=6, smooth=True)
        canvas.create_line(*flat, fill=colors[0], width=2, smooth=True)

    # точки
    for i, (px, py) in enumerate(pts):
        col = colors[i % len(colors)]
        canvas.create_oval(px - 6, py - 6, px + 6, py + 6,
                           fill=col, outline="#ffffff", width=2)
        canvas.create_text(px, py - 14,
                           text=f"{data[i]:.1f}",
                           fill=col, font=FONT_MONO_S)

    # подписи
    for i, v in enumerate(data):
        px = gx0 + i * step
        canvas.create_text(px, gy1 + 15,
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


def draw_area_chart(canvas, x, y, w, h, data, labels, colors):
    """Диаграмма с областями (несколько рядов)."""
    pad_l = 55
    pad_r = 25
    pad_t = 30
    pad_b = 50
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = max(data) if data else 1
    n = len(data)
    if n == 0:
        return

    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = k * max_v
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=FONT_MONO_S)

    step = (gx1 - gx0) / max(1, n - 1)

    # область
    pts = [(gx0, gy1)]
    for i, v in enumerate(data):
        px = gx0 + i * step
        py = gy1 - (v / max_v) * (gy1 - gy0)
        pts.append((px, py))
    pts.append((gx1, gy1))

    flat = []
    for (px, py) in pts:
        flat.extend([px, py])

    canvas.create_polygon(flat,
                          fill=lerp(colors[0], BG_GRAPH, 0.5),
                          outline=colors[0], width=2)

    # верхняя линия
    line_pts = pts[1:-1]
    if len(line_pts) >= 2:
        flat2 = []
        for (px, py) in line_pts:
            flat2.extend([px, py])
        canvas.create_line(*flat2, fill=colors[0], width=3, smooth=True)

    # подписи
    for i, v in enumerate(data):
        px = gx0 + i * step
        canvas.create_text(px, gy1 + 15,
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


def draw_scatter_chart(canvas, x, y, w, h, data, labels, colors):
    """Точечная диаграмма."""
    pad_l = 55
    pad_r = 25
    pad_t = 30
    pad_b = 50
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    max_v = max(data) if data else 1
    n = len(data)
    if n == 0:
        return

    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = k * max_v
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=FONT_MONO_S)

    step = (gx1 - gx0) / max(1, n - 1)

    for i, v in enumerate(data):
        px = gx0 + i * step
        py = gy1 - (v / max_v) * (gy1 - gy0)
        col = colors[i % len(colors)]

        # свечение
        for j in range(4, 0, -1):
            rr = 6 + j * 2
            canvas.create_oval(px - rr, py - rr, px + rr, py + rr,
                               fill="", outline=lerp(col, BG_GRAPH,
                                                      1 - j / 5),
                               width=1)
        # тело
        canvas.create_oval(px - 8, py - 8, px + 8, py + 8,
                           fill=col, outline="#ffffff", width=2)
        # подпись
        canvas.create_text(px, py - 18, text=f"{v:.1f}",
                           fill=col, font=FONT_MONO_S)
        canvas.create_text(px, gy1 + 15,
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


def draw_radar_chart(canvas, x, y, w, h, data, labels, colors):
    """Радар (паутина)."""
    cx = x + w / 2
    cy = y + h / 2
    r = min(w, h) * 0.32

    max_v = max(data) if data else 1
    n = len(data)
    if n < 3:
        return

    # сетка — окружности уровней
    for k in [0.2, 0.4, 0.6, 0.8, 1.0]:
        rr = r * k
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n - math.pi / 2
            pts.extend([cx + rr * math.cos(a), cy + rr * math.sin(a)])
        pts.extend([pts[0], pts[1]])
        canvas.create_line(*pts,
                           fill="#1a2540", width=1)

    # лучи
    for i in range(n):
        a = 2 * math.pi * i / n - math.pi / 2
        ex = cx + r * math.cos(a)
        ey = cy + r * math.sin(a)
        canvas.create_line(cx, cy, ex, ey,
                           fill="#1a2540", width=1)
        # подписи на концах
        tx = cx + (r + 18) * math.cos(a)
        ty = cy + (r + 18) * math.sin(a)
        canvas.create_text(tx, ty,
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    # сам радар
    pts = []
    for i, v in enumerate(data):
        a = 2 * math.pi * i / n - math.pi / 2
        rr = r * (v / max_v)
        pts.extend([cx + rr * math.cos(a), cy + rr * math.sin(a)])

    if len(pts) >= 6:
        pts.extend([pts[0], pts[1]])
        canvas.create_polygon(pts[:-2],
                              fill=lerp(colors[0], BG_GRAPH, 0.6),
                              outline=colors[0], width=2)
        # вершины
        for i in range(0, len(pts) - 2, 2):
            px, py = pts[i], pts[i + 1]
            canvas.create_oval(px - 5, py - 5, px + 5, py + 5,
                               fill=colors[0], outline="#ffffff", width=2)


def draw_stacked_chart(canvas, x, y, w, h, data, labels, colors):
    """С накоплением — две серии."""
    pad_l = 55
    pad_r = 25
    pad_t = 30
    pad_b = 50
    gx0 = x + pad_l
    gy0 = y + pad_t
    gx1 = x + w - pad_r
    gy1 = y + h - pad_b

    # data — одна серия, но разделим на две части
    n = len(data)
    if n == 0:
        return

    # вторая серия — производная
    data2 = [v * random.uniform(0.3, 0.6) for v in data]
    max_v = max([a + b for a, b in zip(data, data2)])

    step = (gx1 - gx0) / n
    bar_w = step * 0.7

    for i in range(6):
        k = i / 5
        yy = gy1 - k * (gy1 - gy0)
        val = k * max_v
        canvas.create_line(gx0, yy, gx1, yy,
                           fill="#1a2540", dash=(2, 4), width=1)
        canvas.create_text(gx0 - 8, yy, anchor="e",
                           text=f"{val:.0f}",
                           fill=TEXT_DIM, font=FONT_MONO_S)

    for i in range(n):
        bx = gx0 + i * step + (step - bar_w) / 2
        v1 = data[i]
        v2 = data2[i]

        h1 = (v1 / max_v) * (gy1 - gy0)
        h2 = (v2 / max_v) * (gy1 - gy0)

        # нижняя часть
        canvas.create_rectangle(bx, gy1 - h1, bx + bar_w, gy1,
                                 fill=colors[0],
                                 outline=lerp(colors[0], "#ffffff", 0.3),
                                 width=1)
        # верхняя часть
        canvas.create_rectangle(bx, gy1 - h1 - h2,
                                 bx + bar_w, gy1 - h1,
                                 fill=colors[1],
                                 outline=lerp(colors[1], "#ffffff", 0.3),
                                 width=1)

        # сумма
        canvas.create_text(bx + bar_w / 2, gy1 - h1 - h2 - 10,
                           text=f"{v1 + v2:.1f}",
                           fill=NEON_AMBER, font=FONT_MONO_S)
        canvas.create_text(bx + bar_w / 2, gy1 + 15,
                           text=labels[i] if i < len(labels) else str(i),
                           fill=TEXT_DIM, font=("Consolas", 9))

    canvas.create_line(gx0, gy0, gx0, gy1, fill=NEON_AMBER, width=2)
    canvas.create_line(gx0, gy1, gx1, gy1, fill=NEON_AMBER, width=2)


DRAW_FUNCS = {
    "bar":     draw_bar_chart,
    "hbar":    draw_hbar_chart,
    "pie":     draw_pie_chart,
    "donut":   draw_donut_chart,
    "line":    draw_line_chart,
    "area":    draw_area_chart,
    "scatter": draw_scatter_chart,
    "radar":   draw_radar_chart,
    "stacked": draw_stacked_chart,
}


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        # текущий тип
        self.chart_type = "bar"

        # данные
        self.data = []
        self.labels = []
        self.colors = list(CHART_COLORS)

        # режим данных
        self.data_mode = "random"   # random | linear | sine | custom

        self.regenerate_data()

    def regenerate_data(self):
        n = random.randint(5, 8)
        self.labels = [f"К{i+1}" for i in range(n)]

        if self.data_mode == "random":
            self.data = [random.uniform(10, 100) for _ in range(n)]
        elif self.data_mode == "linear":
            self.data = [10 + i * (80 / max(1, n-1)) for i in range(n)]
        elif self.data_mode == "sine":
            self.data = [50 + 45 * math.sin(2 * math.pi * i / n)
                          for i in range(n)]
        elif self.data_mode == "custom":
            # не меняем
            pass

    def set_type(self, t):
        self.chart_type = t

    def set_mode(self, m):
        self.data_mode = m
        if m != "custom":
            self.regenerate_data()

    def total(self):
        return sum(self.data)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Chart Component · Диаграммы")
        root.geometry("1600x1000")
        root.minsize(1400, 900)
        root.configure(bg=BG_DEEP)

        self.fps_time = time.time()
        self.fps = 60
        self.frame_count = 0

        self.state = AppState()
        self.btn_zones = {}

        self.W, self.H = 1600, 1000

        self.canvas = tk.Canvas(root, bg=BG_DEEP, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)

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
        self.canvas.create_text(60, 40, text="📊",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="CHART COMPONENT",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(360, 44,
                                text="· ИССЛЕДОВАНИЕ ВОЗМОЖНОСТЕЙ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ПАНЕЛЬ ТИПОВ СВЕРХУ ----------
    def _draw_type_bar(self, w, y):
        round_rect(self.canvas, 50, y, w - 50, y + 60, 12,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 30, anchor="w",
                                text="ТИП:",
                                fill=TEXT_DIM, font=FONT_LABEL)

        # 9 типов в ряд
        btn_w = 130
        btn_h = 40
        gap = 6
        start_x = 130

        for i, (key, label, _icon) in enumerate(CHART_TYPES):
            bx = start_x + i * (btn_w + gap)
            active = (self.state.chart_type == key)
            self._draw_type_btn(bx, y + 10, btn_w, btn_h,
                                  key, label, active)

    def _draw_type_btn(self, x, y, w, h, key, label, active):
        color = NEON_CYAN
        if active:
            for i in range(3, 0, -1):
                round_rect(self.canvas, x - i, y - i,
                           x + w + i, y + h + i, 8 + i,
                           outline=lerp(color, BG_DEEP, i / 4), width=1)
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
        self.btn_zones[f"type_{key}"] = (x, y, x + w, y + h)

    # ---------- ОБЛАСТЬ ДИАГРАММЫ ----------
    def _draw_chart_area(self, w, y, h):
        panel_w = 320
        chart_w = w - 100 - panel_w - 20

        round_rect(self.canvas, 50, y, 50 + chart_w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        # заголовок
        t = next((x[1] for x in CHART_TYPES if x[0] == self.state.chart_type),
                 "CHART")
        self.canvas.create_text(70, y + 25, anchor="w",
                                text=f"▸ {t}",
                                fill=NEON_CYAN, font=FONT_LABEL)

        # внутренний фон графика
        gx = 70
        gy = y + 50
        gw = chart_w - 40
        gh = h - 70

        round_rect(self.canvas, gx, gy, gx + gw, gy + gh, 8,
                   fill=BG_GRAPH, outline="")

        # вызываем функцию отрисовки
        fn = DRAW_FUNCS.get(self.state.chart_type, draw_bar_chart)
        try:
            fn(self.canvas, gx, gy, gw, gh,
               self.state.data, self.state.labels, self.state.colors)
        except Exception as e:
            self.canvas.create_text(gx + gw / 2, gy + gh / 2,
                                    text=f"Ошибка: {e}",
                                    fill=NEON_RED,
                                    font=FONT_LABEL)

    # ---------- ПАНЕЛЬ СПРАВА ----------
    def _draw_panel(self, w, y, h):
        panel_w = 320
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ ДАННЫЕ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # режимы данных
        modes = [
            ("random", "СЛУЧАЙНЫЕ",  NEON_CYAN),
            ("linear", "ЛИНЕЙНЫЕ",   NEON_GREEN),
            ("sine",   "СИНУС",      NEON_PINK),
        ]
        m_w = 88
        m_h = 40
        m_gap = 6
        start_x = panel_x + 20

        for i, (key, label, color) in enumerate(modes):
            bx = start_x + i * (m_w + m_gap)
            active = (self.state.data_mode == key)
            self._draw_mode_btn(bx, y + 50, m_w, m_h,
                                  key, label, color, active)

        # === Таблица значений ===
        ty = y + 115
        self.canvas.create_text(panel_x + 20, ty, anchor="w",
                                text="ЗНАЧЕНИЯ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        # 8 строк таблицы
        row_h = 32
        total_ones = 0

        for i, v in enumerate(self.state.data[:8]):
            ry = ty + 25 + i * row_h
            col = self.state.colors[i % len(self.state.colors)]

            round_rect(self.canvas, panel_x + 20, ry,
                       panel_x + panel_w - 20, ry + row_h - 6, 6,
                       fill=BG_PANEL)

            # цветной индикатор
            self.canvas.create_rectangle(panel_x + 25, ry + 6,
                                          panel_x + 35, ry + row_h - 12,
                                          fill=col, outline="")

            # метка
            self.canvas.create_text(panel_x + 45, ry + row_h / 2 - 3,
                                    anchor="w",
                                    text=self.state.labels[i],
                                    fill=TEXT_DIM,
                                    font=("Consolas", 10))

            # значение
            self.canvas.create_text(panel_x + panel_w - 30,
                                    ry + row_h / 2 - 3, anchor="e",
                                    text=f"{v:.1f}",
                                    fill=col,
                                    font=("Consolas", 12, "bold"))

            total_ones += v

        # === Итог ===
        iy = ty + 25 + 8 * row_h + 10

        round_rect(self.canvas, panel_x + 20, iy,
                   panel_x + panel_w - 20, iy + 80, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_AMBER, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, iy + 20,
                                text="ИТОГО",
                                fill=TEXT_DIM, font=FONT_LABEL_S)
        self.canvas.create_text(panel_x + panel_w / 2, iy + 50,
                                text=f"{total_ones:.1f}",
                                fill=NEON_AMBER,
                                font=("Consolas", 22, "bold"))

        # === Кнопки ===
        by = y + h - 60
        b_w = 130
        b_h = 44
        b_gap = 8

        self._draw_btn(panel_x + 20, by, b_w, b_h,
                       "🎲 НОВЫЕ", NEON_PURP, "regen")
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "📷 PNG", NEON_CYAN, "save_png")

    def _draw_mode_btn(self, x, y, w, h, key, label, color, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill=lerp(color, BG_DEEP, 0.6),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Segoe UI", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 8,
                       fill="#0f141c",
                       outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
        self.btn_zones[f"mode_{key}"] = (x, y, x + w, y + h)

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
        self._draw_type_bar(w, 90)

        chart_y = 170
        chart_h = h - chart_y - 20
        self._draw_chart_area(w, chart_y, chart_h)
        self._draw_panel(w, chart_y, chart_h)

    # ---------- СОБЫТИЯ ----------
    def _on_click(self, event):
        for key, (x0, y0, x1, y1) in self.btn_zones.items():
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self._do_action(key)
                return

    def _do_action(self, key):
        if key.startswith("type_"):
            self.state.set_type(key[5:])
        elif key.startswith("mode_"):
            self.state.set_mode(key[5:])
        elif key == "regen":
            self.state.regenerate_data()
        elif key == "save_png":
            self._save_png()

    def _save_png(self):
        try:
            from PIL import ImageGrab
            from tkinter import filedialog, messagebox
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png")],
                initialfile=f"chart_{self.state.chart_type}.png")
            if not path:
                return
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            ImageGrab.grab().crop((x, y, x1, y1)).save(path)
            messagebox.showinfo("Сохранено", path)
        except ImportError:
            from tkinter import messagebox
            messagebox.showerror("Ошибка",
                "Установите Pillow: pip install pillow")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", str(e))

    # ---------- АНИМАЦИЯ ----------
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