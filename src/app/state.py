"""
state.py — 애플리케이션 상태 관리

전역 변수 대신 AppState 클래스로 상태를 관리한다.
패널 간 통신은 refresh 콜백 레지스트리를 통해 처리한다.
"""

from typing import Callable, Optional

import viser

from viewer import MeshViewer
from io_handler import create_empty_label


class AppState:
    """Affordance Labeller 전역 상태"""

    def __init__(
        self,
        server: viser.ViserServer,
        object_id: str = "ycb_025_mug",
        annotator: str = "unknown",
    ):
        self.server = server
        self.viewer = MeshViewer(server)
        self.label: dict = create_empty_label(object_id, "mesh", annotator)
        self.mesh_path: str = ""

        # GUI 핸들
        self.gui_status = None

        # 패널 간 통신용 콜백 레지스트리
        self._refresh_callbacks: dict[str, list[Callable]] = {}

    def set_status(self, message: str):
        """UI 하단 상태 메시지 갱신"""
        if self.gui_status:
            self.gui_status.content = message

    def register_refresh(self, name: str, callback: Callable):
        """refresh 콜백 등록 (패널 간 통신)"""
        self._refresh_callbacks.setdefault(name, []).append(callback)

    def refresh(self, name: str):
        """등록된 콜백 실행"""
        for cb in self._refresh_callbacks.get(name, []):
            cb()
