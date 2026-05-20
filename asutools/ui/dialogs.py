import uuid
from pathlib import Path

from PyQt6.QtCore import QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import store, theme
from ..env_scanner import scan_all

TOOL_TYPES = [
    ("python", "Python 脚本"),
    ("java", "Java jar"),
    ("shell", "Shell / 命令行"),
    ("gui", "GUI 应用 / 单文件"),
    ("url", "网页 URL"),
]


class _EnvDelegate(QStyledItemDelegate):
    """Multi-line env item: [type] name (default star) / path."""

    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.t = t
        self._c_active = QColor(t["bg_active"])
        self._c_hover = QColor(t["bg_hover"])
        self._c_text = QColor(t["text"])
        self._c_dim = QColor(t["text_dim"])
        self._c_mute = QColor(t["text_mute"])
        self._tag_font = QFont()
        self._tag_font.setPointSize(10)
        self._tag_font.setWeight(QFont.Weight.Medium)
        self._name_font = QFont()
        self._name_font.setPointSize(13)
        self._name_font.setWeight(QFont.Weight.Medium)
        self._path_font = QFont()
        self._path_font.setPointSize(11)

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), 58)

    def paint(self, painter: QPainter, option, index) -> None:
        env = index.data(Qt.ItemDataRole.UserRole) or {}
        is_default = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        rect: QRect = option.rect

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        body = rect.adjusted(4, 2, -4, -2)
        if selected or hovered:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(self._c_active if selected else self._c_hover)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(body, 6, 6)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        ttype = (env.get("type") or "").upper()
        if env.get("javafx"):
            ttype = ttype + "+FX"
        painter.setFont(self._tag_font)
        fm = painter.fontMetrics()
        tag_w = fm.horizontalAdvance(ttype) + 14
        tag_h = 18
        tag_rect = QRect(body.left() + 12, body.top() + (body.height() - tag_h) // 2, tag_w, tag_h)
        tag_bg = self._c_active if not selected else self._c_hover
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(tag_bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(tag_rect, 4, 4)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        fx_color = self._c_text if env.get("javafx") else self._c_dim
        painter.setPen(QPen(fx_color))
        painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, ttype)

        painter.setFont(self._name_font)
        painter.setPen(QPen(self._c_text))
        name = env.get("name", "")
        if is_default:
            name = "★ " + name
        text_x = tag_rect.right() + 12
        name_rect = QRect(text_x, body.top() + 8, body.right() - text_x - 12, 22)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)

        painter.setFont(self._path_font)
        painter.setPen(QPen(self._c_mute))
        path_rect = QRect(text_x, body.top() + 30, body.right() - text_x - 12, 20)
        path = env.get("path", "")
        elided = painter.fontMetrics().elidedText(path, Qt.TextElideMode.ElideMiddle, path_rect.width())
        painter.drawText(path_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)


def _form_label(text: str) -> QLabel:
    x = QLabel(text)
    x.setObjectName("formLabel")
    return x


class ToolDialog(QDialog):
    saved = pyqtSignal(dict)

    def __init__(self, t: dict, tool: dict | None, categories: list[dict], envs: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑工具" if tool else "新增工具")
        self.setMinimumWidth(560)
        self.setStyleSheet(theme.qss(t))
        self.t = t
        self.envs = envs
        self.tool = tool or {}

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.name_input = QLineEdit(self.tool.get("name", ""))
        form.addRow(_form_label("名称"), self.name_input)

        self.type_combo = QComboBox()
        for key, label in TOOL_TYPES:
            self.type_combo.addItem(label, key)
        cur_type = self.tool.get("type", "shell")
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == cur_type:
                self.type_combo.setCurrentIndex(i)
                break
        self.type_combo.currentIndexChanged.connect(self._refresh_env_combo)
        form.addRow(_form_label("类型"), self.type_combo)

        path_row = QWidget()
        pl = QHBoxLayout(path_row)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(6)
        self.path_input = QLineEdit(self.tool.get("path", ""))
        browse_btn = QPushButton("浏览…")
        browse_btn.clicked.connect(self._browse)
        pl.addWidget(self.path_input, 1)
        pl.addWidget(browse_btn)
        form.addRow(_form_label("路径 / URL"), path_row)

        self.args_input = QLineEdit(self.tool.get("args", ""))
        self.args_input.setPlaceholderText("启动参数（可选）")
        form.addRow(_form_label("参数"), self.args_input)

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        for c in categories:
            self.category_combo.addItem(c.get("name", ""), c.get("id", ""))
        cur_cat = self.tool.get("category", "")
        if cur_cat:
            idx = self.category_combo.findData(cur_cat)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setEditText(cur_cat)
        form.addRow(_form_label("分类"), self.category_combo)

        self.env_combo = QComboBox()
        form.addRow(_form_label("环境"), self.env_combo)
        self._refresh_env_combo()

        self.tags_input = QLineEdit(", ".join(self.tool.get("tags", []) or []))
        self.tags_input.setPlaceholderText("逗号分隔")
        form.addRow(_form_label("标签"), self.tags_input)

        self.desc_input = QLineEdit(self.tool.get("description", ""))
        form.addRow(_form_label("描述"), self.desc_input)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_btn = btns.button(QDialogButtonBox.StandardButton.Save)
        if save_btn:
            save_btn.setObjectName("primary")
            save_btn.setText("保存")
        cancel_btn = btns.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setText("取消")
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(18)
        layout.addLayout(form)
        layout.addStretch(1)
        layout.addWidget(btns)

    def _refresh_env_combo(self):
        cur_type = self.type_combo.currentData()
        self.env_combo.clear()
        self.env_combo.addItem("（跟随默认）", None)
        if cur_type in ("python", "java"):
            wanted = ("python", "venv", "conda") if cur_type == "python" else ("java",)
            envs_filtered = [e for e in self.envs if e.get("type") in wanted]
            # FX-enabled Java envs sort first (they're the rare/needed kind)
            envs_filtered.sort(key=lambda e: (not e.get("javafx"), e.get("name", "")))
            for e in envs_filtered:
                fx = "  [+FX]" if e.get("javafx") else ""
                label = f"{e.get('name', '')}{fx}  ·  {e.get('path', '')}"
                self.env_combo.addItem(label, e.get("id"))
            cur = self.tool.get("env_id")
            if cur:
                idx = self.env_combo.findData(cur)
                if idx >= 0:
                    self.env_combo.setCurrentIndex(idx)
            self.env_combo.setEnabled(True)
        else:
            self.env_combo.setEnabled(False)

    def _browse(self):
        cur_type = self.type_combo.currentData()
        if cur_type == "url":
            return
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", str(Path.home()))
        if path:
            self.path_input.setText(path)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "名称不能为空")
            return
        result = {
            "id": self.tool.get("id") or str(uuid.uuid4())[:8],
            "name": name,
            "type": self.type_combo.currentData(),
            "path": self.path_input.text().strip(),
            "args": self.args_input.text().strip(),
            "category": self.category_combo.currentData() or self.category_combo.currentText().strip(),
            "env_id": self.env_combo.currentData(),
            "tags": [s.strip() for s in self.tags_input.text().split(",") if s.strip()],
            "description": self.desc_input.text().strip(),
            "favorite": self.tool.get("favorite", False),
            "last_used": self.tool.get("last_used", 0),
        }
        self.saved.emit(result)
        self.accept()


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(740, 520)
        self.setStyleSheet(theme.qss(t))
        self.t = t

        tabs = QTabWidget()
        tabs.addTab(self._build_env_tab(), "环境")
        tabs.addTab(self._build_general_tab(), "通用")
        tabs.addTab(self._build_about_tab(), "关于")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(tabs)

    def _build_env_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hint = QLabel("自动扫描系统中的 Python / venv / conda / Java，每个工具可单独指定使用哪个。")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        top = QHBoxLayout()
        top.setSpacing(8)
        rescan_btn = QPushButton("重新扫描")
        rescan_btn.clicked.connect(self._rescan)
        add_btn = QPushButton("手动添加…")
        add_btn.clicked.connect(self._manual_add)
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self._remove_selected)
        set_default_btn = QPushButton("★ 设为默认")
        set_default_btn.setObjectName("primary")
        set_default_btn.clicked.connect(self._set_default)

        top.addWidget(rescan_btn)
        top.addWidget(add_btn)
        top.addWidget(remove_btn)
        top.addStretch(1)
        top.addWidget(set_default_btn)
        layout.addLayout(top)

        self.env_list = QListWidget()
        self.env_list.setObjectName("envList")
        self.env_list.setFrameShape(QListWidget.Shape.NoFrame)
        self.env_list.setMouseTracking(True)
        self.env_list.setItemDelegate(_EnvDelegate(self.t, self.env_list))
        self.env_list.itemDoubleClicked.connect(lambda _: self._set_default())
        layout.addWidget(self.env_list, 1)

        self.default_label = QLabel()
        self.default_label.setObjectName("hintLabel")
        layout.addWidget(self.default_label)

        self._refresh_env_list()
        return w

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(14, 14, 14, 14)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        settings = store.load_settings()
        cur = settings.get("theme", "dark")
        idx = self.theme_combo.findData(cur)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        form.addRow(_form_label("主题"), self.theme_combo)

        info = QLabel("主题切换需要重启应用生效。")
        info.setObjectName("hintLabel")
        form.addRow(_form_label(""), info)

        outer.addLayout(form)
        outer.addStretch(1)
        return w

    def _build_about_tab(self) -> QWidget:
        from .. import __version__
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)

        title = QLabel("asuTools")
        f = QFont()
        f.setPointSize(22)
        f.setWeight(QFont.Weight.Bold)
        title.setFont(f)
        layout.addWidget(title)

        ver = QLabel(f"v{__version__}    ·    PyQt6")
        ver.setObjectName("hintLabel")
        layout.addWidget(ver)

        layout.addSpacing(10)
        desc = QLabel(
            "极简的本地工具启动器。\n"
            "支持 Python / venv / conda / Java 多环境，每个工具可单独指定环境。\n\n"
            "MIT License"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch(1)
        return w

    def _on_theme_changed(self):
        settings = store.load_settings()
        settings["theme"] = self.theme_combo.currentData()
        store.save_settings(settings)
        self.settings_changed.emit()

    def _refresh_env_list(self):
        self.env_list.clear()
        data = store.load_environments()
        defaults = data.get("defaults", {})
        for env in data.get("environments", []):
            etype = env.get("type", "")
            is_def = (defaults.get("java") == env.get("id")) if etype == "java" else (defaults.get("python") == env.get("id"))
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, env)
            item.setData(Qt.ItemDataRole.UserRole + 1, bool(is_def))
            self.env_list.addItem(item)

        py_id = defaults.get("python", "")
        java_id = defaults.get("java", "")
        envs = data.get("environments", [])
        py_name = next((e.get("name", "") for e in envs if e.get("id") == py_id), "未设置")
        java_name = next((e.get("name", "") for e in envs if e.get("id") == java_id), "未设置")
        self.default_label.setText(f"默认 Python:  {py_name}        默认 Java:  {java_name}")

    def _rescan(self):
        data = store.load_environments()
        existing_user = [e for e in data.get("environments", []) if e.get("source") == "user"]
        new_envs = [e.to_dict() for e in scan_all()]
        seen_ids = {e["id"] for e in new_envs}
        merged = new_envs + [e for e in existing_user if e["id"] not in seen_ids]
        data["environments"] = merged
        store.save_environments(data)
        self._refresh_env_list()
        self.settings_changed.emit()

    def _manual_add(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 python / java 可执行文件", "/")
        if not path:
            return
        etype, ok = QInputDialog.getItem(
            self, "类型", "环境类型：", ["python", "venv", "java"], 0, False
        )
        if not ok:
            return
        name, ok = QInputDialog.getText(self, "命名", "环境显示名：")
        if not ok or not name:
            return
        data = store.load_environments()
        new_env = {
            "id": f"user-{uuid.uuid4().hex[:8]}",
            "name": name,
            "type": etype,
            "path": path,
            "version": "",
            "source": "user",
            "tags": ["user"],
        }
        data.setdefault("environments", []).append(new_env)
        store.save_environments(data)
        self._refresh_env_list()
        self.settings_changed.emit()

    def _remove_selected(self):
        item = self.env_list.currentItem()
        if not item:
            return
        env = item.data(Qt.ItemDataRole.UserRole)
        data = store.load_environments()
        data["environments"] = [e for e in data.get("environments", []) if e.get("id") != env.get("id")]
        defaults = data.setdefault("defaults", {})
        for k, v in list(defaults.items()):
            if v == env.get("id"):
                defaults[k] = ""
        store.save_environments(data)
        self._refresh_env_list()
        self.settings_changed.emit()

    def _set_default(self):
        item = self.env_list.currentItem()
        if not item:
            return
        env = item.data(Qt.ItemDataRole.UserRole)
        data = store.load_environments()
        defaults = data.setdefault("defaults", {})
        etype = env.get("type", "")
        if etype == "java":
            defaults["java"] = env.get("id", "")
        else:
            defaults["python"] = env.get("id", "")
        store.save_environments(data)
        self._refresh_env_list()
        self.settings_changed.emit()
