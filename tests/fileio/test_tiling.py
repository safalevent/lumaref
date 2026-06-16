import pytest
from PIL import Image
from io import BytesIO
from zeeref.fileio.tiling import generate_tiles, encode_tile, pick_format, TILE_SIZE

def test_pick_format():
    # RGBA always PNG
    img_rgba = Image.new("RGBA", (10, 10))
    assert pick_format(img_rgba) == "png"

    # Small RGB is PNG
    img_small_rgb = Image.new("RGB", (100, 100))
    assert pick_format(img_small_rgb) == "png"

    # Large RGB is JPEG
    img_large_rgb = Image.new("RGB", (600, 600))
    assert pick_format(img_large_rgb) == "jpeg"

    # Animated GIF is gif
    img_gif = Image.new("RGB", (10, 10))
    img_gif.format = "GIF"
    img_gif.is_animated = True
    assert pick_format(img_gif) == "gif"

def test_generate_tiles_small_image():
    # An image smaller than TILE_SIZE (512x512) should yield exactly one tile at level 0
    w, h = 100, 100
    img = Image.new("RGB", (w, h))
    tiles = list(generate_tiles(img))
    assert len(tiles) == 1
    
    tile_img, level, col, row = tiles[0]
    assert level == 0
    assert col == 0
    assert row == 0
    assert tile_img.size == (w, h)

def test_generate_tiles_large_image():
    # A 600x400 image should yield:
    # Level 0 (600x400):
    #   col 0, row 0 (512x400)
    #   col 1, row 0 (88x400)
    # Level 1 (300x200):
    #   col 0, row 0 (300x200) - fits in 1 tile, stops
    img = Image.new("RGB", (600, 400))
    tiles = list(generate_tiles(img))
    assert len(tiles) == 3

    # Level 0, tile 0 (left)
    assert tiles[0][1] == 0  # level
    assert tiles[0][2] == 0  # col
    assert tiles[0][3] == 0  # row
    assert tiles[0][0].size == (512, 400)

    # Level 0, tile 1 (right)
    assert tiles[1][1] == 0  # level
    assert tiles[1][2] == 1  # col
    assert tiles[1][3] == 0  # row
    assert tiles[1][0].size == (88, 400)

    # Level 1, tile 0 (downsampled)
    assert tiles[2][1] == 1  # level
    assert tiles[2][2] == 0  # col
    assert tiles[2][3] == 0  # row
    assert tiles[2][0].size == (300, 200)

def test_generate_tiles_raises_for_animated_gif():
    img = Image.new("RGB", (10, 10))
    img.format = "GIF"
    img.is_animated = True
    with pytest.raises(ValueError, match="Cannot generate tiles for an animated GIF"):
        list(generate_tiles(img))

def test_encode_tile_jpeg():
    # Test encoding RGBA to JPEG (should automatically convert to RGB)
    img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 255))
    jpeg_data = encode_tile(img, "jpeg")
    
    # Read back and verify format/content
    decoded = Image.open(BytesIO(jpeg_data))
    assert decoded.format == "JPEG"
    assert decoded.size == (10, 10)
    # Check pixel value (approximate due to lossy JPEG compression)
    rgb_pixel = decoded.getpixel((0, 0))
    assert abs(rgb_pixel[0] - 255) < 5
    assert rgb_pixel[1] < 5
    assert rgb_pixel[2] < 5

def test_encode_tile_png():
    img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 128))
    png_data = encode_tile(img, "png")
    
    decoded = Image.open(BytesIO(png_data))
    assert decoded.format == "PNG"
    assert decoded.size == (10, 10)
    assert decoded.mode == "RGBA"
    assert decoded.getpixel((0, 0)) == (255, 0, 0, 128)
