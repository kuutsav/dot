import pytest

from kon.tools._read_image import IMAGE_EXTENSIONS, get_mime_type, is_image_file


@pytest.mark.parametrize(
    ("filename", "expected_mime"),
    [
        ("test.jpg", "image/jpeg"),
        ("test.jpeg", "image/jpeg"),
        ("test.png", "image/png"),
        ("test.gif", "image/gif"),
        ("test.webp", "image/webp"),
        ("test.JPG", "image/jpeg"),
        ("test.PNG", "image/png"),
        ("test.txt", None),
        ("test.pdf", None),
        ("test", None),
    ],
)
def test_get_mime_type(filename, expected_mime):
    assert get_mime_type(filename) == expected_mime


@pytest.mark.parametrize(
    ("filename", "expected_is_image"),
    [
        ("test.jpg", True),
        ("test.jpeg", True),
        ("test.png", True),
        ("test.gif", True),
        ("test.webp", True),
        ("test.JPG", True),
        ("test.PNG", True),
        ("test.txt", False),
        ("test.pdf", False),
        ("test", False),
    ],
)
def test_is_image_file(filename, expected_is_image):
    assert is_image_file(filename) == expected_is_image


def test_all_image_extensions():
    for ext in IMAGE_EXTENSIONS:
        assert is_image_file(f"test{ext}")
