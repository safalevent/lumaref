from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from zeeref.items import ZeePixmapItem

def test_selection_cycling(view):
    view.window().activateWindow()
    view.setFocus()
    view.viewport().setFocus()
    
    view.scene.clear()
    
    img = QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32)
    img.fill(QtGui.QColor("red"))
    
    item1 = ZeePixmapItem(img)
    item2 = ZeePixmapItem(img)
    item3 = ZeePixmapItem(img)
    
    item1.setPos(0, 0)
    item2.setPos(0, 0)
    item3.setPos(0, 0)
    
    view.scene.addItem(item1)
    view.scene.addItem(item2)
    view.scene.addItem(item3)

    item1.setZValue(3.0)
    item2.setZValue(2.0)
    item3.setZValue(1.0)
    
    QtWidgets.QApplication.processEvents()
    
    scene_pos = QtCore.QPointF(50, 50)
    viewport_pos_f = QtCore.QPointF(view.mapFromScene(scene_pos))
    
    from PyQt6.QtTest import QTest
    def simulate_left_click():
        QTest.mouseClick(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            viewport_pos_f.toPoint()
        )
        QtWidgets.QApplication.processEvents()

    assert not item1.isSelected()
    assert not item2.isSelected()
    assert not item3.isSelected()
    
    simulate_left_click()
    assert item1.isSelected()
    assert not item2.isSelected()
    assert not item3.isSelected()
    
    simulate_left_click()
    assert not item1.isSelected()
    assert item2.isSelected()
    assert not item3.isSelected()
    
    simulate_left_click()
    assert not item1.isSelected()
    assert not item2.isSelected()
    assert item3.isSelected()
    
    simulate_left_click()
    assert item1.isSelected()
    assert not item2.isSelected()
    assert not item3.isSelected()


def test_double_click_zoom_cycling(view):
    view.window().activateWindow()
    view.setFocus()
    view.viewport().setFocus()
    
    view.scene.clear()
    
    img = QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32)
    img.fill(QtGui.QColor("red"))
    
    item1 = ZeePixmapItem(img)
    item2 = ZeePixmapItem(img)
    
    item1.setPos(0, 0)
    item2.setPos(0, 0)
    
    view.scene.addItem(item1)
    view.scene.addItem(item2)

    item1.setZValue(2.0)
    item2.setZValue(1.0)
    
    QtWidgets.QApplication.processEvents()
    
    scene_pos = QtCore.QPointF(50, 50)
    viewport_pos_f = QtCore.QPointF(view.mapFromScene(scene_pos))
    
    from PyQt6.QtTest import QTest
    def simulate_double_click():
        QTest.mouseDClick(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            viewport_pos_f.toPoint()
        )
        QtWidgets.QApplication.processEvents()

    assert not item1.isSelected()
    assert not item2.isSelected()
    assert view.previous_transform is None
    
    simulate_double_click()
    assert item1.isSelected()
    assert not item2.isSelected()
    assert view.previous_transform is not None
    assert view.previous_transform["toggle_item"] == item1

    simulate_double_click()
    assert view.previous_transform is None
    assert item1.isSelected()
    assert not item2.isSelected()


def test_double_click_selects_currently_selected(view):
    view.window().activateWindow()
    view.setFocus()
    view.viewport().setFocus()
    
    view.scene.clear()
    
    img = QtGui.QImage(100, 100, QtGui.QImage.Format.Format_RGB32)
    img.fill(QtGui.QColor("red"))
    
    item1 = ZeePixmapItem(img)
    item2 = ZeePixmapItem(img)
    
    item1.setPos(0, 0)
    item2.setPos(0, 0)
    
    view.scene.addItem(item1)
    view.scene.addItem(item2)

    item1.setZValue(2.0)
    item2.setZValue(1.0)
    
    item2.setSelected(True)
    
    QtWidgets.QApplication.processEvents()
    
    scene_pos = QtCore.QPointF(50, 50)
    viewport_pos_f = QtCore.QPointF(view.mapFromScene(scene_pos))
    
    from PyQt6.QtTest import QTest
    def simulate_double_click():
        QTest.mouseDClick(
            view.viewport(),
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            viewport_pos_f.toPoint()
        )
        QtWidgets.QApplication.processEvents()

    assert not item1.isSelected()
    assert item2.isSelected()
    
    simulate_double_click()
    
    assert not item1.isSelected()
    assert item2.isSelected()
    assert view.previous_transform is not None
    assert view.previous_transform["toggle_item"] == item2



