"""GoogleConfig 环境变量读取与校验测试"""

import pytest
from yuppie_google_sheets.config import GoogleConfig


def test_from_env_requires_credentials(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_B64", "")
    with pytest.raises(ValueError, match="GOOGLE_CREDENTIALS_B64"):
        GoogleConfig.from_env()


def test_from_env_strips_whitespace(monkeypatch):
    monkeypatch.setenv("GOOGLE_CREDENTIALS_B64", "  abc123  ")
    cfg = GoogleConfig.from_env()
    assert cfg.credentials_b64 == "abc123"


def test_credentials_info_parsing(monkeypatch):
    import base64
    import json
    info = {"type": "service_account", "project_id": "test"}
    b64 = base64.b64encode(json.dumps(info).encode()).decode()
    monkeypatch.setenv("GOOGLE_CREDENTIALS_B64", b64)
    cfg = GoogleConfig.from_env()
    assert cfg.credentials_info == info
