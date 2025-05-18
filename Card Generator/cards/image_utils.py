from PIL import Image, ImageDraw, ImageFont
import os
from utils.font_settings import get_font_settings

CARD_SIZE = (768, 1152)
TITLE_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BODY_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Helper to draw styled text with Pillow
def draw_styled_text(draw, text, xy, font, fill, settings, underline=False, shadow=False, letter_spacing=0, line_spacing=0):
    x, y = xy
    lines = text.split('\n')
    for line in lines:
        orig_line = line
        if settings.get("all_caps"):
            line = line.upper()
        # Letter spacing
        if letter_spacing != 0:
            # Draw each character with extra spacing
            cx = x
            for char in line:
                if shadow:
                    draw.text((cx+2, y+2), char, font=font, fill="#444444")
                draw.text((cx, y), char, font=font, fill=fill)
                bbox = draw.textbbox((0, 0), char, font=font)
                char_w = bbox[2] - bbox[0]
                cx += char_w + letter_spacing
            line_w = cx - x
        else:
            if shadow:
                draw.text((x+2, y+2), line, font=font, fill="#444444")
            draw.text((x, y), line, font=font, fill=fill)
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
        # Underline
        if settings.get("underline") or underline:
            bbox = draw.textbbox((0, 0), line, font=font)
            underline_y = y + (bbox[3] - bbox[1]) + 2
            draw.line((x, underline_y, x + line_w, underline_y), fill=fill, width=2)
        y += (bbox[3] - bbox[1]) + (line_spacing or 0)

# Helper to draw a banner for the subtype
def draw_banner(draw, text, y, width, font, fill_bg=(40,40,40,255), fill_fg="white", settings=None):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 30, 10
    banner_h = text_h + pad_y*2
    banner_w = text_w + pad_x*2
    x = 40
    draw.rectangle([x, y, x+banner_w, y+banner_h], fill=fill_bg)
    draw_styled_text(draw, text, (x+pad_x, y+pad_y), font, fill_fg, settings or {}, underline=False)
    return y + banner_h + 10

def overlay_card(image_path, output_path, title, subtype, back_text="", mode="front", font_path=None, card_type=None):
    # Use a blank image as the template
    img = Image.new("RGBA", CARD_SIZE, (235, 210, 150, 255))  # light tan background
    draw = ImageDraw.Draw(img)
    # Debug: print font path
    print("[DEBUG] overlay_card: Using per-part font settings from config.")
    # Load font settings for this card type
    def get_font(part, default_path, default_size, bold=False, italic=False):
        settings = get_font_settings(card_type or "players", part)
        size = settings.get("size", default_size)
        font_file = settings.get("font_file")
        try:
            if font_file and os.path.exists(os.path.join("fonts", font_file)):
                path = os.path.join("fonts", font_file)
            else:
                path = default_path
            return ImageFont.truetype(path, size)
        except Exception as e:
            print(f"[ERROR] Could not load font '{font_file}': {e}. Using default font.")
            return ImageFont.load_default()
    def get_color(part, default):
        settings = get_font_settings(card_type or "players", part)
        return settings.get("color", default)
    def get_xy(part, default_x, default_y):
        settings = get_font_settings(card_type or "players", part)
        return settings.get("x", default_x), settings.get("y", default_y)
    def get_style(part):
        return get_font_settings(card_type or "players", part)
    try:
        title_font = get_font("title", TITLE_FONT_PATH, 80)
        sub_font = get_font("subtype", TITLE_FONT_PATH, 40)
        body_font = get_font("body", BODY_FONT_PATH, 32)
        stats_font = get_font("stats", BODY_FONT_PATH, 28)
    except Exception as e:
        print(f"[ERROR] Could not load font: {e}. Using default font.")
        title_font = sub_font = body_font = stats_font = ImageFont.load_default()
    if mode == "front":
        # Title (large, bold, all-caps, etc.)
        title_text = title
        title_settings = get_style("title")
        if title_settings.get("all_caps"): title_text = title_text.upper()
        title_x, title_y = get_xy("title", (CARD_SIZE[0]-600)//2, 60)
        draw_styled_text(draw, title_text, (title_x, title_y), title_font, get_color("title", "black"), title_settings, underline=title_settings.get("underline"), shadow=title_settings.get("shadow"), letter_spacing=title_settings.get("letter_spacing", 0), line_spacing=title_settings.get("line_spacing", 0))
        # Subtype banner
        if subtype:
            sub_settings = get_style("subtype")
            sub_x, sub_y = get_xy("subtype", 40, title_y+100)
            draw_banner(draw, subtype.upper() if sub_settings.get("all_caps") else subtype, sub_y, CARD_SIZE[0], sub_font, fill_fg=get_color("subtype", "white"), settings=sub_settings)
        # Placeholder for art
        art_y = title_y+100
        art_h = 600
        draw.rectangle([60, art_y, CARD_SIZE[0]-60, art_y+art_h], fill=(200,180,120,255), outline=(120,100,60,255), width=4)
        draw.text((CARD_SIZE[0]//2-80, art_y+art_h//2-20), "ART HERE", font=sub_font, fill=(120,100,60,255))
    else:
        # Back: Title, Subtype, Story, Stats
        y = 60
        title_text = title
        title_settings = get_style("title")
        if title_settings.get("all_caps"): title_text = title_text.upper()
        title_x, title_y = get_xy("title", (CARD_SIZE[0]-600)//2, y)
        draw_styled_text(draw, title_text, (title_x, title_y), title_font, get_color("title", "black"), title_settings, underline=title_settings.get("underline"), shadow=title_settings.get("shadow"), letter_spacing=title_settings.get("letter_spacing", 0), line_spacing=title_settings.get("line_spacing", 0))
        y = title_y + title_font.size + 20
        if subtype:
            sub_settings = get_style("subtype")
            sub_x, sub_y = get_xy("subtype", 40, y)
            y = draw_banner(draw, subtype.upper() if sub_settings.get("all_caps") else subtype, sub_y, CARD_SIZE[0], sub_font, fill_fg=get_color("subtype", "white"), settings=sub_settings)
        # Story/lore
        if back_text:
            # Split into story and stats if possible
            parts = back_text.split("\n\n", 1)
            story = parts[0]
            stats = parts[1] if len(parts) > 1 else ""
            body_settings = get_style("body")
            body_x, body_y = get_xy("body", 60, y)
            draw_styled_text(draw, story, (body_x, body_y), body_font, get_color("body", "black"), body_settings, underline=body_settings.get("underline"), shadow=body_settings.get("shadow"), letter_spacing=body_settings.get("letter_spacing", 0), line_spacing=body_settings.get("line_spacing", 0))
            # Estimate multiline height using textbbox for each line
            story_lines = story.split('\n')
            for line in story_lines:
                if line.strip():
                    bbox = draw.textbbox((0, 0), line, font=body_font)
                    y += bbox[3] - bbox[1]
            y += 30
            # Stats block
            if stats:
                stats_settings = get_style("stats")
                stats_x, stats_y = get_xy("stats", 60, y)
                draw_styled_text(draw, stats, (stats_x, stats_y), stats_font, get_color("stats", "black"), stats_settings, underline=stats_settings.get("underline"), shadow=stats_settings.get("shadow"), letter_spacing=stats_settings.get("letter_spacing", 0), line_spacing=stats_settings.get("line_spacing", 0))
    try:
        img.save(output_path)
        print(f"[DEBUG] overlay_card: Saved image to {output_path}")
    except Exception as e:
        print(f"[ERROR] overlay_card: Failed to save image to {output_path}: {e}")

# Dummy image gen (not used for template, but kept for compatibility)
def generate_image_from_prompt(prompt, output_path):
    img = Image.new("RGBA", CARD_SIZE, (235, 210, 150, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(TITLE_FONT_PATH, 40)
    except:
        font = ImageFont.load_default()
    draw.text((20, 20), prompt[:80], fill="gray", font=font)
    try:
        img.save(output_path)
        print(f"[DEBUG] generate_image_from_prompt: Saved image to {output_path}")
    except Exception as e:
        print(f"[ERROR] generate_image_from_prompt: Failed to save image to {output_path}: {e}")

def generate_borderless_art_image(prompt, output_path):
    """
    Generate a borderless, art-only image (no background, no frame, no 'ART HERE' text).
    The image will have a transparent background and the correct aspect ratio.
    """
    img = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 0))  # Fully transparent
    # Optionally, you could add AI art generation here using the prompt
    # For now, just save the transparent image as a placeholder
    try:
        img.save(output_path)
        print(f"[DEBUG] generate_borderless_art_image: Saved image to {output_path}")
    except Exception as e:
        print(f"[ERROR] generate_borderless_art_image: Failed to save image to {output_path}: {e}") 