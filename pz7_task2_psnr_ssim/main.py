"""
ОКФРС. Практика 7. Задание 2.
Алгоритм анализа искажения изображений: PSNR и SSIM.
Полноценная реализация + графики зависимости метрик от процента ошибок.
Премиум-стиль 2026.
"""
import tkinter as tk
import sys, os, math, random, time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    import numpy as np
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[warn] Установите: pip install pillow numpy")


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
# ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ
# ============================================================
def generate_test_image(width=256, height=256, pattern="photo"):
    if not PIL_OK:
        return None
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    if pattern == "photo":
        # небо
        for y in range(height):
            t = y / height
            if t < 0.6:
                k = t / 0.6
                col = (int(40 + 130 * k), int(80 + 100 * k), int(160 + 60 * k))
            else:
                k = (t - 0.6) / 0.4
                col = (int(40 + 20 * (1-k)), int(90 + 40 * (1-k)), int(50 + 30 * (1-k)))
            draw.rectangle([0, y, width, y + 1], fill=col)
        # солнце
        draw.ellipse([width - 90, 40, width - 20, 110], fill=(255, 230, 130))
        # горы
        for i in range(3):
            x = i * 100 + 10
            draw.polygon([(x, height - 100), (x + 60, height - 200),
                          (x + 120, height - 100)], fill=(70, 80, 100))
        # земля
        draw.rectangle([0, height - 100, width, height], fill=(50, 90, 50))
    elif pattern == "gradient":
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        xv = np.linspace(0, 255, width, dtype=np.uint8)
        yv = np.linspace(0, 255, height, dtype=np.uint8)
        arr[:, :, 0] = xv[np.newaxis, :]
        arr[:, :, 1] = yv[:, np.newaxis]
        arr[:, :, 2] = (255 - arr[:, :, 0])
        img = Image.fromarray(arr)
    elif pattern == "checker":
        cell = 20
        for y in range(0, height, cell):
            for x in range(0, width, cell):
                c = 255 if ((x // cell + y // cell) % 2 == 0) else 50
                draw.rectangle([x, y, x + cell, y + cell], fill=(c, c, c))
    elif pattern == "circles":
        for _ in range(10):
            cx, cy = random.randint(0, width), random.randint(0, height)
            r = random.randint(30, 70)
            col = tuple(random.randint(50, 255) for _ in range(3))
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col)
    return img


def add_bit_errors(img, percent):
    """Инвертирует случайные биты в процентах от общего числа."""
    arr = np.array(img, dtype=np.uint8).copy()
    prob = percent / 100.0
    flat = arr.flatten()
    n = flat.size
    mask = np.random.random(n) < prob
    bits = np.random.randint(0, 8, n).astype(np.uint8)
    xors = (1 << bits).astype(np.uint8)
    flat = flat ^ (mask * xors).astype(np.uint8)
    return Image.fromarray(flat.reshape(arr.shape))


# ============================================================
# МЕТРИКИ
# ============================================================
def mse(img1, img2):
    a = np.array(img1, dtype=np.float64)
    b = np.array(img2, dtype=np.float64)
    return float(np.mean((a - b) ** 2))


def psnr(img1, img2):
    m = mse(img1, img2)
    if m == 0:
        return 100.0   # максимум
    return 10 * math.log10(255 * 255 / m)


def ssim_full(img1, img2, window=11):
    """
    Полноценный SSIM с окнами (как в оригинальной статье Wang et al., 2004).
    Использует гауссово окно 11x11.
    """
    g1 = np.array(img1.convert("L"), dtype=np.float64)
    g2 = np.array(img2.convert("L"), dtype=np.float64)

    # гауссово окно
    sigma = 1.5
    ax = np.arange(-window//2 + 1, window//2 + 1, dtype=np.float64)
    gauss = np.exp(-(ax ** 2) / (2 * sigma ** 2))
    gauss /= gauss.sum()
    win2d = np.outer(gauss, gauss)

    # константы
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    # локальные средние/дисперсии через свёртку
    from scipy.ndimage import uniform_filter
    try:
        mu1 = uniform_filter(g1, size=window, mode="reflect")
        mu2 = uniform_filter(g2, size=window, mode="reflect")
        mu1_sq = mu1 * mu1
        mu2_sq = mu2 * mu2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = uniform_filter(g1 * g1, size=window) - mu1_sq
        sigma2_sq = uniform_filter(g2 * g2, size=window) - mu2_sq
        sigma12 = uniform_filter(g1 * g2, size=window) - mu1_mu2

        num = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
        den = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
        ssim_map = num / den
        return float(ssim_map.mean())
    except ImportError:
        # fallback — глобальный SSIM
        mu1 = g1.mean()
        mu2 = g2.mean()
        var1 = g1.var()
        var2 = g2.var()
        cov = ((g1 - mu1) * (g2 - mu2)).mean()
        s = ((2 * mu1 * mu2 + C1) * (2 * cov + C2)) / \
            ((mu1**2 + mu2**2 + C1) * (var1 + var2 + C2))
        return float(s)


def ssim_global(img1, img2):
    """Глобальный (упрощённый) SSIM — для сравнения."""
    g1 = np.array(img1.convert("L"), dtype=np.float64)
    g2 = np.array(img2.convert("L"), dtype=np.float64)

    mu1 = g1.mean()
    mu2 = g2.mean()
    var1 = g1.var()
    var2 = g2.var()
    cov = ((g1 - mu1) * (g2 - mu2)).mean()

    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    s = ((2 * mu1 * mu2 + C1) * (2 * cov + C2)) / \
        ((mu1**2 + mu2**2 + C1) * (var1 + var2 + C2))
    return float(s)


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.image_size = 256
        self.pattern = "photo"
        self.error_percent = 1.0

        self.original_img = None
        self.noisy_img = None

        # текущие метрики
        self.mse_val = 0.0
        self.psnr_val = 0.0
        self.ssim_val = 0.0
        self.ssim_global_val = 0.0

        # кривые зависимости от % ошибок
        self.curve_percents = [0, 0.1, 0.2, 0.5, 1, 2, 3, 5, 7, 10, 15, 20, 30, 40, 50]
        self.curve_psnr = []
        self.curve_ssim = []
        self.curve_ssim_global = []
        self.curve_mse = []

        self.regenerate()

    def regenerate(self):
        self.original_img = generate_test_image(self.image_size,
                                                 self.image_size,
                                                 self.pattern)
        self.apply_noise()
        self.compute_curves()

    def apply_noise(self):
        if self.original_img is None:
            return
        self.noisy_img = add_bit_errors(self.original_img, self.error_percent)
        self.mse_val = mse(self.original_img, self.noisy_img)
        self.psnr_val = psnr(self.original_img, self.noisy_img)
        self.ssim_global_val = ssim_global(self.original_img, self.noisy_img)
        try:
            self.ssim_val = ssim_full(self.original_img, self.noisy_img)
        except Exception:
            self.ssim_val = self.ssim_global_val

    def compute_curves(self):
        """Считает зависимости метрик от процента ошибок."""
        if self.original_img is None:
            return
        self.curve_psnr = []
        self.curve_ssim = []
        self.curve_ssim_global = []
        self.curve_mse = []

        for p in self.curve_percents:
            noisy = add_bit_errors(self.original_img, p)
            self.curve_mse.append(mse(self.original_img, noisy))
            self.curve_psnr.append(psnr(self.original_img, noisy))
            self.curve_ssim_global.append(ssim_global(self.original_img, noisy))
            try:
                self.curve_ssim.append(ssim_full(self.original_img, noisy))
            except Exception:
                self.curve_ssim.append(self.curve_ssim_global[-1])

    def set_error_percent(self, p):
        self.error_percent = max(0.0, min(50.0, float(p)))
        self.apply_noise()

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.regenerate()


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ PSNR · SSIM · Анализ искажений")
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

        self.original_photo = None
        self.noisy_photo = None

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
        for x in range(0, w, 60):
            self.canvas.create_line(x, 0, x, h, fill="#0d1220")
        for y in range(0, h, 60):
            self.canvas.create_line(0, y, w, y, fill="#0d1220")

    # ---------- ЗАГОЛОВОК ----------
    def _draw_header(self, w):
        self.canvas.create_text(60, 40, text="∿",
                                fill=NEON_CYAN,
                                font=("Segoe UI", 30, "bold"))
        self.canvas.create_text(100, 40, text="PSNR & SSIM",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(300, 44,
                                text="· АНАЛИЗ ИСКАЖЕНИЙ ИЗОБРАЖЕНИЙ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ИЗОБРАЖЕНИЯ + МЕТРИКИ ----------
    def _draw_images_and_metrics(self, w, y, h):
        panel_w = 460
        main_w = w - 100 - panel_w - 20

        # карточка
        round_rect(self.canvas, 50, y, 50 + main_w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 25, anchor="w",
                                text="▸ СРАВНЕНИЕ ИЗОБРАЖЕНИЙ",
                                fill=NEON_CYAN, font=FONT_LABEL)

        # изображения — 2 квадрата в верхней части
        img_size = min(int((main_w - 100) / 2), int(h * 0.55))
        x1 = 70
        x2 = 70 + img_size + 60
        img_y = y + 60

        # ОРИГИНАЛ
        self.canvas.create_text(x1, y + 50, anchor="w",
                                text="ОРИГИНАЛ",
                                fill=NEON_GREEN, font=FONT_LABEL_S)
        round_rect(self.canvas, x1 - 4, img_y - 4,
                   x1 + img_size + 4, img_y + img_size + 4, 8,
                   fill="#051208",
                   outline=lerp(NEON_GREEN, BG_DEEP, 0.4), width=2)

        # ИСКАЖЁННЫЙ
        self.canvas.create_text(x2, y + 50, anchor="w",
                                text=f"С {self.state.error_percent:.2f}% ОШИБОК",
                                fill=NEON_RED, font=FONT_LABEL_S)
        round_rect(self.canvas, x2 - 4, img_y - 4,
                   x2 + img_size + 4, img_y + img_size + 4, 8,
                   fill="#1a0508",
                   outline=lerp(NEON_RED, BG_DEEP, 0.4), width=2)

        if PIL_OK and self.state.original_img:
            o = self.state.original_img.resize((img_size, img_size),
                                                Image.NEAREST)
            n = self.state.noisy_img.resize((img_size, img_size),
                                             Image.NEAREST)
            self.original_photo = ImageTk.PhotoImage(o)
            self.noisy_photo = ImageTk.PhotoImage(n)
            self.canvas.create_image(x1, img_y, anchor="nw",
                                      image=self.original_photo)
            self.canvas.create_image(x2, img_y, anchor="nw",
                                      image=self.noisy_photo)

        # метрики — нижняя часть карточки
        m_y = img_y + img_size + 30
        m_h = y + h - m_y - 20
        if m_h < 80:
            m_h = 80

        m_gap = 12
        m_w = (main_w - 40 - 3 * m_gap) / 4

        metrics = [
            ("MSE",  f"{self.state.mse_val:.2f}",
             NEON_AMBER, "средне-квадр. ошибка"),
            ("PSNR", f"{self.state.psnr_val:.2f} дБ",
             self._psnr_color(self.state.psnr_val),
             ">30 = отлично, <20 = плохо"),
            ("SSIM", f"{self.state.ssim_val:.4f}",
             self._ssim_color(self.state.ssim_val),
             "полноценный (окна 11×11)"),
            ("SSIM₂", f"{self.state.ssim_global_val:.4f}",
             self._ssim_color(self.state.ssim_global_val),
             "глобальный (упрощ.)"),
        ]

        for i, (label, value, color, hint) in enumerate(metrics):
            mx = 70 + i * (m_w + m_gap)

            round_rect(self.canvas, mx, m_y,
                       mx + m_w, m_y + m_h, 10,
                       fill=BG_PANEL,
                       outline=lerp(color, BG_DEEP, 0.5), width=1)

            self.canvas.create_text(mx + 15, m_y + 22, anchor="w",
                                    text=label, fill=TEXT_DIM,
                                    font=FONT_LABEL_S)
            self.canvas.create_text(mx + 15, m_y + 55, anchor="w",
                                    text=value, fill=color,
                                    font=("Consolas", 17, "bold"))
            self.canvas.create_text(mx + 15, m_y + 85, anchor="w",
                                    text=hint, fill=TEXT_DIM,
                                    font=("Segoe UI", 8, "italic"))

    def _psnr_color(self, v):
        if v > 30: return NEON_GREEN
        if v > 20: return NEON_AMBER
        return NEON_RED

    def _ssim_color(self, v):
        if v > 0.9: return NEON_GREEN
        if v > 0.7: return NEON_AMBER
        return NEON_RED

    # ---------- ГРАФИКИ ----------
    def _draw_curves(self, w, y, h):
        panel_w = 460
        main_w = w - 100 - panel_w - 20

        round_rect(self.canvas, 50, y, 50 + main_w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 25, anchor="w",
                                text="▸ ЗАВИСИМОСТЬ МЕТРИК ОТ ПРОЦЕНТА ОШИБОК",
                                fill=NEON_CYAN, font=FONT_LABEL)

        # 3 графика: PSNR, SSIM, MSE
        n_plots = 3
        gap = 15
        plot_w = (main_w - 40 - (n_plots - 1) * gap) / n_plots
        plot_h = h - 60

        px_start = 70
        py = y + 55

        # === PSNR ===
        self._draw_one_curve(px_start, py, plot_w, plot_h,
                              "PSNR (дБ)", self.state.curve_percents,
                              self.state.curve_psnr,
                              y_min=0, y_max=50, color=NEON_GREEN,
                              good_threshold=30)

        # === SSIM ===
        x2 = px_start + plot_w + gap
        self._draw_one_curve(x2, py, plot_w, plot_h,
                              "SSIM", self.state.curve_percents,
                              self.state.curve_ssim,
                              y_min=0, y_max=1, color=NEON_CYAN,
                              good_threshold=0.9)

        # === MSE ===
        x3 = x2 + plot_w + gap
        mse_max = max(self.state.curve_mse) if self.state.curve_mse else 1
        self._draw_one_curve(x3, py, plot_w, plot_h,
                              "MSE", self.state.curve_percents,
                              self.state.curve_mse,
                              y_min=0, y_max=mse_max, color=NEON_AMBER)

    def _draw_one_curve(self, x, y, w, h, title, xs, ys,
                         y_min, y_max, color, good_threshold=None):
        # заголовок
        self.canvas.create_text(x + w / 2, y - 5,
                                text=title, fill=color,
                                font=FONT_LABEL_S)

        # фон
        round_rect(self.canvas, x, y, x + w, y + h, 6,
                   fill=BG_GRAPH, outline=BORDER, width=1)

        # сетка
        for i in range(1, 5):
            k = i / 5
            gx = x + k * w
            gy = y + k * h
            self.canvas.create_line(gx, y, gx, y + h,
                                    fill="#1a2540", dash=(2, 3))
            self.canvas.create_line(x, gy, x + w, gy,
                                    fill="#1a2540", dash=(2, 3))

        # оси
        self.canvas.create_line(x, y + h - 20, x + w, y + h - 20,
                                fill=NEON_AMBER, width=1)
        self.canvas.create_line(x + 25, y, x + 25, y + h,
                                fill=NEON_AMBER, width=1)

        # подписи по Y
        self.canvas.create_text(x + 20, y + 8, anchor="e",
                                text=f"{y_max:.0f}",
                                fill=TEXT_DIM,
                                font=("Consolas", 8))
        self.canvas.create_text(x + 20, y + h - 20, anchor="e",
                                text=f"{y_min:.0f}",
                                fill=TEXT_DIM,
                                font=("Consolas", 8))

        # порог
        if good_threshold is not None and y_min <= good_threshold <= y_max:
            ty = y + h - 20 - (good_threshold - y_min) / (y_max - y_min) * (h - 20)
            self.canvas.create_line(x + 25, ty, x + w, ty,
                                    fill=lerp(NEON_GREEN, BG_DEEP, 0.5),
                                    dash=(4, 4), width=1)
            self.canvas.create_text(x + w - 5, ty - 6, anchor="e",
                                    text=f"{good_threshold}",
                                    fill=NEON_GREEN,
                                    font=("Consolas", 8))

        # кривая
        if not xs or not ys:
            return

        pts = []
        for xv, yv in zip(xs, ys):
            px = x + 25 + (xv / max(xs)) * (w - 30)
            yv_clamped = max(y_min, min(y_max, yv))
            py = y + h - 20 - (yv_clamped - y_min) / (y_max - y_min) * (h - 20)
            pts.extend([px, py])

        if len(pts) >= 4:
            self.canvas.create_line(*pts,
                                    fill=lerp(color, BG_DEEP, 0.6),
                                    width=4, smooth=True)
            self.canvas.create_line(*pts, fill=color,
                                    width=2, smooth=True)

        # текущая точка
        current_x = self.state.error_percent
        # найдём ближайшее
        closest_idx = 0
        min_diff = 1e9
        for i, xv in enumerate(xs):
            d = abs(xv - current_x)
            if d < min_diff:
                min_diff = d
                closest_idx = i

        px = x + 25 + (xs[closest_idx] / max(xs)) * (w - 30)
        yv = ys[closest_idx]
        yv_c = max(y_min, min(y_max, yv))
        py = y + h - 20 - (yv_c - y_min) / (y_max - y_min) * (h - 20)

        self.canvas.create_oval(px - 5, py - 5, px + 5, py + 5,
                                fill="#ffffff", outline=color, width=2)

    # ---------- ПАНЕЛЬ ----------
    def _draw_panel(self, w, y, h):
        panel_w = 460
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ УПРАВЛЕНИЕ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # ползунок
        sy = y + 65

        self.canvas.create_text(panel_x + 20, sy, anchor="w",
                                text="ПРОЦЕНТ ОШИБОЧНЫХ БИТОВ",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        self.canvas.create_text(panel_x + panel_w - 20, sy, anchor="e",
                                text=f"{self.state.error_percent:.2f} %",
                                fill=NEON_PINK, font=FONT_MONO)

        bar_x0 = panel_x + 20
        bar_x1 = panel_x + panel_w - 20
        bar_y = sy + 35
        bar_h = 14

        round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                   bar_x1, bar_y + bar_h/2, 7,
                   fill="#0f141c", outline="")

        k = self.state.error_percent / 50.0
        k = max(0.0, min(1.0, k))
        if k > 0.005:
            col_fill = NEON_GREEN if k < 0.15 else (
                       NEON_AMBER if k < 0.4 else NEON_RED)
            round_rect(self.canvas, bar_x0, bar_y - bar_h/2,
                       bar_x0 + (bar_x1 - bar_x0) * k, bar_y + bar_h/2,
                       7, fill=col_fill, outline="")

        cx_ = bar_x0 + (bar_x1 - bar_x0) * k
        self.canvas.create_oval(cx_ - 12, bar_y - 12,
                                cx_ + 12, bar_y + 12,
                                fill="#ffffff", outline=NEON_PINK, width=2)

        self.slider_zones["errors"] = (bar_x0 - 10, bar_y - 16,
                                        bar_x1 + 10, bar_y + 16,
                                        0.0, 50.0)

        for j in range(6):
            kk = j / 5
            xx = bar_x0 + (bar_x1 - bar_x0) * kk
            val = int(50 * kk)
            self.canvas.create_line(xx, bar_y + 16, xx, bar_y + 20,
                                    fill=TEXT_DIM, width=1)
            self.canvas.create_text(xx, bar_y + 30,
                                    text=f"{val}",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 9, "bold"))

        # быстрые кнопки
        qy = y + 170

        self.canvas.create_text(panel_x + 20, qy, anchor="w",
                                text="БЫСТРЫЙ ВЫБОР:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        q_vals = [(0.1, "0.1"), (0.5, "0.5"), (1, "1"),
                  (5, "5"), (10, "10"), (25, "25")]
        q_btn_w = 64
        q_btn_h = 34
        q_gap = 6
        q_start = panel_x + 20

        for i, (n, label) in enumerate(q_vals):
            bx = q_start + i * (q_btn_w + q_gap)
            active = abs(self.state.error_percent - n) < 0.01
            self._draw_q_btn(bx, qy + 20, q_btn_w, q_btn_h, label, n, active)

        # паттерны
        py = y + 250

        self.canvas.create_text(panel_x + 20, py, anchor="w",
                                text="ТИП ИЗОБРАЖЕНИЯ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        patterns = [
            ("photo",    "ФОТО",      NEON_CYAN),
            ("gradient", "ГРАДИЕНТ",  NEON_GREEN),
            ("circles",  "КРУГИ",     NEON_AMBER),
            ("checker",  "ШАХМАТЫ",   NEON_PINK),
        ]
        p_btn_w = 100
        p_btn_h = 34
        p_gap = 8
        p_start = panel_x + 20

        for i, (key, label, color) in enumerate(patterns):
            bx = p_start + i * (p_btn_w + p_gap)
            active = (self.state.pattern == key)
            self._draw_p_btn(bx, py + 20, p_btn_w, p_btn_h,
                              key, label, color, active)

        # --- информационный блок ---
        info_y = y + 330
        info_h = h - (info_y - y) - 20

        round_rect(self.canvas, panel_x + 20, info_y,
                   panel_x + panel_w - 20, info_y + info_h, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, info_y + 22,
                                text="ЧТО ТАКОЕ PSNR И SSIM",
                                fill=NEON_CYAN, font=FONT_LABEL_S)

        info_lines = [
            "PSNR (Peak Signal-to-Noise Ratio):",
            "  PSNR = 10·log₁₀(255² / MSE)",
            "  >40 дБ — идеально,",
            "  30-40 — отлично, не заметно,",
            "  20-30 — заметные искажения,",
            "  <20 — сигнал разрушен.",
            "",
            "SSIM (Structural Similarity):",
            "  учитывает структуру, яркость, контраст.",
            "  1.0 — идентичны,",
            "  >0.95 — отлично,",
            "  0.8-0.95 — заметно,",
            "  <0.5 — сильно искажено.",
        ]

        ly = info_y + 45
        for line in info_lines:
            if line:
                self.canvas.create_text(panel_x + 35, ly, anchor="w",
                                        text=line, fill=TEXT_DIM,
                                        font=("Consolas", 9))
            ly += 15

    def _draw_q_btn(self, x, y, w, h, text, n, active):
        color = NEON_CYAN
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.5),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=text, fill=color,
                                    font=("Consolas", 11, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=text, fill=TEXT_DIM,
                                    font=("Consolas", 11, "bold"))
        self.btn_zones[f"q_{n}"] = (x, y, x + w, y + h)

    def _draw_p_btn(self, x, y, w, h, key, label, color, active):
        if active:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill=lerp(color, BG_DEEP, 0.55),
                       outline=color, width=2)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=color,
                                    font=("Segoe UI", 10, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 10, "bold"))
        self.btn_zones[f"pattern_{key}"] = (x, y, x + w, y + h)

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

        # изображения + метрики — верхняя часть
        top_y = 90
        top_h = h * 0.5 - 40
        self._draw_images_and_metrics(w, top_y, top_h)

        # графики — нижняя часть
        graph_y = top_y + top_h + 15
        graph_h = h - graph_y - 30
        if graph_h < 200:
            graph_h = 200
        self._draw_curves(w, graph_y, graph_h)

        # панель — на всю высоту
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
        if key == "errors":
            self.state.set_error_percent(val)

    def _do_action(self, key):
        if key.startswith("q_"):
            val = float(key[2:])
            self.state.set_error_percent(val)
        elif key.startswith("pattern_"):
            pattern = key[8:]
            self.state.set_pattern(pattern)

    # ---------- АНИМАЦИЯ ----------
    def _animate(self):
        self.frame_count += 1
        now = time.time()
        if now - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = now

        self._redraw_all()
        self.root.after(80, self._animate)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()