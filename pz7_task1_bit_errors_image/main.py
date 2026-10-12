"""
ОКФРС. Практика 7. Задание 1.
Модель передачи изображения через шумный канал:
процент ошибочных битов → искажение пикселей.
Премиум-стиль 2026.
"""
import tkinter as tk
import sys, os, math, random, time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[warn] Установите Pillow: pip install pillow")


# ============================================================
# ПАЛИТРА
# ============================================================
BG_DEEP    = "#08090f"
BG_GLASS   = "#131823"
BG_GRAPH   = "#050810"
BG_PANEL   = "#0f141c"
BG_CELL    = "#0e1218"
BORDER     = "#232a3d"
BORDER_HL  = "#2f3648"

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
# ГЕНЕРАЦИЯ ТЕСТОВОГО ИЗОБРАЖЕНИЯ
# ============================================================
def generate_test_image(width, height, pattern="gradient"):
    """Генерирует тестовое изображение с известным паттерном."""
    if not PIL_OK:
        return None

    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    if pattern == "gradient":
        for y in range(height):
            for x in range(width):
                r = int(x / width * 255)
                g = int(y / height * 255)
                b = int((1 - (x + y) / (width + height)) * 255)
                img.putpixel((x, y), (r, g, b))
    elif pattern == "circles":
        # несколько цветных кругов
        for i in range(8):
            cx = random.randint(0, width)
            cy = random.randint(0, height)
            r = random.randint(30, 80)
            col = (random.randint(50, 255),
                   random.randint(50, 255),
                   random.randint(50, 255))
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    elif pattern == "checkerboard":
        cell = 20
        for y in range(0, height, cell):
            for x in range(0, width, cell):
                c = 255 if ((x // cell + y // cell) % 2 == 0) else 40
                draw.rectangle([x, y, x + cell - 1, y + cell - 1],
                               fill=(c, c, c))
    elif pattern == "photo":
        # имитация фотографии — фигуры
        draw.rectangle([0, 0, width, height], fill=(20, 40, 80))
        # небо→земля
        for y in range(height // 2):
            t = y / (height // 2)
            col = (int(20 + 100 * t), int(40 + 80 * t), int(80 + 60 * t))
            draw.rectangle([0, y, width, y + 1], fill=col)
        # солнце
        draw.ellipse([width - 100, 40, width - 30, 110],
                     fill=(255, 220, 100))
        # горы
        for i in range(4):
            x = i * 120 + 30
            draw.polygon([(x, height - 100), (x + 80, height - 200),
                          (x + 160, height - 100)],
                         fill=(60, 70, 90))
        # земля
        draw.rectangle([0, height - 100, width, height],
                       fill=(40, 80, 40))
    elif pattern == "letters":
        # текст большими буквами
        draw.rectangle([0, 0, width, height], fill=(240, 240, 240))
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 90)
        except Exception:
            font = None
        draw.text((30, height // 2 - 60), "TEST", fill=(20, 20, 20), font=font)
    else:
        # random
        for y in range(height):
            for x in range(width):
                img.putpixel((x, y),
                             (random.randint(0, 255),
                              random.randint(0, 255),
                              random.randint(0, 255)))
    return img


# ============================================================
# ИСКАЖЕНИЕ ИЗОБРАЖЕНИЯ
# ============================================================
def add_bit_errors(img, error_percent):
    """
    Искажает изображение: каждая битовая позиция пикселя
    с вероятностью error_percent/100 инвертируется.
    """
    if not PIL_OK:
        return img

    error_prob = error_percent / 100.0
    pixels = img.load()
    w, h = img.size

    # для ускорения — используем numpy если есть
    try:
        import numpy as np
        arr = np.array(img, dtype=np.uint8).copy()
        shape = arr.shape

        # создаём маску ошибок на уровне битов
        # каждый байт = 8 бит, поэтому полная маска
        flat = arr.flatten()
        n_bytes = flat.size
        mask = np.random.random(n_bytes) < error_prob
        # для каждого ошибочного байта — инвертируем случайный бит
        bit_positions = np.random.randint(0, 8, n_bytes).astype(np.uint8)
        xor_vals = (1 << bit_positions).astype(np.uint8)
        flat = flat ^ (mask * xor_vals).astype(np.uint8)
        arr = flat.reshape(shape)
        return Image.fromarray(arr)
    except ImportError:
        # медленный питоновский путь
        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]
                new_r = r
                new_g = g
                new_b = b
                for _ in range(3):
                    if random.random() < error_prob:
                        bit = random.randint(0, 7)
                        if _ == 0:
                            new_r ^= (1 << bit)
                        elif _ == 1:
                            new_g ^= (1 << bit)
                        else:
                            new_b ^= (1 << bit)
                pixels[x, y] = (new_r & 0xFF, new_g & 0xFF, new_b & 0xFF)
        return img


# ============================================================
# МЕТРИКИ
# ============================================================
def compute_mse(img1, img2):
    """Mean Squared Error."""
    if not PIL_OK:
        return 0
    try:
        import numpy as np
        a = np.array(img1, dtype=np.float64)
        b = np.array(img2, dtype=np.float64)
        return float(np.mean((a - b) ** 2))
    except ImportError:
        p1 = img1.load()
        p2 = img2.load()
        w, h = img1.size
        total = 0
        n = 0
        for y in range(h):
            for x in range(w):
                r1, g1, b1 = p1[x, y]
                r2, g2, b2 = p2[x, y]
                total += ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
                n += 3
        return total / n if n else 0


def compute_psnr(img1, img2):
    """Peak Signal-to-Noise Ratio в дБ."""
    mse = compute_mse(img1, img2)
    if mse == 0:
        return 999.0
    return 10 * math.log10(255.0 * 255.0 / mse)


def compute_ssim_simple(img1, img2):
    """
    Упрощённый SSIM (без окон, глобальный).
    Полноценный SSIM обычно на grayscale с окнами 8x8 или 11x11.
    """
    if not PIL_OK:
        return 0
    try:
        import numpy as np

        # в grayscale
        g1 = np.array(img1.convert("L"), dtype=np.float64)
        g2 = np.array(img2.convert("L"), dtype=np.float64)

        mu1 = g1.mean()
        mu2 = g2.mean()
        var1 = g1.var()
        var2 = g2.var()
        cov = ((g1 - mu1) * (g2 - mu2)).mean()

        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        ssim = ((2 * mu1 * mu2 + C1) * (2 * cov + C2)) / \
               ((mu1 ** 2 + mu2 ** 2 + C1) * (var1 + var2 + C2))
        return float(ssim)
    except ImportError:
        return 0.0


def percent_different_pixels(img1, img2):
    """Процент пикселей, отличающихся хотя бы на 1 в любом канале."""
    if not PIL_OK:
        return 0
    try:
        import numpy as np
        a = np.array(img1, dtype=np.int16)
        b = np.array(img2, dtype=np.int16)
        diff = np.any(a != b, axis=2)
        return float(diff.mean() * 100)
    except ImportError:
        p1 = img1.load()
        p2 = img2.load()
        w, h = img1.size
        count = 0
        for y in range(h):
            for x in range(w):
                if p1[x, y] != p2[x, y]:
                    count += 1
        return count / (w * h) * 100


# ============================================================
# СОСТОЯНИЕ
# ============================================================
class AppState:
    def __init__(self):
        self.error_percent = 1.0
        self.image_size = 256
        self.pattern = "photo"

        self.original_img = None
        self.noisy_img = None
        self.original_photo = None
        self.noisy_photo = None

        self.mse = 0.0
        self.psnr = 0.0
        self.ssim = 0.0
        self.diff_pct = 0.0

        self.regenerate_original()

    def regenerate_original(self):
        self.original_img = generate_test_image(self.image_size,
                                                 self.image_size,
                                                 self.pattern)
        self.apply_noise()

    def apply_noise(self):
        if self.original_img is None:
            return
        self.noisy_img = add_bit_errors(self.original_img.copy(),
                                         self.error_percent)
        # вычисляем метрики
        self.mse = compute_mse(self.original_img, self.noisy_img)
        self.psnr = compute_psnr(self.original_img, self.noisy_img)
        self.ssim = compute_ssim_simple(self.original_img, self.noisy_img)
        self.diff_pct = percent_different_pixels(self.original_img,
                                                   self.noisy_img)

    def set_error_percent(self, p):
        self.error_percent = max(0.0, min(50.0, float(p)))
        self.apply_noise()

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.regenerate_original()

    def get_photos(self, size):
        """Возвращает PhotoImage для отображения."""
        if not PIL_OK:
            return None, None
        o = self.original_img.resize((size, size), Image.NEAREST)
        n = self.noisy_img.resize((size, size), Image.NEAREST)
        return ImageTk.PhotoImage(o), ImageTk.PhotoImage(n)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("⚡ Bit Errors · Искажение изображения")
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
        self.canvas.create_text(60, 40, text="⚡",
                                fill=NEON_CYAN,
                                font=("Segoe UI Emoji", 26))
        self.canvas.create_text(100, 40, text="BIT ERRORS · IMAGE",
                                fill=TEXT_MAIN, anchor="w",
                                font=("Segoe UI", 20, "bold"))
        self.canvas.create_text(380, 44,
                                text="· ИСКАЖЕНИЕ ПИКСЕЛЕЙ БИТОВЫМИ ОШИБКАМИ",
                                fill=NEON_CYAN, anchor="w",
                                font=("Segoe UI", 11, "bold"))

        self.canvas.create_text(w - 60, 37, text=f"{self.fps:>3} FPS",
                                fill=TEXT_DIM, font=FONT_MONO_S, anchor="e")
        self.canvas.create_line(40, 70, w - 40, 70, fill=BORDER)

    # ---------- ИЗОБРАЖЕНИЯ ----------
    def _draw_images(self, w, y, h):
        panel_w = 380
        img_card_w = w - 100 - panel_w - 20

        # две картинки в одной карточке
        round_rect(self.canvas, 50, y, 50 + img_card_w, y + h, 14,
                   fill=BG_GLASS, outline=BORDER, width=1)

        self.canvas.create_text(70, y + 25, anchor="w",
                                text="▸ СРАВНЕНИЕ ИЗОБРАЖЕНИЙ",
                                fill=NEON_CYAN, font=FONT_LABEL)

        # размер каждой картинки
        img_size = min(int(h - 100), int((img_card_w - 80) / 2))

        x1 = 70
        x2 = 70 + img_size + 40
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
                                text="ПОСЛЕ ИСКАЖЕНИЙ",
                                fill=NEON_RED, font=FONT_LABEL_S)
        round_rect(self.canvas, x2 - 4, img_y - 4,
                   x2 + img_size + 4, img_y + img_size + 4, 8,
                   fill="#1a0508",
                   outline=lerp(NEON_RED, BG_DEEP, 0.4), width=2)

        # генерируем PhotoImage
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
        else:
            self.canvas.create_text(x1 + img_size / 2, img_y + img_size / 2,
                                    text="Pillow не установлен",
                                    fill=NEON_RED, font=FONT_LABEL)

    # ---------- МЕТРИКИ ----------
    def _draw_metrics(self, w, y, h):
        panel_w = 380
        img_card_w = w - 100 - panel_w - 20

        # 4 метрики в ряд
        m_gap = 12
        m_w = (img_card_w - 3 * m_gap) / 4

        metrics = [
            ("MSE",       f"{self.state.mse:.1f}",
             NEON_AMBER, "меньше = лучше"),
            ("PSNR",      f"{self.state.psnr:.2f} дБ",
             NEON_GREEN if self.state.psnr > 30 else
             (NEON_AMBER if self.state.psnr > 20 else NEON_RED),
             ">30 дБ — отлично"),
            ("SSIM",      f"{self.state.ssim:.4f}",
             NEON_CYAN if self.state.ssim > 0.9 else
             (NEON_AMBER if self.state.ssim > 0.7 else NEON_RED),
             "1.0 = идентичны"),
            ("ИСКАЖЕНО",  f"{self.state.diff_pct:.2f} %",
             NEON_PINK, "пикселей"),
        ]

        for i, (label, value, color, hint) in enumerate(metrics):
            mx = 50 + i * (m_w + m_gap)

            round_rect(self.canvas, mx, y,
                       mx + m_w, y + h, 10,
                       fill=BG_PANEL,
                       outline=lerp(color, BG_DEEP, 0.5), width=1)

            self.canvas.create_text(mx + 15, y + 22, anchor="w",
                                    text=label,
                                    fill=TEXT_DIM, font=FONT_LABEL_S)
            self.canvas.create_text(mx + 15, y + 55, anchor="w",
                                    text=value, fill=color,
                                    font=("Consolas", 18, "bold"))
            self.canvas.create_text(mx + 15, y + 82, anchor="w",
                                    text=hint, fill=TEXT_DIM,
                                    font=("Segoe UI", 8, "italic"))

    # ---------- ПАНЕЛЬ УПРАВЛЕНИЯ ----------
    def _draw_panel(self, w, y, h):
        panel_w = 380
        panel_x = w - 50 - panel_w

        round_rect(self.canvas, panel_x, y, panel_x + panel_w, y + h, 14,
                   fill=BG_GLASS, outline=lerp(NEON_PURP, BG_DEEP, 0.5),
                   width=2)

        self.canvas.create_text(panel_x + 20, y + 25, anchor="w",
                                text="▸ УПРАВЛЕНИЕ",
                                fill=NEON_PURP, font=FONT_LABEL)

        # === процент ошибок ===
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

        vmin, vmax = 0.0, 50.0
        k = (self.state.error_percent - vmin) / (vmax - vmin)
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
                                        vmin, vmax)

        # деления
        for j in range(6):
            kk = j / 5
            xx = bar_x0 + (bar_x1 - bar_x0) * kk
            val = int(vmin + (vmax - vmin) * kk)
            self.canvas.create_line(xx, bar_y + 16, xx, bar_y + 20,
                                    fill=TEXT_DIM, width=1)
            self.canvas.create_text(xx, bar_y + 30,
                                    text=f"{val}",
                                    fill=TEXT_DIM,
                                    font=("Consolas", 9, "bold"))

        # === быстрые кнопки ===
        qy = y + 170

        self.canvas.create_text(panel_x + 20, qy, anchor="w",
                                text="БЫСТРЫЙ ВЫБОР:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        q_vals = [(0.1, "0.1"), (0.5, "0.5"), (1, "1"),
                  (5, "5"), (10, "10"), (25, "25")]
        q_btn_w = 52
        q_btn_h = 34
        q_gap = 6
        q_start = panel_x + 20

        for i, (n, label) in enumerate(q_vals):
            bx = q_start + i * (q_btn_w + q_gap)
            active = abs(self.state.error_percent - n) < 0.01
            self._draw_q_btn(bx, qy + 20, q_btn_w, q_btn_h, label, n, active)

        # === паттерн изображения ===
        py = y + 250

        self.canvas.create_text(panel_x + 20, py, anchor="w",
                                text="ТИП ИЗОБРАЖЕНИЯ:",
                                fill=TEXT_DIM, font=FONT_LABEL_S)

        patterns = [
            ("photo",       "ФОТО",       NEON_CYAN),
            ("gradient",    "ГРАДИЕНТ",   NEON_GREEN),
            ("circles",     "КРУГИ",      NEON_AMBER),
            ("checkerboard","ШАХМАТЫ",    NEON_PINK),
            ("random",      "ШУМ",        NEON_RED),
        ]
        p_btn_w = 68
        p_btn_h = 34
        p_gap = 6
        p_start = panel_x + 20

        for i, (key, label, color) in enumerate(patterns):
            bx = p_start + i * (p_btn_w + p_gap)
            active = (self.state.pattern == key)
            self._draw_p_btn(bx, py + 20, p_btn_w, p_btn_h,
                              key, label, color, active)

        # === кнопки ===
        by = y + 340
        b_w = 160
        b_h = 44
        b_gap = 10

        self._draw_btn(panel_x + 20, by, b_w, b_h,
                       "🎲 ПЕРЕСОЗДАТЬ ШУМ", NEON_PURP, "renoise")
        self._draw_btn(panel_x + 20 + b_w + b_gap, by, b_w, b_h,
                       "↺ НОВОЕ ИЗОБР.", NEON_RED, "new_image")

        # === информационный блок ===
        info_y = y + 405
        info_h = h - (info_y - y) - 20

        round_rect(self.canvas, panel_x + 20, info_y,
                   panel_x + panel_w - 20, info_y + info_h, 10,
                   fill=BG_PANEL,
                   outline=lerp(NEON_CYAN, BG_DEEP, 0.5), width=1)

        self.canvas.create_text(panel_x + panel_w / 2, info_y + 22,
                                text="КАК ЭТО РАБОТАЕТ",
                                fill=NEON_CYAN,
                                font=FONT_LABEL_S)

        info_lines = [
            "Изображение передаётся по каналу,",
            "в котором случайно инвертируются",
            "отдельные биты пикселей.",
            "",
            "Процент ошибок показывает,",
            "какая доля бит будет испорчена.",
            "",
            "PSNR > 30 дБ — картинка неотличима,",
            "PSNR 20-30 — заметные искажения,",
            "PSNR < 20 — сигнал разрушен.",
        ]

        ly = info_y + 45
        for line in info_lines:
            if line:
                self.canvas.create_text(panel_x + 35, ly, anchor="w",
                                        text=line, fill=TEXT_DIM,
                                        font=("Consolas", 9))
            ly += 16

    def _draw_btn(self, x, y, w, h, text, color, key):
        round_rect(self.canvas, x, y, x + w, y + h, 8,
                   fill=lerp(color, BG_DEEP, 0.8),
                   outline=color, width=1)
        self.canvas.create_text(x + w / 2, y + h / 2,
                                text=text, fill=color,
                                font=("Segoe UI", 10, "bold"))
        self.btn_zones[key] = (x, y, x + w, y + h)

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
                                    font=("Segoe UI", 9, "bold"))
        else:
            round_rect(self.canvas, x, y, x + w, y + h, 6,
                       fill="#0f141c", outline="#2a3040", width=1)
            self.canvas.create_text(x + w / 2, y + h / 2,
                                    text=label, fill=TEXT_DIM,
                                    font=("Segoe UI", 9, "bold"))
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

        # изображения — верхняя часть
        img_y = 90
        img_h = h - 90 - 200
        self._draw_images(w, img_y, img_h)

        # метрики — под изображениями
        met_y = img_y + img_h + 15
        self._draw_metrics(w, met_y, 100)

        # панель справа — на всю высоту
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
        if key == "renoise":
            self.state.apply_noise()
        elif key == "new_image":
            self.state.regenerate_original()
        elif key.startswith("q_"):
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