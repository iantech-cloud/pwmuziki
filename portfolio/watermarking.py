from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def branded_copy(image_field):
    image_field.open('rb')
    with Image.open(image_field) as source:
        image = source.convert('RGBA')
        width, height = image.size
        font_size = max(18, width // 34)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        except OSError:
            font = ImageFont.load_default()

        draw = ImageDraw.Draw(image, 'RGBA')
        label = 'P  pwmuziki'
        left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
        padding = max(10, width // 90)
        box_width = right - left + padding * 2
        box_height = bottom - top + padding * 2
        x = max(padding, width - box_width - padding)
        y = max(padding, height - box_height - padding)
        draw.rounded_rectangle((x, y, x + box_width, y + box_height), radius=padding, fill=(39, 36, 31, 185))
        draw.text((x + padding, y + padding - top), label, font=font, fill=(255, 253, 249, 235))

        output = BytesIO()
        image.convert('RGB').save(output, format='JPEG', quality=88, optimize=True)
        return output.getvalue()