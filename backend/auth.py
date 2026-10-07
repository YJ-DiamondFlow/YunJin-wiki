# -*- coding: utf-8 -*-
"""
认证模块：密码哈希（PBKDF2-HMAC-SHA256，标准库实现）+ 会话令牌。
不依赖任何第三方库，不接入邮箱 / 手机号 / 第三方平台。
"""
import hashlib
import hmac
import os
import secrets

import config
import db


def hash_password(password: str, salt: str = None):
    """返回 (password_hash_hex, salt_hex)。"""
    if salt is None:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        config.PBKDF2_ITERATIONS,
    )
    return dk.hex(), salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        config.PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(dk.hex(), expected_hash)


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.create_session(token, user_id, config.SESSION_TTL)
    return token


def resolve_user(token: str):
    """根据 token 返回用户行，无效则返回 None。"""
    if not token:
        return None
    session = db.get_session(token)
    if not session:
        return None
    return db.get_user_by_id(session["user_id"])


def user_public(user) -> dict:
    """序列化为前端需要的公开字段。"""
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
        "last_login": user["last_login"],
    }
