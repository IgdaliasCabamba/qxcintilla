from typing import Dict, List, Union

from qtpy import QtGui
from qtpy.QtCore import QPoint, QSize, Qt, Signal
from qtpy.QtWidgets import QLabel, QPlainTextEdit
from typing_extensions import Self
from PyQt6.Qsci import *

from ..internal import (
    FeaturesExceptions,
    PanelsExceptions,
)
from ..managers import (
    FeaturesManager,
    PanelsManager,
)


class QXcintilla(QsciScintilla):
    on_resized = Signal()
    on_painted = Signal(object)
    on_updated = Signal()
    on_key_pressed = Signal(object)
    on_key_released = Signal(object)
    on_mouse_moved = Signal(object)
    on_mouse_released = Signal(object)
    on_mouse_double_clicked = Signal(object)
    on_text_setted = Signal(str)
    on_mouse_wheel_activated = Signal(object)
    on_chelly_document_changed = Signal(object)
    post_on_key_pressed = Signal(object)

    @property
    def followers(self) -> List[Self]:
        try:
            return self.__followers_references  # not initialized
        except AttributeError:
            return []

    @property
    def followed(self) -> bool:
        return bool(self.followers)

    @property
    def shareables(self) -> dict:
        return {"panels": self.panels, "features": self.features}
    

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._panels = PanelsManager(self)
        self._features = FeaturesManager(self)
    
        self._last_mouse_pos = QPoint(0, 0)
        self.__followers_references = []
        self._shared_reference = None
        self.__build()

    def __build(self):
        self.setMouseTracking(True)

    def update_state(self):
        self.on_updated.emit()

    def update(self):
        self.update_state()
        return super().update()

    @property
    def panels(self) -> PanelsManager:
        return self._panels

    @panels.setter
    def panels(self, new_manager: PanelsManager) -> PanelsManager:
        if new_manager is PanelsManager:
            self._panels = new_manager(self)
        elif isinstance(new_manager, PanelsManager):
            self._panels = new_manager
        else:
            raise PanelsExceptions.PanelValueError(
                f"invalid type: {new_manager} expected: {PanelsManager}"
            )

    @property
    def features(self) -> FeaturesManager:
        return self._features

    @features.setter
    def features(self, new_manager: FeaturesManager) -> FeaturesManager:
        if new_manager is FeaturesManager:
            self._features = new_manager(self)
        elif isinstance(new_manager, FeaturesManager):
            self._features = new_manager
        else:
            raise FeaturesExceptions.FeatureValueError(
                f"invalid type: {new_manager} expected: {FeaturesManager}"
            )
    
    def showEvent(self, event):
        super().showEvent(event)
        self.panels.refresh()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        self.on_painted.emit(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.on_resized.emit()
    
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> Union[None, object]:
        self.on_key_pressed.emit(event)
        super().keyPressEvent(event)
        self.post_on_key_pressed.emit(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        self.on_key_released.emit(event)
        return super().keyReleaseEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        self.on_mouse_wheel_activated.emit(event)
        return super().wheelEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        self.on_mouse_moved.emit(event)
        self._last_mouse_pos = event.pos()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.on_mouse_released.emit(event)
        return super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        self.on_mouse_double_clicked.emit(event)
        return super().mouseDoubleClickEvent(event)

    def setText(self, text: str) -> None:
        self.on_text_setted.emit(text)
        return super().setText(text)

    def follow(self, other_editor: Self, follow_back: bool = False):
        other_editor.followers.append(self)
        self.chelly_document = other_editor.chelly_document

        if follow_back:
            self.followers.append(other_editor)

    def unfollow(self, other_editor: Self, unfollow_back: bool = False):
        if self.following(other_editor):
            other_editor.followers.remove(self)
            ...
        if unfollow_back:
            if other_editor.following(self):
                self.followers.remove(other_editor)

    def following(self, other_editor: Self) -> bool:
        return self in other_editor.followers

    @property
    def shared_reference(self) -> list:
        return self.__shared_reference

    @shared_reference.setter
    def shared_reference(self, other_editor: Self):
        self.__shared_reference = other_editor

        for key, from_manager in other_editor.shareables.items():
            if hasattr(self, key):
                try:
                    to_manager = getattr(self, key)
                    to_manager.shared_reference = from_manager
                except AttributeError as e:
                    print(e)

    @shared_reference.deleter
    def shared_reference(self):
        self.__shared_reference = None