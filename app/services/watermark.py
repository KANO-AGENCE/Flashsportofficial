"""Generate watermarked thumbnails for web display."""
import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

THUMB_MAX_SIZE = 800
WATERMARK_TEXT = "FLASHSPORT"
WATERMARK_OPACITY = 0.35


def create_watermarked_thumbnail(source_path: str, dest_path: str) -> bool:
    """Create a watermarked, resized thumbnail from a source image."""
    try:
        img = cv2.imread(source_path)
        if img is None:
            return False

        h, w = img.shape[:2]

        # Resize to max dimension
        scale = min(THUMB_MAX_SIZE / w, THUMB_MAX_SIZE / h)
        if scale < 1:
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w = new_h, new_w

        # Create watermark overlay
        overlay = img.copy()

        # Draw diagonal watermark text across the image
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.8, w / 500)
        thickness = max(2, int(w / 250))

        # Multiple diagonal lines of text
        for i in range(-2, 5):
            x_offset = int(i * w * 0.35)
            for j in range(0, h + 200, int(h * 0.25)):
                center_x = x_offset + int(j * 0.5)
                center_y = j

                # Get text size for centering
                (tw, th), _ = cv2.getTextSize(WATERMARK_TEXT, font, font_scale, thickness)

                # Rotation matrix for diagonal text
                M = cv2.getRotationMatrix2D((center_x, center_y), -30, 1)

                # Draw on overlay with white text
                cv2.putText(overlay, WATERMARK_TEXT, (center_x - tw // 2, center_y + th // 2),
                            font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        # Blend overlay with original
        result = cv2.addWeighted(overlay, WATERMARK_OPACITY, img, 1 - WATERMARK_OPACITY, 0)

        # Add subtle diagonal lines for extra protection
        line_overlay = result.copy()
        for i in range(-h, w + h, 40):
            cv2.line(line_overlay, (i, 0), (i + h, h), (200, 200, 200), 1, cv2.LINE_AA)
        result = cv2.addWeighted(line_overlay, 0.15, result, 0.85, 0)

        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(dest_path, result, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return True

    except Exception as e:
        logger.error(f"Watermark error for {source_path}: {e}")
        return False
