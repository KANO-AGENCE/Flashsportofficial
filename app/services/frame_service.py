"""Apply decorative frames and race time text to photos."""
import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def apply_frame_to_photo(
    photo_path: str,
    frame_path: str,
    output_path: str,
    race_time: str | None = None,
    text_x: float = 0.5,
    text_y: float = 0.9,
    text_size: int = 48,
    text_color: str = "#FFFFFF",
) -> bool:
    """Overlay a frame on a photo and optionally add race time text.

    Args:
        photo_path: Path to the original photo
        frame_path: Path to the frame image (PNG with transparency)
        output_path: Where to save the result
        race_time: Optional race time string to overlay
        text_x: Relative X position (0-1) for the time text
        text_y: Relative Y position (0-1) for the time text
        text_size: Font size for the time text
        text_color: Hex color for the time text
    """
    try:
        photo = Image.open(photo_path).convert("RGBA")
        frame = Image.open(frame_path).convert("RGBA")

        # Resize frame to match photo dimensions
        frame = frame.resize(photo.size, Image.LANCZOS)

        # Composite frame over photo
        result = Image.alpha_composite(photo, frame)

        # Add race time text if provided
        if race_time:
            draw = ImageDraw.Draw(result)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", text_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Calculate text position
            px = int(photo.width * text_x)
            py = int(photo.height * text_y)

            # Draw text with slight shadow for readability
            shadow_offset = max(1, text_size // 20)
            draw.text(
                (px + shadow_offset, py + shadow_offset),
                race_time,
                fill="#00000080",
                font=font,
                anchor="mm",
            )
            draw.text((px, py), race_time, fill=text_color, font=font, anchor="mm")

        # Save as JPEG
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        result.convert("RGB").save(output_path, "JPEG", quality=95)
        return True

    except Exception as e:
        logger.error(f"Frame overlay error: {e}")
        return False
