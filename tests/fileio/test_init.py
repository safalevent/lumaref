import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6 import QtCore, QtGui

from zeeref import fileio
from zeeref.fileio.scratch import create_scratch_file
from zeeref.types.snapshot import PixmapItemSnapshot
from zeeref.items import ZeePixmapItem
from ..utils import queue2list


def test_save_zref_via_swp(scene, imgfilename3x3):
    from zeeref.fileio.scratch import create_scratch_file

    scene._scratch_file = create_scratch_file(None)
    item = ZeePixmapItem(QtGui.QImage(imgfilename3x3))
    scene.addItem(item)
    snapshots = scene.snapshot_for_save()
    swp_path = scene._scratch_file
    assert swp_path is not None
    with tempfile.TemporaryDirectory() as dirname:
        fname = Path(dirname) / "test.zref"
        fileio.save_zref(fname, snapshots, swp_path)
        assert fname.exists()


@patch("zeeref.fileio.sql.SQLiteIO.read")
def test_load_zref(read_mock):
    with tempfile.TemporaryDirectory() as dirname:
        fname = Path(dirname) / "test.zref"
        fname.touch()
        fileio.load_zref(fname, MagicMock())
        read_mock.assert_called_once()


def _assert_finished_result(worker, *, errors, created_count):
    """Check the emitted IOResult's filename/errors and created_ids length."""
    worker.finished.emit.assert_called_once()
    result = worker.finished.emit.call_args[0][0]
    assert result.filename is None
    assert result.errors == errors
    assert len(result.created_ids) == created_count


def test_load_images_loads(scene, imgfilename3x3):
    scene._scratch_file = create_scratch_file(None)
    worker = MagicMock(canceled=False)
    fileio.insert_image_files([imgfilename3x3], QtCore.QPointF(5, 6), scene, worker)
    worker.begin_processing.emit.assert_called_once_with(1)
    worker.progress.emit.assert_called_once_with(0)
    _assert_finished_result(worker, errors=[], created_count=1)
    itemdata = queue2list(scene.items_to_add)
    assert len(itemdata) == 1
    snap, selected = itemdata[0]
    assert isinstance(snap, PixmapItemSnapshot)
    assert selected is True
    assert snap.x == 5 - snap.width / 2
    assert snap.y == 6 - snap.height / 2


def test_load_images_canceled(scene, imgfilename3x3):
    scene._scratch_file = create_scratch_file(None)
    worker = MagicMock(canceled=True)
    fileio.insert_image_files(
        [imgfilename3x3, imgfilename3x3], QtCore.QPointF(5, 6), scene, worker
    )
    worker.begin_processing.emit.assert_called_once_with(2)
    worker.progress.emit.assert_called_once_with(0)
    _assert_finished_result(worker, errors=[], created_count=0)
    itemdata = queue2list(scene.items_to_add)
    assert len(itemdata) == 0


def test_load_images_error(scene, imgfilename3x3):
    scene._scratch_file = create_scratch_file(None)
    worker = MagicMock(canceled=False)
    fileio.insert_image_files(
        ["foo.jpg", imgfilename3x3], QtCore.QPointF(5, 6), scene, worker
    )
    worker.begin_processing.emit.assert_called_once_with(2)
    worker.progress.emit.assert_any_call(0)
    worker.progress.emit.assert_any_call(1)
    _assert_finished_result(worker, errors=["foo.jpg"], created_count=1)
    itemdata = queue2list(scene.items_to_add)
    assert len(itemdata) == 1
    snap, selected = itemdata[0]
    assert isinstance(snap, PixmapItemSnapshot)
    assert selected is True
    assert snap.x == 5 - snap.width / 2
    assert snap.y == 6 - snap.height / 2


def test_load_animated_gif_item(scene, tmp_path):
    from PIL import Image
    from zeeref.fileio.tilecache import set_tile_cache, TileCache
    from zeeref.items import ZeePixmapItem
    from zeeref.items import _GifLoader

    # 1. Create a mock TileCache and register it
    scene._scratch_file = create_scratch_file(None)
    cache = TileCache(scene._scratch_file)
    set_tile_cache(cache)

    # 2. Build a 2-frame animated GIF
    frames = [
        Image.new("RGB", (50, 50), (255, 0, 0)),
        Image.new("RGB", (50, 50), (0, 255, 0)),
    ]
    gif_file = tmp_path / "test_anim.gif"
    frames[0].save(
        gif_file,
        save_all=True,
        append_images=frames[1:],
        format="GIF",
        loop=0,
        duration=100,
    )

    # 3. Insert the GIF file using insert_image_files
    worker = MagicMock(canceled=False)
    fileio.insert_image_files([str(gif_file)], QtCore.QPointF(5, 6), scene, worker)

    # 4. Process the queued items
    items = scene.add_queued_items()
    assert len(items) == 1
    item = items[0]

    # 5. Check item properties
    assert isinstance(item, ZeePixmapItem)
    assert item._is_gif is True

    # 6. Wait for the async load to complete
    loop = QtCore.QEventLoop()
    _GifLoader.instance().gif_blob_ready.connect(lambda item_ref, raw: loop.quit())
    QtCore.QTimer.singleShot(2000, loop.quit)
    loop.exec()

    # Check if movie setup succeeded and has a movie device
    assert item._gif_bytes is not None
    assert len(item._gif_bytes) > 0
    assert item._movie is not None
    assert item._movie.isValid() is True

    # Clean up
    set_tile_cache(None)
