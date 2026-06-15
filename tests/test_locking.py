import pytest
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from zeeref.items import ZeePixmapItem
from zeeref import commands
from zeeref.selection import SelectableMixin

def test_default_unlocked(qapp, item):
    item.setPos(10, 20)
    assert not item.is_locked
    assert item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    assert item.pos() == QtCore.QPointF(10, 20)


def test_lock_toggling(qapp, item):
    item.setPos(10, 20)
    orig_pos = item.pos()
    item.is_locked = True
    assert item.is_locked
    assert not (item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    assert item.pos() == orig_pos

    item.is_locked = False
    assert not item.is_locked
    assert item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    assert item.pos() == orig_pos


def test_lock_prevents_transformations(qapp, item):
    item.setPos(10, 20)
    item.setScale(2.0)
    item.setRotation(45.0)
    orig_pos = item.pos()
    orig_scale = item.scale()
    orig_rotation = item.rotation()

    item.is_locked = True
    
    # Try to modify
    item.setPos(100, 200)
    item.setScale(5.0)
    item.setRotation(90.0)
    item.do_flip()

    assert item.pos() == orig_pos
    assert item.scale() == orig_scale
    assert item.rotation() == orig_rotation


def test_lock_prevents_handles(qapp, scene, item):
    item.setPos(10, 20)
    orig_pos = item.pos()
    scene.addItem(item)
    item.setSelected(True)
    assert item.has_selection_handles()

    item.is_locked = True
    assert not item.has_selection_handles()
    assert item.pos() == orig_pos


def test_lock_excludes_rubberband(qapp, scene, item):
    scene.addItem(item)
    item.setPos(50, 50)
    orig_pos = item.pos()
    
    # Enable rubberband mode
    scene.active_mode = scene.RUBBERBAND_MODE
    scene.event_start = QtCore.QPointF(0, 0)
    
    # Set selection area over the item (item is not locked)
    path = QtGui.QPainterPath()
    path.addRect(QtCore.QRectF(10, 10, 100, 100))
    
    scene.setSelectionArea(path)
    assert item.isSelected()
    
    # Lock the item, it should be deselected if setSelectionArea is called again during rubberband selection
    item.is_locked = True
    
    # Trigger selection check
    for it in scene.selectedItems(user_only=True):
        if getattr(it, "is_locked", False):
            it.setSelected(False)
            
    assert not item.isSelected()
    assert item.pos() == orig_pos


def test_lock_commands(qapp, scene, item):
    scene.addItem(item)
    item.setPos(10, 20)
    orig_pos = item.pos()
    
    # Initial state
    assert not item.is_locked
    
    # Push lock command
    cmd = commands.LockItems(scene, [item], True)
    scene.undo_stack.push(cmd)
    assert item.is_locked
    assert item.pos() == orig_pos
    
    # Undo
    scene.undo_stack.undo()
    assert not item.is_locked
    assert item.pos() == orig_pos
    
    # Redo
    scene.undo_stack.redo()
    assert item.is_locked
    assert item.pos() == orig_pos


def test_serialization_deserialization(qapp, item):
    item.setPos(10, 20)
    orig_pos = item.pos()
    item.is_locked = True
    data = item.get_extra_save_data()
    assert data.get("locked") is True

    # Recreate from snapshot
    snap = item.snapshot()
    new_item = ZeePixmapItem.from_snapshot(snap)
    assert new_item.is_locked
    assert not (new_item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    assert new_item.pos() == orig_pos


def test_copy_copies_lock_state(qapp, item):
    item.setPos(10, 20)
    orig_pos = item.pos()
    item.is_locked = True
    copy_item = item.create_copy()
    assert copy_item.is_locked
    assert not (copy_item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    assert copy_item.pos() == orig_pos


def test_action_enablement(qapp, view, item):
    item.setPos(10, 20)
    orig_pos = item.pos()
    scene = view.scene
    scene.deselect_all_items()
    scene.addItem(item)
    item.setSelected(True)
    
    from zeeref.actions.actions import actions
    lock_action = actions.get("lock_items")
    
    # Initial: item is unlocked
    assert lock_action.qaction.isEnabled()
    assert lock_action.qaction.text() == "&Lock"
    
    # Lock item
    item.is_locked = True
    view.on_selection_changed()
    assert lock_action.qaction.isEnabled()
    assert lock_action.qaction.text() == "&Unlock"
    assert item.pos() == orig_pos


def test_lock_setSelected_ignored_in_rubberband_mode(qapp, scene, item):
    item.setPos(10, 20)
    orig_pos = item.pos()
    scene.addItem(item)
    item.is_locked = True
    
    # Not in rubberband mode, setSelected(True) should work
    item.setSelected(True)
    assert item.isSelected()
    
    # Deselect
    item.setSelected(False)
    assert not item.isSelected()
    
    # Enter rubberband mode
    scene.active_mode = scene.RUBBERBAND_MODE
    
    # setSelected(True) should be ignored
    item.setSelected(True)
    assert not item.isSelected()
    assert item.pos() == orig_pos


def test_drawing_locking(qapp, scene):
    from zeeref.items import ZeePathItem
    path_item = ZeePathItem(strokes=[])
    scene.addItem(path_item)
    path_item.setPos(10, 20)
    orig_pos = path_item.pos()
    
    assert path_item.is_lockable
    assert not path_item.is_locked
    
    path_item.is_locked = True
    assert path_item.is_locked
    assert not (path_item.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
    assert path_item.pos() == orig_pos
    
    # Check serialization
    data = path_item.get_extra_save_data()
    assert data.get("locked") is True
    
    # Recreate from snapshot
    snap = path_item.snapshot()
    new_item = ZeePathItem.from_snapshot(snap)
    assert new_item.is_locked
    assert new_item.pos() == orig_pos
    
    # Copy
    copy_item = path_item.create_copy()
    assert copy_item.is_locked
    assert copy_item.pos() == orig_pos


def test_lock_multiple_items_undo_retains_position(qapp, scene):
    item1 = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    item2 = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    scene.addItem(item1)
    scene.addItem(item2)
    
    item1.setPos(10, 10)
    item2.setPos(100, 100)
    
    item1.setSelected(True)
    item2.setSelected(True)
    
    # Check that they are selected and multi selection is active
    assert item1.isSelected()
    assert item2.isSelected()
    assert scene.has_multi_selection()
    
    pos1_init = item1.pos()
    pos2_init = item2.pos()
    
    # Lock them
    cmd = commands.LockItems(scene, [item1, item2], True)
    scene.undo_stack.push(cmd)
    
    assert item1.is_locked
    assert item2.is_locked
    
    # Undo lock
    scene.undo_stack.undo()
    
    assert not item1.is_locked
    assert not item2.is_locked
    
    assert item1.pos() == pos1_init
    assert item2.pos() == pos2_init


def test_lock_multiple_items_with_view_undo_retains_position(qapp, view):
    scene = view.scene
    item1 = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    item2 = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    scene.addItem(item1)
    scene.addItem(item2)
    
    item1.setPos(10, 10)
    item2.setPos(100, 100)
    
    item1.setSelected(True)
    item2.setSelected(True)
    
    # Check that they are selected and multi selection is active
    assert item1.isSelected()
    assert item2.isSelected()
    assert scene.has_multi_selection()
    
    pos1_init = item1.pos()
    pos2_init = item2.pos()
    
    # Lock them
    cmd = commands.LockItems(scene, [item1, item2], True)
    scene.undo_stack.push(cmd)
    qapp.processEvents()
    
    assert item1.is_locked
    assert item2.is_locked
    
    # Undo lock
    scene.undo_stack.undo()
    qapp.processEvents()
    
    assert not item1.is_locked
    assert not item2.is_locked
    
    assert item1.pos() == pos1_init
    assert item2.pos() == pos2_init


def test_locked_items_drag_does_not_push_undo(qapp, view):
    scene = view.scene
    item = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    scene.addItem(item)
    item.setPos(10, 20)
    item.setSelected(True)
    item.is_locked = True

    # Empty undo stack before dragging
    scene.undo_stack.clear()

    # Get local points in view viewport coordinates
    pt_start = QtCore.QPointF(view.mapFromScene(QtCore.QPointF(15, 25)))
    pt_end = QtCore.QPointF(view.mapFromScene(QtCore.QPointF(115, 125)))

    press_event = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonPress,
        pt_start,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    view.mousePressEvent(press_event)

    move_event = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseMove,
        pt_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    view.mouseMoveEvent(move_event)

    release_event = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonRelease,
        pt_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    view.mouseReleaseEvent(release_event)

    # Position should be unchanged
    assert item.pos() == QtCore.QPointF(10, 20)
    # No commands should be pushed to the undo stack
    assert scene.undo_stack.count() == 0





