"""Horizontal category tab bar — iTerm-style chips, scrollable on overflow."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTabBar

ALL_ID = "__all__"
FAV_ID = "__fav__"
RECENT_ID = "__recent__"

VIRTUAL_NAMES = {"全部工具", "我的收藏", "最近启动"}


class CategoryTabs(QTabBar):
    category_changed = pyqtSignal(str)

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("categoryTabs")
        self.t = theme
        self.setExpanding(False)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.TextElideMode.ElideNone)
        self.setDrawBase(False)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.currentChanged.connect(self._on_current_changed)
        self._suppress_emit = False

    def set_categories(self, categories: list[dict], counts: dict[str, int]) -> None:
        self._suppress_emit = True
        # Remove all existing tabs (QTabBar lacks clear())
        while self.count():
            self.removeTab(0)

        all_count = sum(counts.values()) - counts.get(FAV_ID, 0) - counts.get(RECENT_ID, 0)
        # We computed all_count as sum of category counts (each tool counted once via its category).

        entries = [
            ("全部工具", ALL_ID, all_count),
            ("我的收藏", FAV_ID, counts.get(FAV_ID, 0)),
            ("最近启动", RECENT_ID, counts.get(RECENT_ID, 0)),
        ]
        for cat in categories:
            cid = cat.get("id") or cat.get("name", "")
            name = cat.get("name", cid)
            if name in VIRTUAL_NAMES:
                continue
            entries.append((name, cid, counts.get(cid, 0)))

        for name, cid, count in entries:
            label = f"{name}  {count}" if count else name
            idx = self.addTab(label)
            self.setTabData(idx, cid)

        self.setCurrentIndex(0)
        self._suppress_emit = False
        self._on_current_changed(0)

    def _on_current_changed(self, idx: int) -> None:
        if self._suppress_emit or idx < 0:
            return
        cid = self.tabData(idx)
        if cid:
            self.category_changed.emit(cid)

    def select_offset(self, delta: int) -> None:
        n = self.count()
        if n == 0:
            return
        cur = self.currentIndex()
        nxt = (cur + delta) % n
        self.setCurrentIndex(nxt)

    def select_index(self, idx: int) -> None:
        if 0 <= idx < self.count():
            self.setCurrentIndex(idx)
