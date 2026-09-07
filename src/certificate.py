"""
Generate a shareable "Proof of Real" verification certificate (PNG).

The certificate shows the on-chain verification details plus a QR code that
links straight to the transaction on the block explorer — scan it to verify.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Certificate canvas
W, H = 1000, 640
BG = (16, 18, 27)
PANEL = (24, 27, 40)
ACCENT = (34, 197, 94)      # green
TEXT = (230, 233, 240)
MUTED = (148, 158, 178)


def _load_font(size: int, bold: bool = False):
    """Best-effort font loader; falls back to PIL default if TTFs are missing."""
    from PIL import ImageFont
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_certificate(record: Dict,
                         explorer_url: str,
                         face_image_path: Optional[str] = None,
                         output_path: str = "output/certificate.png") -> Optional[str]:
    """
    Build a verification certificate PNG.

    Args:
        record: on-chain record dict (record_id, face_hash, timestamp, recorded_by, ...)
        explorer_url: block-explorer URL the QR code points to
        face_image_path: optional face image to embed as a thumbnail
        output_path: where to save the PNG

    Returns:
        The output path, or None on failure.
    """
    try:
        from PIL import Image, ImageDraw
        import qrcode
    except Exception as e:
        logger.error(f"Certificate deps missing (Pillow/qrcode): {e}")
        return None

    try:
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)

        f_title = _load_font(40, bold=True)
        f_badge = _load_font(22, bold=True)
        f_label = _load_font(18)
        f_value = _load_font(20, bold=True)
        f_small = _load_font(15)

        # Header
        d.text((40, 36), "PROOF OF REAL", font=f_title, fill=TEXT)
        d.text((42, 88), "Blockchain-verified face record", font=f_label, fill=MUTED)

        # Verified badge (top-right)
        badge = "VERIFIED ON-CHAIN"
        bw = d.textlength(badge, font=f_badge)
        d.rounded_rectangle((W - bw - 90, 40, W - 40, 84), radius=12, fill=ACCENT)
        d.text((W - bw - 70, 50), badge, font=f_badge, fill=(8, 20, 12))

        # Divider
        d.line((40, 120, W - 40, 120), fill=PANEL, width=2)

        # Face thumbnail
        thumb_x, thumb_y, thumb = 40, 150, 220
        if face_image_path and Path(face_image_path).exists():
            try:
                face = Image.open(face_image_path).convert("RGB").resize((thumb, thumb))
                img.paste(face, (thumb_x, thumb_y))
                d.rectangle((thumb_x, thumb_y, thumb_x + thumb, thumb_y + thumb),
                            outline=ACCENT, width=3)
            except Exception:
                d.rectangle((thumb_x, thumb_y, thumb_x + thumb, thumb_y + thumb),
                            fill=PANEL)
        else:
            d.rectangle((thumb_x, thumb_y, thumb_x + thumb, thumb_y + thumb), fill=PANEL)
            d.text((thumb_x + 70, thumb_y + 100), "no image", font=f_small, fill=MUTED)

        # Record fields
        fx = thumb_x + thumb + 40
        fields = [
            ("Face hash (SHA256)", _short(record.get("face_hash", ""), 40)),
            ("Record ID", _short(record.get("record_id", ""), 40)),
            ("Recorded by", record.get("recorded_by", "")),
            ("Timestamp", str(record.get("timestamp", ""))),
            ("Network", record.get("network", "Ethereum Sepolia")),
        ]
        y = 150
        for label, value in fields:
            d.text((fx, y), label, font=f_label, fill=MUTED)
            d.text((fx, y + 22), value, font=f_value, fill=TEXT)
            y += 62

        # QR code -> explorer
        if explorer_url:
            qr = qrcode.make(explorer_url).convert("RGB").resize((150, 150))
            qx, qy = W - 190, H - 210
            img.paste(qr, (qx, qy))
            d.text((qx - 6, qy + 155), "scan to verify on-chain", font=f_small, fill=MUTED)

        # Footer
        d.line((40, H - 60, W - 40, H - 60), fill=PANEL, width=2)
        d.text((40, H - 46), (explorer_url or "")[:70], font=f_small, fill=ACCENT)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        logger.info(f"Certificate saved to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to generate certificate: {str(e)}")
        return None


def _short(s: str, n: int) -> str:
    """Shorten a long hex string with an ellipsis in the middle."""
    if not s or len(s) <= n:
        return s
    keep = (n - 3) // 2
    return f"{s[:keep]}...{s[-keep:]}"
