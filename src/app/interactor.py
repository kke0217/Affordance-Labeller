"""
interactor.py — Custom VTK Interactor Style

왼쪽 클릭/드래그 = painting (칠하기) 또는 pose 배치
오른쪽 클릭/드래그 = erasing (지우기)
Ctrl+왼쪽 드래그 = orbit 회전 (full trackball)
"""

import numpy as np
import vtk


class PaintInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    AffordanceApp의 상태를 참조하여 painting/erasing/orbit을 분리하는 커스텀 스타일.
    app["paint_active"], app["pose_place_mode"] 상태에 따라 동작이 달라진다.
    """

    def __init__(self, app):
        self.app = app
        self.AddObserver("LeftButtonPressEvent", self.on_left_press)
        self.AddObserver("LeftButtonReleaseEvent", self.on_left_release)
        self.AddObserver("RightButtonPressEvent", self.on_right_press)
        self.AddObserver("RightButtonReleaseEvent", self.on_right_release)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self._left_press_pos = None
        self._right_press_pos = None
        self._dragging = False

    def _pick_position(self, pos):
        """화면 좌표 → 3D world position (CellPicker)"""
        iren = self.GetInteractor()
        renderer = iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)
        picker.Pick(pos[0], pos[1], 0, renderer)
        if picker.GetCellId() < 0:
            return None
        return np.array(picker.GetPickPosition())

    # --- Left Button (paint / pose / orbit) ---
    def on_left_press(self, obj, event):
        iren = self.GetInteractor()
        ctrl = iren.GetControlKey()
        if ctrl:
            iren.SetControlKey(0)
            self.OnLeftButtonDown()
            iren.SetControlKey(1)
            return
        if not self.app["paint_active"]:
            self.OnLeftButtonDown()
            return
        if self.app["pose_place_mode"]:
            hit = self._pick_position(iren.GetEventPosition())
            if hit is not None:
                self.app.place_pose_at(hit)
            return
        self._left_press_pos = iren.GetEventPosition()
        self._dragging = False

    def on_left_release(self, obj, event):
        iren = self.GetInteractor()
        ctrl = iren.GetControlKey()
        if ctrl:
            iren.SetControlKey(0)
            self.OnLeftButtonUp()
            iren.SetControlKey(1)
            return
        if not self.app["paint_active"]:
            self.OnLeftButtonUp()
            return
        if not self._dragging and self._left_press_pos:
            hit = self._pick_position(self._left_press_pos)
            if hit is not None:
                self.app.paint_at(hit)
        self._left_press_pos = None
        self._dragging = False

    # --- Right Button (erase) ---
    def on_right_press(self, obj, event):
        iren = self.GetInteractor()
        if not self.app["paint_active"]:
            self.OnRightButtonDown()
            return
        self._right_press_pos = iren.GetEventPosition()
        self._dragging = False

    def on_right_release(self, obj, event):
        iren = self.GetInteractor()
        if not self.app["paint_active"]:
            self.OnRightButtonUp()
            return
        if not self._dragging and self._right_press_pos:
            hit = self._pick_position(self._right_press_pos)
            if hit is not None:
                self.app.erase_at(hit)
        self._right_press_pos = None
        self._dragging = False

    # --- Mouse Move ---
    def on_mouse_move(self, obj, event):
        iren = self.GetInteractor()
        ctrl = iren.GetControlKey()
        if ctrl:
            iren.SetControlKey(0)
            self.OnMouseMove()
            iren.SetControlKey(1)
            return
        if self._left_press_pos is not None:
            cur = iren.GetEventPosition()
            if abs(cur[0] - self._left_press_pos[0]) > 3 or abs(cur[1] - self._left_press_pos[1]) > 3:
                self._dragging = True
                hit = self._pick_position(cur)
                if hit is not None:
                    self.app.paint_at(hit)
            return
        if self._right_press_pos is not None:
            cur = iren.GetEventPosition()
            if abs(cur[0] - self._right_press_pos[0]) > 3 or abs(cur[1] - self._right_press_pos[1]) > 3:
                self._dragging = True
                hit = self._pick_position(cur)
                if hit is not None:
                    self.app.erase_at(hit)
            return
        self.OnMouseMove()
