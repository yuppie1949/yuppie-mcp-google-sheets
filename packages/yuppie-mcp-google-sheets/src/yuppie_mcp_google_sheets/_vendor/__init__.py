"""vendor 副本引导

优先使用用户环境真实安装的库包 yuppie-google-sheets（可与本壳包共存），
仅当未安装时把 vendor 目录挂到 sys.path，使副本以顶层名可导入
（pip._vendor 同款模式）。tools 层导入 yuppie_google_sheets 前需先调用
mount_if_needed()。
"""

from __future__ import annotations

import importlib.util
import os
import sys


def mount_if_needed() -> None:
    if importlib.util.find_spec("yuppie_google_sheets") is not None:
        return
    parent = os.path.dirname(os.path.join(os.path.dirname(__file__), "yuppie_google_sheets"))
    if parent not in sys.path:
        sys.path.insert(0, parent)
