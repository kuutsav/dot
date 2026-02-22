import base64
import io
import os

IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

MAX_DIMENSION = 2000
MAX_BYTES = 4 * 1024 * 1024
JPEG_QUALITY_STEPS = [85, 70, 55, 40]


def get_mime_type(path: str) -> str | None:
    ext = os.path.splitext(path)[1].lower()
    return IMAGE_EXTENSIONS.get(ext)


def is_image_file(path: str) -> bool:
    return get_mime_type(path) is not None


def resize_image(data: bytes, mime_type: str) -> tuple[bytes, str, str | None]:
    """
    Resize image if needed to stay within limits.

    Returns (data, mime_type, resize_note).
    If Pillow is not available, returns original image unchanged.
    """
    try:
        from PIL import Image
    except ImportError:
        return data, mime_type, None

    if len(data) <= MAX_BYTES:
        img = Image.open(io.BytesIO(data))
        width, height = img.size
        if width <= MAX_DIMENSION and height <= MAX_DIMENSION:
            return data, mime_type, f"[{width}x{height}]"

    img = Image.open(io.BytesIO(data))
    original_width, original_height = img.size

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    width, height = original_width, original_height
    if width > MAX_DIMENSION:
        height = int(height * MAX_DIMENSION / width)
        width = MAX_DIMENSION
    if height > MAX_DIMENSION:
        width = int(width * MAX_DIMENSION / height)
        height = MAX_DIMENSION

    if (width, height) != (original_width, original_height):
        img = img.resize((width, height), Image.Resampling.LANCZOS)

    def encode_image(fmt: str, quality: int | None = None) -> tuple[bytes, str]:
        buf = io.BytesIO()
        if fmt == "JPEG" and quality:
            img.save(buf, format=fmt, quality=quality, optimize=True)
        elif fmt == "PNG":
            img.save(buf, format=fmt, optimize=True)
        else:
            img.save(buf, format=fmt)
        return buf.getvalue(), f"image/{fmt.lower()}"

    png_data, png_mime = encode_image("PNG")
    if len(png_data) <= MAX_BYTES:
        if (width, height) != (original_width, original_height):
            resize_note = f"[{width}x{height}, resized from {original_width}x{original_height}]"
        else:
            resize_note = f"[{width}x{height}]"
        return png_data, png_mime, resize_note

    jpeg_data, jpeg_mime = encode_image("JPEG")
    for quality in JPEG_QUALITY_STEPS:
        jpeg_data, jpeg_mime = encode_image("JPEG", quality)
        if len(jpeg_data) <= MAX_BYTES:
            resize_note = (
                f"[{width}x{height}, resized from "
                f"{original_width}x{original_height}, quality={quality}]"
            )
            return jpeg_data, jpeg_mime, resize_note

    resize_note = (
        f"[{width}x{height}, resized from "
        f"{original_width}x{original_height}, may exceed size limit]"
    )
    return jpeg_data, jpeg_mime, resize_note


def read_and_process_image(path: str) -> tuple[str, str, str | None]:
    mime_type = get_mime_type(path)
    if not mime_type:
        raise ValueError(
            f"Unsupported image format. Supported: {', '.join(IMAGE_EXTENSIONS.keys())}"
        )
    with open(path, "rb") as f:
        data = f.read()
    data, mime_type, resize_note = resize_image(data, mime_type)
    return base64.b64encode(data).decode("utf-8"), mime_type, resize_note
