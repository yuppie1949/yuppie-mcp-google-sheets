"""Google Drive 操作 mixin — 文件列表、过滤排序、复制"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from .base import SCOPES, _GoogleProtocol

if TYPE_CHECKING:
    pass


class DriveMixin:
    """Google Drive 操作方法（混入 _GoogleBase 子类使用）"""

    def _get_drive_service(self: _GoogleProtocol):
        creds = Credentials.from_service_account_info(self._get_credentials_info(), scopes=SCOPES)
        return build("drive", "v3", credentials=creds)

    def list_files(
        self: _GoogleProtocol, folder_id: str, file_type: str | None = None
    ) -> dict[str, Any]:
        """列出文件夹中的文件"""
        try:
            service = self._get_drive_service()
            query = f"'{folder_id}' in parents and trashed=false"
            if file_type:
                query += f" and mimeType='{file_type}'"

            files = []
            page_token: str | None = None
            while True:
                response = (
                    service.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken=page_token,
                    )
                    .execute()
                )
                for f in response.get("files", []):
                    files.append({"id": f.get("id"), "name": f.get("name")})
                page_token = response.get("nextPageToken")
                if page_token is None:
                    break
            return {"success": True, "data": {"files": files}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def filter_and_sort_files(
        self: _GoogleProtocol,
        file_list: list[dict[str, Any]],
        prefix: str | None = None,
        suffix: str | None = None,
        datetime_format: str | None = None,
        reverse: bool = True,
    ) -> dict[str, Any]:
        """按文件名前缀、后缀过滤，并按时间戳排序"""
        try:
            filtered = []
            for f in file_list:
                name = f.get("name", "")
                if prefix and not name.startswith(prefix):
                    continue
                if suffix and not name.endswith(suffix):
                    continue
                if datetime_format:
                    try:
                        date_str = name
                        if prefix:
                            date_str = date_str[len(prefix) :]
                        if suffix:
                            date_str = date_str[: -len(suffix)]
                        f["datetime"] = datetime.strptime(date_str, datetime_format).isoformat()
                    except ValueError:
                        continue
                filtered.append(f)
            if datetime_format:
                filtered.sort(key=lambda x: x.get("datetime", ""), reverse=reverse)
            return {"success": True, "data": {"files": filtered}}
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def copy_file(
        self: _GoogleProtocol,
        file_id: str,
        target_folder_id: str,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """通过 Google Apps Script 复制文件到指定文件夹（解决服务账号存储配额限制）"""
        try:
            script_url = os.environ.get("GOOGLE_APPS_SCRIPT_URL", "")
            if not script_url:
                raise ValueError("GOOGLE_APPS_SCRIPT_URL 环境变量未设置")
            payload = {
                "project": "google_drive",
                "action": "copy_file",
                "sourceFileId": file_id,
                "destinationFolderId": target_folder_id,
                "newName": new_name or "",
            }
            resp = requests.post(script_url, json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if result.get("status") != 200:
                raise RuntimeError(
                    result.get("details") or result.get("message", "Apps Script 执行失败")
                )
            return {
                "success": True,
                "data": {
                    "id": result.get("newFileId"),
                    "name": result.get("newFileName"),
                    "url": result.get("url"),
                },
            }
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}

    def get_storage_quota(self: _GoogleProtocol) -> dict[str, Any]:
        """查询 Drive 存储用量"""
        try:
            about = (
                self._get_drive_service()
                .about()
                .get(fields="storageQuota(limit,usage,usageInDrive)")
                .execute()
            )
            quota = about.get("storageQuota", {})
            return {
                "success": True,
                "data": {
                    "limit": int(quota.get("limit", 0)),
                    "usage": int(quota.get("usage", 0)),
                    "usage_in_drive": int(quota.get("usageInDrive", 0)),
                },
            }
        except Exception as e:
            return {"success": False, "error": self._format_error(e)}
