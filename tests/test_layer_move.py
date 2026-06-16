import pytest
from PyQt6 import QtCore, QtGui
from zeeref.items import ZeePixmapItem, ZeePathItem

def test_layer_move_images(view):
    scene = view.scene
    # Create 3 overlapping images
    img1 = ZeePixmapItem(QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    img2 = ZeePixmapItem(QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    img3 = ZeePixmapItem(QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))

    # Position them so they overlap
    img1.setPos(0, 0)
    img2.setPos(10, 10)
    img3.setPos(20, 20)

    # Set initial z-values
    img1.setZValue(1.0)
    img2.setZValue(2.0)
    img3.setZValue(3.0)

    scene.addItem(img1)
    scene.addItem(img2)
    scene.addItem(img3)

    # Test "up" (Bring Forward) of img1
    scene.clearSelection()
    img1.setSelected(True)
    view.on_action_bring_forward()
    # img1 should be put one z-step above the next colliding item above it (img2)
    # img2 is at 2.0, so img1 should be at 2.0 + Z_STEP (2.001)
    assert img1.zValue() == pytest.approx(2.001)

    # Test Undo
    view.on_action_undo()
    assert img1.zValue() == 1.0

    # Test Redo
    view.on_action_redo()
    assert img1.zValue() == pytest.approx(2.001)

    # Test "top" (Bring to Front) of img1
    view.on_action_bring_to_front()
    # img1 should be above all other images (img3 is at 3.0), so 3.0 + Z_STEP
    assert img1.zValue() == pytest.approx(3.001)

    # Test "down" (Send Backward) of img1
    view.on_action_send_backward()
    # img1 is at 3.001. The first colliding item below it is img3 (at 3.0).
    # So it should become 3.0 - Z_STEP
    assert img1.zValue() == pytest.approx(2.999)

    # Test "bottom" (Send to Back) of img1
    view.on_action_send_to_back()
    # img2 is at 2.0. img3 is at 3.0. Minimum of other images is 2.0.
    # So img1 should become 2.0 - Z_STEP
    assert img1.zValue() == pytest.approx(1.999)


def test_layer_move_partition_boundaries(view):
    scene = view.scene
    # Create an image and a drawing
    img = ZeePixmapItem(QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    img.setPos(0, 0)
    img.setZValue(5.0)

    # Create a path with strokes that overlap
    path = ZeePathItem(strokes=[
        {
            "base_size": 10,
            "points": [{"x": 0, "y": 0, "pressure": 1.0}, {"x": 50, "y": 50, "pressure": 1.0}]
        }
    ])
    path.setPos(0, 0)
    path.setZValue(1e9 + 10.0)

    scene.addItem(img)
    scene.addItem(path)

    # Try to raise the image to top. There are no other images in the scene,
    # but we can try to raise it extremely high manually first and test boundary.
    # Actually, let's add another image and put it at a high Z, say 2e9 (though not allowed ideally).
    # If the max image Z is artificially made high, let's see if boundary limits it.
    img2 = ZeePixmapItem(QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32))
    img2.setPos(0, 0)
    img2.setZValue(1e9 + 50.0) # set artificially high
    scene.addItem(img2)

    scene.clearSelection()
    img.setSelected(True)
    view.on_action_bring_to_front()
    # It shouldn't cross 1e9. It should be capped at 1e9 - Z_STEP
    assert img.zValue() == pytest.approx(1e9 - scene.Z_STEP)

    # Try to lower the path to bottom. We'll add another path at a very low Z.
    path2 = ZeePathItem(strokes=[
        {
            "base_size": 10,
            "points": [{"x": 0, "y": 0, "pressure": 1.0}, {"x": 50, "y": 50, "pressure": 1.0}]
        }
    ])
    path2.setPos(0, 0)
    path2.setZValue(1.0) # sets lower than 1e9, but setZValue adds 1e9, so it becomes 1e9 + 1.0 (or similar)
    scene.addItem(path2)

    scene.clearSelection()
    path.setSelected(True)
    view.on_action_send_to_back()
    # It shouldn't go below 1e9
    assert path.zValue() >= 1e9

    # Now make path2 have zValue exactly 1e9
    path2.setZValue(1e9)
    # Since path2 is at 1e9, path's send_to_back should try to set it to 1e9 - Z_STEP,
    # but the boundary enforcement should cap it at 1e9.
    view.on_action_send_to_back()
    assert path.zValue() == 1e9
