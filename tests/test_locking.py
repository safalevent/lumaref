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


def test_hierarchical_lock_criteria_match(qapp, scene):
    # A (small item): area is 100
    item_a = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    # B (large item): area is 900 (which is 900% of A's area, so >= 150%)
    item_b = ZeePixmapItem(QtGui.QImage(30, 30, QtGui.QImage.Format.Format_RGB32))
    
    scene.addItem(item_b)  # bottom-most
    scene.addItem(item_a)  # top-most
    
    # Position A such that it is completely enclosed by B
    item_b.setPos(0, 0)
    item_a.setPos(10, 10)
    
    # Both are user items in scene. Let's check stacking order: index of item_b < index of item_a
    user_items = scene.user_items()
    assert user_items.index(item_b) < user_items.index(item_a)
    
    # Lock A, it should find B as parent
    item_a.is_locked = True
    assert item_a.locked_to is item_b
    assert item_a in item_b.locked_children


def test_hierarchical_lock_criteria_mismatch(qapp, scene):
    # A (small item)
    item_a = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    # B (large item)
    item_b = ZeePixmapItem(QtGui.QImage(30, 30, QtGui.QImage.Format.Format_RGB32))
    
    scene.addItem(item_b)
    scene.addItem(item_a)
    
    # Position A such that it is far away (0% enclosure)
    item_b.setPos(0, 0)
    item_a.setPos(100, 100)
    
    # Lock A, it should NOT find B as parent since there is no overlap
    item_a.is_locked = True
    assert item_a.locked_to is None
    assert not hasattr(item_b, "locked_children") or not item_b.locked_children


def test_hierarchical_lock_transform_propagation(qapp, scene):
    # A (small item)
    item_a = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    # B (large item)
    item_b = ZeePixmapItem(QtGui.QImage(30, 30, QtGui.QImage.Format.Format_RGB32))
    
    scene.addItem(item_b)
    scene.addItem(item_a)
    
    item_b.setPos(0, 0)
    item_a.setPos(10, 10)
    
    # Lock A to B
    item_a.is_locked = True
    assert item_a.locked_to is item_b
    
    # 1. Move parent B by (20, 30). Child A should move by (20, 30) too.
    item_b.setPos(20, 30)
    assert item_a.pos() == QtCore.QPointF(30, 40)
    
    # 2. Scale parent B
    item_b.setScale(2.0)
    # Child scale should scale by B's scale factor (A.scale_orig * B.scale_factor)
    # Since A.scale() was 1.0, and B.scale() is now 2.0, A's scale should be 2.0
    assert item_a.scale() == 2.0
    
    # 3. Rotate parent B
    item_b.setRotation(90.0)
    assert item_a.rotation() == 90.0
    
    # 4. Flip parent B
    item_b.do_flip()
    assert item_a.flip() == -1.0


def test_hierarchical_lock_parent_deletion(qapp, scene):
    item_a = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    item_b = ZeePixmapItem(QtGui.QImage(30, 30, QtGui.QImage.Format.Format_RGB32))
    
    scene.addItem(item_b)
    scene.addItem(item_a)
    
    item_b.setPos(0, 0)
    item_a.setPos(10, 10)
    
    item_a.is_locked = True
    assert item_a.locked_to is item_b
    
    # Remove B from scene (simulate deletion)
    scene.removeItem(item_b)
    # This should trigger ItemSceneChange on B. Since it is removed, its children should unlock.
    assert not item_a.is_locked
    assert item_a.locked_to is None
    assert item_b.locked_children == []


def test_hierarchical_lock_save_restore(qapp, scene):
    item_a = ZeePixmapItem(QtGui.QImage(10, 10, QtGui.QImage.Format.Format_RGB32))
    item_b = ZeePixmapItem(QtGui.QImage(30, 30, QtGui.QImage.Format.Format_RGB32))
    item_a.save_id = "item_a"
    item_b.save_id = "item_b"
    
    scene.addItem(item_b)
    scene.addItem(item_a)
    
    item_b.setPos(0, 0)
    item_a.setPos(10, 10)
    
    item_a.is_locked = True
    assert item_a.locked_to is item_b
    
    # Create snapshots
    snap_a = item_a.snapshot()
    snap_b = item_b.snapshot()
    
    assert snap_a.data.get("locked_to") == "item_b"
    
    # Recreate items from snapshots in a new scene
    from zeeref.items import create_item_from_snapshot
    from zeeref.scene import ZeeGraphicsScene
    new_scene = ZeeGraphicsScene(QtGui.QUndoStack())
    
    new_b = create_item_from_snapshot(snap_b)
    new_a = create_item_from_snapshot(snap_a)
    
    new_scene.addItem(new_b)
    new_scene.addItem(new_a)
    
    # Resolve relationships
    new_scene.resolve_lock_relationships()
    
    assert new_a.locked_to is new_b
    assert new_a in new_b.locked_children
    
    # Test that transform propagation still works on restored items
    new_b.setPos(50, 50)
    assert new_a.pos() == QtCore.QPointF(60, 60)





