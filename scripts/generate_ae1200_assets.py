#!/usr/bin/env python3
"""Generate AE-1200WHD-1AV-style assets for Amazfit Bip 6 (390x450).

Visual target: dark partitioned LCD (Casio AE-1200WHD-1AV).
Data mapping:
  top-left dial  -> step goal progress
  top-right      -> battery
  map area       -> heart rate
  bottom         -> day, date, HH:MM (no seconds)
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "390x450-amazfit-bip-6"
PROTO = ROOT / "prototype"
REF = ROOT / "reference" / "ae1200-1.jpg"

W, H = 390, 450
RADIUS = 86  # Bip 6 screen corner radius

# Black bezel + original lighter LCD green
BEZEL_HI = (42, 42, 42, 255)
BEZEL_MID = (18, 18, 18, 255)
BEZEL_LO = (6, 6, 6, 255)
LCD_BG = (52, 58, 52, 255)       # lighter olive module (previous)
LCD_FACE = (72, 82, 68, 255)     # lighter wells (previous)
SEG = (18, 24, 14, 255)
SEG_GHOST = (40, 48, 36, 255)
CASE = (8, 8, 8, 255)

# Geometry (absolute coords on 390x450)
BEZEL = (18, 28, 354, 394)  # x,y,w,h — silver frame
LCD = (40, 70, 310, 300)    # dark LCD inset

DIAL_CX, DIAL_CY, DIAL_R = 105, 145, 52
BAT_BOX = (248, 78, 88, 48)     # top-right indicator well
HR_BOX = (210, 135, 126, 78)    # former map well
BOTTOM = (48, 230, 294, 128)    # main timekeeping well

WEEKDAY_POS = (70, 242)
MONTH_POS = (175, 242)
TIME_HOUR = (70, 280)
TIME_MIN = (178, 280)
COLON_POS = (158, 285)
PM_POS = (290, 250)

STEP_VAL_POS = (78, 155)
HR_VAL_POS = (218, 155)
# battery icon 72x28 centered in BAT_BOX
BAT_VAL_POS = (248 + (88 - 72) // 2, 78 + (48 - 28) // 2)  # (256, 88)


def ensure_dirs() -> None:
    for p in [
        OUT / "bg",
        OUT / "font" / "large",
        OUT / "font" / "small",
        OUT / "font" / "tiny",
        OUT / "week",
        OUT / "ampm",
        OUT / "ui",
        OUT / "progress",
        OUT / "battery",
    ]:
        p.mkdir(parents=True, exist_ok=True)


def try_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    cands = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in cands:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_seven_seg(draw, digit, box, color, thickness):
    x0, y0, x1, y1 = box
    t = thickness
    pad = max(2, t // 2)
    mx, my, Mw, Mh = x0 + pad, y0 + pad, x1 - pad, y1 - pad
    mid = (y0 + y1) // 2
    segs = {
        "a": (mx + t, my, Mw - t, my + t),
        "b": (Mw - t, my + t, Mw, mid - t // 2),
        "c": (Mw - t, mid + t // 2, Mw, Mh - t),
        "d": (mx + t, Mh - t, Mw - t, Mh),
        "e": (mx, mid + t // 2, mx + t, Mh - t),
        "f": (mx, my + t, mx + t, mid - t // 2),
        "g": (mx + t, mid - t // 2, Mw - t, mid + t // 2),
    }
    map_d = {
        "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
        "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    }
    for s in map_d.get(digit, ""):
        draw.rectangle(segs[s], fill=color)


def make_digit_sheet(size, thickness, out_dir: Path) -> None:
    dw, dh = size
    for d in "0123456789":
        im = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        draw_seven_seg(draw, d, (1, 1, dw - 1, dh - 1), SEG, thickness)
        im.save(out_dir / f"{d}.png")


def make_colon(path: Path) -> None:
    im = Image.new("RGBA", (16, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((4, 14, 12, 22), fill=SEG)
    d.rectangle((4, 38, 12, 46), fill=SEG)
    im.save(path)


def make_dash(path: Path) -> None:
    im = Image.new("RGBA", (12, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((1, 12, 11, 16), fill=SEG)
    im.save(path)


def text_image(text: str, size: int, out: Path, fill=SEG, padding=(3, 2)) -> None:
    font = try_font(size, True)
    tmp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    im = Image.new("RGBA", (tw + padding[0] * 2, th + padding[1] * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.text((padding[0] - bbox[0], padding[1] - bbox[1]), text, font=font, fill=fill)
    im.save(out)


def make_weekdays() -> None:
    # AE-1200 uses 3-letter days
    for name, label in [
        ("mon", "MON"), ("tue", "TUE"), ("wed", "WED"), ("thu", "THU"),
        ("fri", "FRI"), ("sat", "SAT"), ("sun", "SUN"),
    ]:
        text_image(label, 22, OUT / "week" / f"{name}.png")


def make_labels() -> None:
    text_image("PM", 12, OUT / "ampm" / "pm.png")
    text_image("AM", 12, OUT / "ampm" / "am.png")


def make_battery_frames() -> None:
    """10 frames for battery level 0..100 via IMG_PROGRESS."""
    for i in range(10):
        im = Image.new("RGBA", (72, 28), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # body
        d.rectangle((2, 6, 62, 24), outline=SEG, width=2)
        # nub
        d.rectangle((62, 10, 68, 20), fill=SEG)
        # fill
        fill_w = int(52 * i / 9) if i > 0 else 0
        if fill_w > 0:
            d.rectangle((6, 10, 6 + fill_w, 20), fill=SEG)
        im.save(OUT / "battery" / f"{i}.png")


def make_progress_frames() -> None:
    size = 120
    cx = cy = size // 2
    r = 48
    width = 7
    for i in range(10):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=SEG_GHOST, width=width)
        extent = int(360 * i / 9) if i > 0 else 0
        if extent > 0:
            d.arc((cx - r, cy - r, cx + r, cy + r), start=-90, end=-90 + extent, fill=SEG, width=width)
        im.save(OUT / "progress" / f"{i}.png")


def make_ui() -> None:
    Image.new("RGBA", (120, 120), (0, 0, 0, 0)).save(OUT / "ui" / "tap_step.png")
    Image.new("RGBA", (130, 90), (0, 0, 0, 0)).save(OUT / "ui" / "tap_hr.png")
    im = Image.new("RGBA", (18, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 12, 7, 16), fill=SEG)
    d.rectangle((11, 12, 16, 16), fill=SEG)
    im.save(OUT / "font" / "invalid.png")


def black_bezel(draw: ImageDraw.ImageDraw, box) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=BEZEL_MID)
    draw.rounded_rectangle((x + 3, y + 3, x + w - 3, y + h - 3), radius=16, fill=BEZEL_HI)
    draw.rounded_rectangle((x + 8, y + 8, x + w - 8, y + h - 8), radius=14, fill=BEZEL_MID)
    # inner recess for LCD (tighter — no room reserved for bezel text)
    draw.rounded_rectangle((x + 12, y + 12, x + w - 12, y + h - 12), radius=6, fill=BEZEL_LO)
    draw.rounded_rectangle((x + 14, y + 14, x + w - 14, y + h - 14), radius=5, fill=LCD_BG)


def make_background() -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Bip 6 black case under bezel
    draw.rounded_rectangle((0, 0, W - 1, H - 1), radius=RADIUS, fill=CASE)
    draw.rounded_rectangle((2, 2, W - 3, H - 3), radius=RADIUS - 2, outline=(36, 36, 36, 255), width=2)

    # faux side buttons (kept)
    draw.rectangle((0, 108, 7, 140), fill=(55, 55, 55, 255))
    draw.rectangle((0, 198, 7, 250), fill=(55, 55, 55, 255))
    draw.rectangle((W - 7, 150, W - 1, 196), fill=(55, 55, 55, 255))

    bx, by, bw, bh = BEZEL
    black_bezel(draw, BEZEL)

    # LCD wells
    lx, ly, lw, lh = LCD
    draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), radius=4, fill=LCD_BG)

    # top-left dial well (circular)
    draw.ellipse(
        (DIAL_CX - DIAL_R - 4, DIAL_CY - DIAL_R - 4, DIAL_CX + DIAL_R + 4, DIAL_CY + DIAL_R + 4),
        fill=LCD_FACE,
        outline=SEG_GHOST,
        width=2,
    )
    # tick marks (AE-1200 analog-style dial)
    for i in range(60):
        ang = math.radians(i * 6 - 90)
        inner = DIAL_R - (11 if i % 5 == 0 else 7)
        outer = DIAL_R - 1
        x1 = DIAL_CX + inner * math.cos(ang)
        y1 = DIAL_CY + inner * math.sin(ang)
        x2 = DIAL_CX + outer * math.cos(ang)
        y2 = DIAL_CY + outer * math.sin(ang)
        draw.line((x1, y1, x2, y2), fill=SEG if i % 5 == 0 else SEG_GHOST, width=2 if i % 5 == 0 else 1)

    # top-right battery well
    bx0, by0, bw0, bh0 = BAT_BOX
    draw.rectangle((bx0, by0, bx0 + bw0, by0 + bh0), fill=LCD_FACE, outline=SEG_GHOST, width=1)

    # map / HR well
    hx, hy, hw, hh = HR_BOX
    draw.rectangle((hx, hy, hx + hw, hy + hh), fill=LCD_FACE, outline=SEG_GHOST, width=1)

    # bottom timekeeping well
    tx, ty, tw, th = BOTTOM
    draw.rectangle((tx, ty, tx + tw, ty + th), fill=LCD_FACE, outline=SEG_GHOST, width=1)

    # Printed glass labels
    font_tiny = try_font(8, True)
    draw.text((lx + 8, ty - 14), "WR100M", font=font_tiny, fill=SEG)
    draw.text((lx + lw - 70, hy + hh // 2 - 4), "CASIO", font=font_tiny, fill=SEG)
    draw.text((tx + 70, ty + th + 4), "10 YEAR BATTERY", font=font_tiny, fill=SEG)

    # Section captions
    font_lab = try_font(9, True)
    draw.text((DIAL_CX - 18, DIAL_CY - 18), "STEP", font=font_lab, fill=SEG)
    draw.text((hx + 6, hy + 4), "HR", font=font_lab, fill=SEG)
    # BAT label centered in battery well
    bat_lab = "BAT"
    bb = draw.textbbox((0, 0), bat_lab, font=font_lab)
    bat_tw = bb[2] - bb[0]
    draw.text((bx0 + (bw0 - bat_tw) // 2, by0 + 4), bat_lab, font=font_lab, fill=SEG)

    return im


def make_preview(bg: Image.Image) -> None:
    preview = bg.copy()

    def paste(path: Path, pos):
        if path.exists():
            preview.alpha_composite(Image.open(path).convert("RGBA"), dest=pos)

    paste(OUT / "progress" / "6.png", (DIAL_CX - 60, DIAL_CY - 60))
    for i, ch in enumerate("8432"):
        paste(OUT / "font" / "tiny" / f"{ch}.png", (STEP_VAL_POS[0] + i * 14, STEP_VAL_POS[1]))
    paste(OUT / "battery" / "8.png", BAT_VAL_POS)
    for i, ch in enumerate("072"):
        paste(OUT / "font" / "large" / f"{ch}.png", (HR_VAL_POS[0] + i * 34, HR_VAL_POS[1]))
    paste(OUT / "week" / "sun.png", WEEKDAY_POS)
    paste(OUT / "font" / "small" / "0.png", MONTH_POS)
    paste(OUT / "font" / "small" / "6.png", (MONTH_POS[0] + 20, MONTH_POS[1]))
    paste(OUT / "font" / "dash.png", (MONTH_POS[0] + 42, MONTH_POS[1] + 2))
    paste(OUT / "font" / "small" / "3.png", (MONTH_POS[0] + 54, MONTH_POS[1]))
    paste(OUT / "font" / "small" / "0.png", (MONTH_POS[0] + 74, MONTH_POS[1]))
    paste(OUT / "font" / "large" / "1.png", TIME_HOUR)
    paste(OUT / "font" / "large" / "0.png", (TIME_HOUR[0] + 46, TIME_HOUR[1]))
    paste(OUT / "font" / "colon.png", COLON_POS)
    paste(OUT / "font" / "large" / "0.png", TIME_MIN)
    paste(OUT / "font" / "large" / "8.png", (TIME_MIN[0] + 46, TIME_MIN[1]))
    paste(OUT / "ampm" / "pm.png", PM_POS)

    PROTO.mkdir(parents=True, exist_ok=True)
    preview.save(PROTO / "preview-390x450.png")
    # Official Zepp OS 2.0 watchface icon is 64×64
    preview.resize((64, 64), Image.Resampling.LANCZOS).save(OUT / "icon.png")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    ensure_dirs()

    make_digit_sheet((44, 60), 7, OUT / "font" / "large")
    make_digit_sheet((18, 28), 3, OUT / "font" / "small")
    make_digit_sheet((12, 18), 2, OUT / "font" / "tiny")
    make_colon(OUT / "font" / "colon.png")
    make_dash(OUT / "font" / "dash.png")
    make_weekdays()
    make_labels()
    make_battery_frames()
    make_progress_frames()
    make_ui()

    bg = make_background()
    bg.save(OUT / "bg" / "bg.png")
    make_preview(bg)
    print(f"Wrote {OUT}")
    print(f"Wrote {PROTO / 'preview-390x450.png'}")
    if REF.exists():
        print(f"Reference used for style: {REF}")


if __name__ == "__main__":
    main()
