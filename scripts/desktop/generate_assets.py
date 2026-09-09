import os
import pathlib
from PIL import Image, ImageDraw, ImageFont

def generate_assets():
    base_dir = pathlib.Path(r"e:\dentalcare-pro")
    assets_dir = base_dir / "assets" / "branding"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate 512x512 Master App Icon
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rectangle: Medical Teal gradient base (#0f766e)
    bg_color = (15, 118, 110, 255) # #0f766e
    border_color = (45, 212, 191, 255) # #2dd4bf
    draw.rounded_rectangle([16, 16, size - 16, size - 16], radius=96, fill=bg_color, outline=border_color, width=8)

    # Cross emblem
    cross_color = (255, 255, 255, 255)
    accent_cyan = (6, 182, 212, 255) # #06b6d4

    # Horizontal bar of cross
    draw.rounded_rectangle([116, 206, size - 116, 306], radius=24, fill=cross_color)
    # Vertical bar of cross
    draw.rounded_rectangle([206, 116, 306, size - 116], radius=24, fill=cross_color)

    # Central tooth contour or clinical blue core
    draw.rounded_rectangle([226, 226, 286, 286], radius=16, fill=accent_cyan)

    # Save 512x512 PNG
    png_path = assets_dir / "app_icon.png"
    img.save(png_path, format="PNG")
    print(f"Generated {png_path}")

    # 2. Generate Multi-Resolution Windows ICO
    ico_path = assets_dir / "app_icon.ico"
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"Generated {ico_path} with sizes {ico_sizes}")

    # 3. Generate 600x360 Splash Screen
    splash_w, splash_h = 600, 360
    splash = Image.new("RGB", (splash_w, splash_h), (15, 23, 42)) # Deep Slate #0f172a
    s_draw = ImageDraw.Draw(splash)

    # Decorative top border in Teal
    s_draw.rectangle([0, 0, splash_w, 6], fill=(15, 118, 110))

    # Draw mini logo
    mini_icon = img.resize((96, 96), Image.Resampling.LANCZOS)
    splash.paste(mini_icon, (splash_w // 2 - 48, 50), mini_icon)

    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_sub = ImageFont.truetype("arial.ttf", 14)
        font_status = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font_title = font_sub = font_status = ImageFont.load_default()

    s_draw.text((splash_w // 2, 175), "DentalCare Pro", fill=(255, 255, 255), font=font_title, anchor="mm")
    s_draw.text((splash_w // 2, 210), "Enterprise Dental Practice Management System (v1.0.0)", fill=(148, 163, 184), font=font_sub, anchor="mm")
    s_draw.text((splash_w // 2, 280), "Starting local services & verifying database...", fill=(45, 212, 191), font=font_status, anchor="mm")

    # Progress bar outline
    bar_x1, bar_y1, bar_x2, bar_y2 = 120, 305, splash_w - 120, 313
    s_draw.rounded_rectangle([bar_x1, bar_y1, bar_x2, bar_y2], radius=4, fill=(30, 41, 59), outline=(51, 65, 85))
    s_draw.rounded_rectangle([bar_x1, bar_y1, bar_x1 + 220, bar_y2], radius=4, fill=(15, 118, 110))

    splash_path = assets_dir / "splash_screen.png"
    splash.save(splash_path, format="PNG")
    print(f"Generated {splash_path}")

    # 4. Generate Inno Setup BMPs (WizardImageFile 164x314, WizardSmallImageFile 55x55)
    banner = Image.new("RGB", (164, 314), (15, 118, 110)) # Teal
    b_draw = ImageDraw.Draw(banner)
    b_icon = img.resize((80, 80), Image.Resampling.LANCZOS)
    banner.paste(b_icon, (42, 60), b_icon)
    b_draw.text((82, 165), "DentalCare", fill=(255, 255, 255), font=font_sub, anchor="mm")
    b_draw.text((82, 185), "Pro", fill=(45, 212, 191), font=font_sub, anchor="mm")
    banner_path = assets_dir / "installer_banner.bmp"
    banner.save(banner_path, format="BMP")
    print(f"Generated {banner_path}")

    small_logo = img.resize((48, 48), Image.Resampling.LANCZOS)
    small_bmp = Image.new("RGB", (55, 55), (255, 255, 255))
    small_bmp.paste(small_logo, (3, 3), small_logo)
    small_path = assets_dir / "installer_small.bmp"
    small_bmp.save(small_path, format="BMP")
    print(f"Generated {small_path}")

if __name__ == "__main__":
    generate_assets()
