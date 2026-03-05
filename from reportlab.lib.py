from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os, zipfile, math

# ============================================================
# Configuration
# ============================================================
PAGE_W, PAGE_H = A4
MARGIN = 15  # 5 mm printable margin
OUTPUT_DIR = "Red_AI_Robot_Papercraft_v1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PAGES = [
    "Head Front (OLED + ESP32)",
    "Head Back + Sides",
    "Body Front (Blue Chest + Ultrasonic)",
    "Body Back + Sides (Arduino + Driver)",
    "Arms (Left + Right)",
    "Base (Motors + Free Wheel)",
    "Decorations + Spare Tabs"
]

BROWN = colors.Color(0.86, 0.74, 0.57)
BLUE = colors.Color(0.3, 0.5, 0.85)
WHITE = colors.white
BLACK = colors.black


# ============================================================
# Helpers
# ============================================================
def draw_fold_line(c, x1, y1, x2, y2):
    c.setStrokeColor(BLACK)
    c.setDash(4, 4)
    c.line(x1, y1, x2, y2)
    c.setDash(1, 0)

def draw_cut_line(c, x1, y1, x2, y2):
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.2)
    c.line(x1, y1, x2, y2)

def draw_oval(c, x, y, w, h, stroke=1, fill=0, color=BLACK):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.ellipse(x, y, x + w, y + h, stroke=stroke, fill=fill)

def add_label(c, text, x, y, color=BLACK, size=10):
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    c.drawString(x, y, text)


# ============================================================
# Page renderer
# ============================================================
def draw_template(c, title):
    # Background
    c.setFillColor(BROWN)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Blue header band
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - 60, PAGE_W, 60, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_W/2, PAGE_H - 40, f"Red AI Robot Papercraft v1 — {title}")

    # Margin box
    c.setStrokeColor(BLACK)
    c.rect(MARGIN, MARGIN, PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN, stroke=1, fill=0)

    # Common note
    add_label(c, "Solid = Cut, Dashed = Fold, Tabs ≈10mm", 90, 70, BLACK, 9)
    add_label(c, "Match labels (A↔A, B↔B)", 90, 55, BLACK, 9)


    # ==== PER-PAGE DRAWINGS ====
    if "Head Front" in title:
        # Oval head + OLED cutouts + ESP32 label
        draw_oval(c, 100, 450, 300, 180, stroke=1, fill=0)
        add_label(c, "[Oval Head Outline]", 180, 640, BLACK, 10)
        # OLED eye holes
        c.setFillColor(colors.white)
        c.rect(170, 540, 30, 30, stroke=1, fill=0)
        c.rect(300, 540, 30, 30, stroke=1, fill=0)
        add_label(c, "[OLED 0.96\" Eyes 30×30 mm]", 160, 515, BLACK, 9)
        add_label(c, "ESP32 Mount Zone", 180, 490, BLACK, 9)

    elif "Head Back" in title:
        draw_oval(c, 110, 440, 280, 170, stroke=1, fill=0)
        add_label(c, "[Head Back Shape + Side Tabs]", 150, 630)
        draw_fold_line(c, 120, 430, 380, 430)
        add_label(c, "Neck Connector Tabs", 170, 410)

    elif "Body Front" in title:
        # Main rectangle
        c.rect(100, 200, 320, 240, stroke=1, fill=0)
        # Blue chest area
        c.setFillColor(BLUE)
        c.roundRect(150, 270, 220, 100, 20, stroke=0, fill=1)
        add_label(c, "[Blue Chest Panel]", 180, 250, WHITE, 10)
        add_label(c, "[Ultrasonic Sensor Slot (50×25 mm)]", 150, 230, BLACK, 9)

    elif "Body Back" in title:
        c.rect(100, 200, 320, 240, stroke=1, fill=0)
        add_label(c, "Arduino UNO Mount (69×54 mm)", 150, 420, BLACK, 9)
        add_label(c, "Motor Driver L298N Mount (43×43 mm)", 150, 400, BLACK, 9)
        add_label(c, "Battery Holder Zone", 150, 370, BLACK, 9)

    elif "Arms" in title:
        # Two curved arms
        c.setFillColor(BLUE)
        draw_oval(c, 80, 300, 100, 200, stroke=1, fill=0)
        draw_oval(c, 340, 300, 100, 200, stroke=1, fill=0)
        add_label(c, "[Left Arm]", 100, 280, BLACK)
        add_label(c, "[Right Arm]", 360, 280, BLACK)

    elif "Base" in title:
        # Oval base + motor cutouts
        draw_oval(c, 100, 220, 320, 150, stroke=1, fill=0)
        add_label(c, "[Base Outline (oval)]", 170, 390)
        # Motor holes
        c.setFillColor(colors.white)
        c.rect(130, 260, 30, 25, stroke=1, fill=0)
        c.rect(350, 260, 30, 25, stroke=1, fill=0)
        add_label(c, "DC Motor × 2", 180, 250)
        # Free wheel
        draw_oval(c, 240, 240, 40, 20, stroke=1, fill=0)
        add_label(c, "Free Wheel", 230, 225)

    elif "Decorations" in title:
        c.setFillColor(BLUE)
        c.roundRect(150, 450, 220, 100, 20, stroke=0, fill=1)
        draw_oval(c, 170, 300, 40, 40, stroke=1, fill=1)
        draw_oval(c, 290, 300, 40, 40, stroke=1, fill=1)
        add_label(c, "[Blue Overlays / Spare Tabs]", 160, 260, WHITE, 10)

    # Reset fill color
    c.setFillColor(BLACK)

# ============================================================
# Generate all pages + zip
# ============================================================
for page_title in PAGES:
    pdf_path = os.path.join(OUTPUT_DIR, f"{page_title.replace(' ', '_')}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    draw_template(c, page_title)
    c.showPage()
    c.save()

zip_path = f"{OUTPUT_DIR}.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            fp = os.path.join(root, f)
            zf.write(fp, os.path.relpath(fp, OUTPUT_DIR))

print(f"\n✅ 7 A4 templates generated in '{OUTPUT_DIR}/' and zipped to '{zip_path}'.")
print("➡  Print each PDF at 100 % scale to build your 47–50 cm Red AI Robot Papercraft v1.")