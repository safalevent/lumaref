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

from __future__ import annotations

from importlib.resources import files as rsc_files
import logging
from typing import Optional

from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import Qt

from zeeref import constants, commands


logger = logging.getLogger(__name__)


class ZeeProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self, label, worker, maximum=0, parent=None):
        super().__init__(label, "Cancel", 0, maximum, parent=parent)
        logger.debug("Initialised progress bar")
        self.setMinimumDuration(0)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAutoReset(False)
        self.setAutoClose(False)
        worker.begin_processing.connect(self.on_begin_processing)
        worker.progress.connect(self.on_progress)
        worker.finished.connect(self.on_finished)
        worker.user_input_required.connect(self.on_finished)
        self.canceled.connect(worker.on_canceled)

    def on_progress(self, value):
        logger.debug(f"Progress dialog: {value}")
        self.setValue(value)

    def on_begin_processing(self, value):
        logger.debug(f"Beginn progress dialog: {value}")
        self.setMaximum(value)

    def on_finished(self, *args, **kwargs):
        logger.debug("Finished progress dialog")
        self.setValue(self.maximum())
        self.reset()
        self.hide()
        QtCore.QTimer.singleShot(100, self.deleteLater)


class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(f"{constants.APPNAME} Help")

        tabs = QtWidgets.QTabWidget()

        # Controls
        controls_txt = (
            rsc_files("zeeref.documentation").joinpath("controls.html").read_text()
        )
        controls_label = QtWidgets.QLabel(controls_txt)
        controls_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls_label)
        tabs.addTab(scroll, "&Controls")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(tabs)

        # Bottom row of buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.show()


class SceneToPixmapExporterDialog(QtWidgets.QDialog):
    MIN_SIZE = 10
    MAX_SIZE = 100000

    def __init__(self, parent, default_size):
        super().__init__(parent)
        self.default_size = default_size
        if (
            self.default_size.width() > self.MAX_SIZE
            or self.default_size.width() >= self.MAX_SIZE
        ):
            self.default_size.scale(
                self.MAX_SIZE, self.MAX_SIZE, Qt.AspectRatioMode.KeepAspectRatio
            )

        self.ignore_change = False
        self.setWindowTitle("Export Scene to Image")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        width_label = QtWidgets.QLabel("Width:")
        layout.addWidget(width_label, 0, 0)
        self.width_input = QtWidgets.QSpinBox()
        self.width_input.setRange(self.MIN_SIZE, self.MAX_SIZE)
        self.width_input.setValue(default_size.width())
        self.width_input.valueChanged.connect(self.on_width_changed)
        layout.addWidget(self.width_input, 0, 1)

        height_label = QtWidgets.QLabel("Height:")
        layout.addWidget(height_label, 1, 0)
        self.height_input = QtWidgets.QSpinBox()
        self.height_input.setMinimum(10)
        self.height_input.setRange(self.MIN_SIZE, self.MAX_SIZE)
        self.height_input.setValue(default_size.height())
        self.height_input.valueChanged.connect(self.on_height_changed)
        layout.addWidget(self.height_input, 1, 1)

        # Bottom row of buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, 3, 1)

    def on_width_changed(self, width):
        if not self.ignore_change:
            self.ignore_change = True
            new = self.default_size.scaled(
                width, self.MAX_SIZE, Qt.AspectRatioMode.KeepAspectRatio
            )
            self.height_input.setValue(new.height())
            self.ignore_change = False

    def on_height_changed(self, height):
        if not self.ignore_change:
            self.ignore_change = True
            new = self.default_size.scaled(
                self.MAX_SIZE, height, Qt.AspectRatioMode.KeepAspectRatio
            )
            self.width_input.setValue(new.width())
            self.ignore_change = False

    def value(self):
        return QtCore.QSize(self.width_input.value(), self.height_input.value())


class ChangeOpacityDialog(QtWidgets.QDialog):
    def __init__(self, parent, images, undo_stack):
        super().__init__(parent)
        self.undo_stack = undo_stack
        self.images = images
        self.command = commands.ChangeOpacity(images, opacity=1)

        value = int(images[0].opacity() * 100) if images else 100

        self.setWindowTitle("Change Opacity:")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.label = QtWidgets.QLabel("Opacity:")
        layout.addWidget(self.label)

        self.input = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.input.valueChanged.connect(self.on_value_changed)
        self.input.setRange(0, 100)
        self.input.setValue(value)
        layout.addWidget(self.input)

        # Bottom row of buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.show()

    def on_value_changed(self, value):
        self.label.setText(f"Opacity: {value}%")
        self.command.opacity = value / 100
        self.command.redo()

    def accept(self):
        if self.images:
            logger.debug(f"Setting opacity to {self.command.opacity}")
            self.command.ignore_first_redo = True
            self.undo_stack.push(self.command)
        return super().accept()

    def reject(self):
        self.command.undo()
        return super().reject()


class ZeeNotification(QtWidgets.QWidget):
    def __init__(self, parent, text):
        super().__init__(parent)
        if hasattr(parent, "findChildren"):
            for child in parent.findChildren(ZeeNotification):
                if child is not self:
                    child.hide()
                    child.deleteLater()
        self.label = QtWidgets.QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("ZeeNotification")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAutoFillBackground(True)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        color = constants.COLORS["Active:Window"]
        self.setStyleSheet(
            f"background-color: rgba({color[0]}, {color[1]}, {color[2]}, 0.9);"
            "padding: 0.7em;"
            "border-radius: 5px;"
        )
        self.show()
        # We only get own width after showing it;
        # updateGeometry doesn't work on hidden widgets
        x = (parent.width() - self.width()) / 2
        self.move(int(x), 10)

        QtCore.QTimer.singleShot(1000 * 3, self.deleteLater)


class SampleColorWidget(QtWidgets.QWidget):
    OFFSET = 10  # Offset from mouse pointer
    SIZE = 50
    NONE_COLOR = QtGui.QColor(0, 0, 0, 0)

    def __init__(self, parent, pos, color):
        super().__init__(parent)
        self.color = color
        self.set_pos(pos)
        self.show()

    def set_pos(self, pos):
        self.setGeometry(
            int(pos.x() + self.OFFSET), int(pos.y() + self.OFFSET), self.SIZE, self.SIZE
        )

    def paintEvent(self, event: Optional[QtGui.QPaintEvent]) -> None:
        color = self.color if self.color else self.NONE_COLOR
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, self.SIZE, self.SIZE)

    def update_sample(self, pos: QtCore.QPointF, color: QtGui.QColor | None) -> None:
        self.set_pos(pos)
        self.color = color
        self.repaint()


class ExportImagesFileExistsDialog(QtWidgets.QDialog):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.setWindowTitle("File exists")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        label = QtWidgets.QLabel(f"File already exists:\n{filename}")
        layout.addWidget(label)

        choices = (
            ("skip", "Skip this file"),
            ("skip_all", "Skip all existing files"),
            ("overwrite", "Overwrite this file"),
            ("overwrite_all", "Overwrite all existing files"),
        )

        self.radio_buttons = {}
        for value, label in choices:
            btn = QtWidgets.QRadioButton(label)
            self.radio_buttons[value] = btn
            layout.addWidget(btn)
        self.radio_buttons["skip"].setChecked(True)

        # Bottom row of buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def get_answer(self):
        for value, btn in self.radio_buttons.items():
            if btn.isChecked():
                return value


class BrushPreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.brush_size: float = 1.0
        self.brush_color: list[int] = [255, 255, 255, 255]
        self.setFixedSize(100, 80)

    def update_brush(self, size: float, color: list[int]) -> None:
        self.brush_size = size
        self.brush_color = color
        self.update()

    def paintEvent(self, event: Optional[QtGui.QPaintEvent]) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Draw actual size capped at a maximum of 70px to fit well in the overlay
        max_display_size = 70.0
        display_size = min(self.brush_size, max_display_size)
        display_size = max(display_size, 2.0)
        radius = display_size / 2.0

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        qcolor = QtGui.QColor(*self.brush_color)
        painter.setBrush(QtGui.QBrush(qcolor))
        # Draw a subtle outline for visual contrast
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 80), 1.0))
        painter.drawEllipse(QtCore.QPointF(cx, cy), radius, radius)


class StrokeSizeOverlay(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Layout setup
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Text label
        self.label = QtWidgets.QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            "color: #ffffff;"
            "font-size: 13px;"
            "font-weight: bold;"
            "font-family: 'Segoe UI', Arial, sans-serif;"
        )
        layout.addWidget(self.label)

        # Brush size/color preview widget
        self.preview = BrushPreviewWidget(self)
        layout.addWidget(self.preview)

        # Visibility timers and animations
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)

        self.animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(150)

        self.hide()

    def update_values(self, size: float, color: list[int]) -> None:
        self.label.setText(f"Stroke Size: {size:.1f} px")
        self.preview.update_brush(size, color)

    def show_overlay(self) -> None:
        self.timer.stop()
        self.animation.stop()
        self.show()
        self.raise_()

        parent = self.parentWidget()
        if parent:
            self.adjustSize()
            x = int((parent.width() - self.width()) / 2)
            y = 20
            self.move(x, y)

        self.animation.setStartValue(self.opacity_effect.opacity())
        self.animation.setEndValue(1.0)
        self.animation.start()

        self.timer.start(1000)

    def fade_out(self) -> None:
        self.animation.stop()
        self.animation.setStartValue(self.opacity_effect.opacity())
        self.animation.setEndValue(0.0)
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass
        self.animation.finished.connect(self.on_fade_out_finished)
        self.animation.start()

    def on_fade_out_finished(self) -> None:
        if self.opacity_effect.opacity() == 0.0:
            self.hide()

    def paintEvent(self, event: Optional[QtGui.QPaintEvent]) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Dark glassmorphic background card
        bg_color = QtGui.QColor(30, 30, 30, 220)
        border_color = QtGui.QColor(255, 255, 255, 30)

        painter.setBrush(QtGui.QBrush(bg_color))
        painter.setPen(QtGui.QPen(border_color, 1.0))

        rect = self.rect()
        draw_rect = QtCore.QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.drawRoundedRect(draw_rect, 8.0, 8.0)

