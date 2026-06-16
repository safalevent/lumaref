# This file is part of ZeeRef.
#
# ZeeRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ZeeRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ZeeRef.  If not, see <https://www.gnu.org/licenses/>.

"""Tile pyramid generation for image storage."""

from __future__ import annotations

from collections.abc import Iterator
from math import ceil

from PIL import Image
from io import BytesIO

TILE_SIZE = 512


def generate_tiles(
    pil_img: Image.Image,
) -> Iterator[tuple[Image.Image, int, int, int]]:
    """Yield (tile_pil, level, col, row) for each tile in the pyramid.

    Level 0 is full resolution. Each subsequent level halves the image.
    Pyramid downsampling uses PIL LANCZOS; cropping into tiles uses PIL crop().
    Stops after the first level where the entire image fits in one tile.
    """
    if getattr(pil_img, "format", None) == "GIF" and getattr(pil_img, "is_animated", False):
        raise ValueError("Cannot generate tiles for an animated GIF")
    current_pil = pil_img
    level = 0
    while True:
        w, h = current_pil.size
        for row in range(ceil(h / TILE_SIZE)):
            for col in range(ceil(w / TILE_SIZE)):
                box = (
                    col * TILE_SIZE,
                    row * TILE_SIZE,
                    min(w, (col + 1) * TILE_SIZE),
                    min(h, (row + 1) * TILE_SIZE),
                )
                tile = current_pil.crop(box)
                yield (tile, level, col, row)
        if w <= TILE_SIZE and h <= TILE_SIZE:
            break
        current_pil = current_pil.resize(
            (max(1, w >> 1), max(1, h >> 1)),
            resample=Image.Resampling.LANCZOS,
        )
        level += 1


def encode_tile(tile: Image.Image, fmt: str) -> bytes:
    """Encode a PIL Image tile to bytes."""
    buf = BytesIO()
    if fmt == "jpeg":
        if tile.mode == "RGBA":
            tile = tile.convert("RGB")
        tile.save(buf, format="JPEG", quality=98)
    else:
        tile.save(buf, format="PNG")
    return buf.getvalue()



def pick_format(pil_img: Image.Image) -> str:
    """Choose storage format based on source format and image properties.

    PNG sources stay PNG to avoid lossy re-encoding. JPEG and other
    formats use JPEG for large non-alpha images, PNG otherwise.
    Animated GIFs are stored as raw GIF bytes.
    """
    if pil_img.format == "GIF" and getattr(pil_img, "is_animated", False):
        return "gif"
    if pil_img.format == "PNG" or pil_img.mode == "RGBA":
        return "png"
    w, h = pil_img.size
    if w < 500 and h < 500:
        return "png"
    return "jpeg"
