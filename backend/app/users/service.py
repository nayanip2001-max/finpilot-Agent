"""
Loads synthetic user profiles + portfolios from backend/data/users/*.json.
This is intentionally file-based (not a DB table) for the MVP so judges can
open and read the synthetic data directly; swap for a DB-backed store later
without changing the API contract.
"""
'''from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger("finpilot.users")


class UserService:
    def __init__(self, users_dir: str | None = None):
        settings = get_settings()
        self.users_dir = Path(users_dir or settings.users_data_path)

    def list_users(self) -> List[Dict[str, Any]]:
        if not self.users_dir.exists():
            return []
        users = []
        for path in sorted(self.users_dir.glob("*.json")):
            try:
                users.append(json.loads(path.read_text()))
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to parse user file %s: %s", path, exc)
        return users

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        path = self.users_dir / f"{user_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to parse user file %s: %s", path, exc)
            return None


user_service = UserService()'''
import json
from pathlib import Path
from typing import Any


class UserService:
    def __init__(self):
        # service.py is:
        # backend/app/users/service.py
        # parents[2] = backend
        self.data_dir = Path(__file__).resolve().parents[2] / "data" / "users"

    def _load_users(self) -> list[dict[str, Any]]:
        users = []

        if not self.data_dir.exists():
            return users

        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Support either:
                # { "id": "user_001", ... }
                # OR
                # [ { "id": "user_001", ... }, ... ]
                if isinstance(data, dict):
                    if "users" in data and isinstance(data["users"], list):
                        users.extend(data["users"])
                    elif "id" in data:
                        users.append(data)

                elif isinstance(data, list):
                    users.extend(
                        item for item in data
                        if isinstance(item, dict)
                    )

            except (json.JSONDecodeError, OSError) as exc:
                print(f"Warning: could not load {file_path}: {exc}")

        return users

    def list_users(self) -> list[dict[str, Any]]:
        return self._load_users()

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        user_id = str(user_id).strip()

        for user in self._load_users():
            if str(user.get("id", "")).strip() == user_id:
                return user

        return None


user_service = UserService()