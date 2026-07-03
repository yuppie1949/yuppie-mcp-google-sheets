"""Google Sheets MCP Server 配置：从环境变量读取并校验"""

from __future__ import annotations

import base64
import json
import os

from dotenv import load_dotenv

load_dotenv()


class GoogleConfig:
    """运行配置：Google 服务账号凭据"""

    credentials_b64: str
    _credentials_info: dict | None = None

    def __init__(self, credentials_b64: str) -> None:
        self.credentials_b64 = credentials_b64.strip()

    @property
    def credentials_info(self) -> dict:
        """解析并缓存凭据 JSON"""
        if self._credentials_info is None:
            raw = base64.b64decode(self.credentials_b64).decode("utf-8")
            self._credentials_info = json.loads(raw)
        return self._credentials_info

    @classmethod
    def from_env(cls) -> GoogleConfig:
        """从环境变量构造配置，缺少必填项时抛 ValueError"""
        b64 = os.environ.get("GOOGLE_CREDENTIALS_B64", "").strip()
        if not b64:
            raise ValueError("缺少必填环境变量 GOOGLE_CREDENTIALS_B64")
        return cls(credentials_b64=b64)
