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

# Edge-to-edge black bezel; module green kept, wells brightened
BEZEL_HI = (42, 42, 42, 255)
BEZEL_MID = (18, 18, 18, 255)
BEZEL_LO = (6, 6, 6, 255)
LCD_BG = (52, 58, 52, 255)       # #343a34 module (unchanged)
LCD_FACE = (122, 136, 112, 255)  # #7a8870 brighter wells
SEG = (18, 24, 14, 255)
SEG_GHOST = (58, 68, 54, 255)    # #3a4436 — readable on bright wells
CASE = (8, 8, 8, 255)

# Geometry (absolute coords on 390x450) — match prototype grid:
# left dial | right column (BAT + HR same width) | full-width bottom
BEZEL = (2, 2, 386, 446)
LCD = (16, 16, 358, 418)

DIAL_CX, DIAL_CY, DIAL_R = 106, 122, 84  # larger step wheel (~168px face)
# Right column shared width (HTML grid: both wells same 1fr column)
BAT_BOX = (206, 46, 156, 56)
HR_BOX = (206, 114, 156, 102)
BOTTOM = (28, 236, 334, 168)  # main timekeeping well

WEEKDAY_POS = (48, 252)
MONTH_POS = (170, 252)
TIME_HOUR = (48, 300)
TIME_MIN = (170, 300)
COLON_POS = (150, 305)
PM_POS = (310, 258)

# Step count centered in dial (small digits 18×28; sample "8432" → 4×18+3)
STEP_VAL_POS = (DIAL_CX - (4 * 18 + 3) // 2, DIAL_CY - 28 // 2)
# large digits in HR well
HR_VAL_POS = (HR_BOX[0] + (HR_BOX[2] - 3 * 34) // 2, HR_BOX[1] + 28)
# battery icon centered in BAT_BOX
BAT_ICON_W, BAT_ICON_H = 116, 28
BAT_VAL_POS = (
    BAT_BOX[0] + (BAT_BOX[2] - BAT_ICON_W) // 2,
    BAT_BOX[1] + (BAT_BOX[3] - BAT_ICON_H) // 2 + 4,  # sit under BAT label
)
PROGRESS_SIZE = 176


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
    """10 frames for battery level 0..100 via IMG_LEVEL."""
    for i in range(10):
        im = Image.new("RGBA", (BAT_ICON_W, BAT_ICON_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # body — scaled to wider BAT well (same width as HR)
        body_r = BAT_ICON_W - 10
        d.rectangle((2, 6, body_r, 24), outline=SEG, width=2)
        # nub
        d.rectangle((body_r, 10, BAT_ICON_W - 2, 20), fill=SEG)
        # fill
        fill_max = body_r - 10
        fill_w = int(fill_max * i / 9) if i > 0 else 0
        if fill_w > 0:
            d.rectangle((6, 10, 6 + fill_w, 20), fill=SEG)
        im.save(OUT / "battery" / f"{i}.png")


def make_progress_frames() -> None:
    size = PROGRESS_SIZE
    cx = cy = size // 2
    r = DIAL_R - 4
    width = 8
    for i in range(10):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=SEG_GHOST, width=width)
        extent = int(360 * i / 9) if i > 0 else 0
        if extent > 0:
            d.arc((cx - r, cy - r, cx + r, cy + r), start=-90, end=-90 + extent, fill=SEG, width=width)
        im.save(OUT / "progress" / f"{i}.png")


def make_ui() -> None:
    Image.new("RGBA", (PROGRESS_SIZE, PROGRESS_SIZE), (0, 0, 0, 0)).save(OUT / "ui" / "tap_step.png")
    hx, hy, hw, hh = HR_BOX
    Image.new("RGBA", (hw, hh), (0, 0, 0, 0)).save(OUT / "ui" / "tap_hr.png")
    im = Image.new("RGBA", (18, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 12, 7, 16), fill=SEG)
    d.rectangle((11, 12, 16, 16), fill=SEG)
    im.save(OUT / "font" / "invalid.png")


def black_bezel(draw: ImageDraw.ImageDraw, box) -> None:
    x, y, w, h = box
    # Large radii for edge-to-edge bezel on Bip 6 screen
    draw.rounded_rectangle((x, y, x + w, y + h), radius=84, fill=BEZEL_MID)
    draw.rounded_rectangle((x + 3, y + 3, x + w - 3, y + h - 3), radius=82, fill=BEZEL_HI)
    draw.rounded_rectangle((x + 8, y + 8, x + w - 8, y + h - 8), radius=78, fill=BEZEL_MID)
    draw.rounded_rectangle((x + 12, y + 12, x + w - 12, y + h - 12), radius=74, fill=BEZEL_LO)
    draw.rounded_rectangle((x + 14, y + 14, x + w - 14, y + h - 14), radius=72, fill=LCD_BG)


def make_background() -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Bip 6 black case under bezel
    draw.rounded_rectangle((0, 0, W - 1, H - 1), radius=RADIUS, fill=CASE)
    draw.rounded_rectangle((2, 2, W - 3, H - 3), radius=RADIUS - 2, outline=(36, 36, 36, 255), width=2)

    black_bezel(draw, BEZEL)

    # LCD wells
    lx, ly, lw, lh = LCD
    draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), radius=70, fill=LCD_BG)

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
        inner = DIAL_R - (14 if i % 5 == 0 else 8)
        outer = DIAL_R - 1
        x1 = DIAL_CX + inner * math.cos(ang)
        y1 = DIAL_CY + inner * math.sin(ang)
        x2 = DIAL_CX + outer * math.cos(ang)
        y2 = DIAL_CY + outer * math.sin(ang)
        draw.line((x1, y1, x2, y2), fill=SEG if i % 5 == 0 else SEG_GHOST, width=2 if i % 5 == 0 else 1)

    # top-right battery well
    bx0, by0, bw0, bh0 = BAT_BOX
    draw.rounded_rectangle(
        (bx0, by0, bx0 + bw0, by0 + bh0), radius=14, fill=LCD_FACE, outline=SEG_GHOST, width=1
    )

    # map / HR well
    hx, hy, hw, hh = HR_BOX
    draw.rounded_rectangle(
        (hx, hy, hx + hw, hy + hh), radius=14, fill=LCD_FACE, outline=SEG_GHOST, width=1
    )

    # bottom timekeeping well
    tx, ty, tw, th = BOTTOM
    draw.rounded_rectangle(
        (tx, ty, tx + tw, ty + th), radius=16, fill=LCD_FACE, outline=SEG_GHOST, width=1
    )

    # Printed glass labels
    font_tiny = try_font(8, True)
    draw.text((lx + 8, ty - 14), "WR100M", font=font_tiny, fill=SEG)
    draw.text((hx + hw - 48, hy + 8), "CASIO", font=font_tiny, fill=SEG)
    draw.text((tx + 90, ty + th + 4), "10 YEAR BATTERY", font=font_tiny, fill=SEG)

    # Section captions (STEP omitted so the count can sit centered in the dial)
    font_lab = try_font(9, True)
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

    paste(OUT / "progress" / "6.png", (DIAL_CX - PROGRESS_SIZE // 2, DIAL_CY - PROGRESS_SIZE // 2))
    for i, ch in enumerate("8432"):
        paste(OUT / "font" / "small" / f"{ch}.png", (STEP_VAL_POS[0] + i * 19, STEP_VAL_POS[1]))
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
