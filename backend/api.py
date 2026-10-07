# -*- coding: utf-8 -*-
"""
API 路由层：纯 Python 实现，返回值统一为 (http_status, payload_dict)。
"""
import re

import auth
import config
import db

USERNAME_RE = re.compile(r"^[\w\u4e00-\u9fa5]{2,20}$")


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _require_auth(user):
    if not user:
        raise ApiError(401, "请先登录")


def _require_role(user, roles, message="没有权限执行该操作"):
    _require_auth(user)
    if user["role"] not in roles:
        raise ApiError(403, message)


def _validate_credentials(username, password):
    if not username or not isinstance(username, str):
        raise ApiError(400, "请输入用户名")
    if not USERNAME_RE.match(username):
        raise ApiError(400, "用户名需为 2-20 位的中文、字母、数字或下划线")
    if not password or not isinstance(password, str):
        raise ApiError(400, "请输入密码")
    if len(password) < 6:
        raise ApiError(400, "密码长度至少为 6 位")


# ---------------- 认证 ----------------
def register(payload, user):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    _validate_credentials(username, password)

    if db.get_user_by_username(username):
        raise ApiError(409, "该用户名已被注册，请换一个")

    pwd_hash, salt = auth.hash_password(password)
    new_user = db.create_user(username, pwd_hash, salt, config.ROLE_USER)
    token = auth.issue_token(new_user["id"])
    db.touch_last_login(new_user["id"])
    return 200, {"token": token, "user": auth.user_public(db.get_user_by_id(new_user["id"]))}


def login(payload, user):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        raise ApiError(400, "请输入用户名和密码")

    row = db.get_user_by_username(username)
    if not row or not auth.verify_password(password, row["salt"], row["password_hash"]):
        raise ApiError(401, "用户名或密码错误")

    token = auth.issue_token(row["id"])
    db.touch_last_login(row["id"])
    return 200, {"token": token, "user": auth.user_public(db.get_user_by_id(row["id"]))}


def logout(payload, user, token=None):
    if token:
        db.delete_session(token)
    return 200, {"ok": True}


def me(user):
    if not user:
        return 200, {"user": None}
    return 200, {"user": auth.user_public(user)}


# ---------------- 页面 ----------------
def list_pages(user):
    pages = db.list_pages()
    return 200, {"pages": [dict(p) for p in pages]}


def get_page(slug, user):
    page = db.get_page(slug)
    if not page:
        raise ApiError(404, "页面不存在")
    return 200, {"page": dict(page)}


def _note_pending(user, action, slug, title, content):
    """创建一条待审核变更，并给超级管理员发送站内消息。"""
    change = db.create_pending_change(
        action, slug, title, content, user["username"], user["id"]
    )
    verb = {"create": "新增", "update": "修改", "delete": "删除"}.get(action, "变更")
    db.add_notification(
        title=f"{user['username']} 提交了页面{verb}申请",
        body=f"页面「{title}」({slug}) 的{verb}申请等待审核。",
        link="/admin",
        target_role=config.ROLE_ADMIN,
    )
    return change


def update_page(slug, payload, user):
    _require_role(user, config.EDIT_ROLES, "你的账号没有编辑页面的权限")
    page = db.get_page(slug)
    if not page:
        raise ApiError(404, "页面不存在")
    title = (payload.get("title") or page["title"]).strip() or page["title"]
    content = payload.get("content")
    if content is None:
        raise ApiError(400, "内容不能为空")

    # 子管理员（普通 admin）的修改需要超级管理员审核
    if user["role"] != config.ROLE_ADMIN:
        change = _note_pending(user, "update", slug, title, content)
        return 200, {"status": "pending", "change": _serialize_change(change)}

    db.update_page(slug, title, content, user["username"])
    return 200, {"status": "applied", "page": dict(db.get_page(slug))}


def create_page(payload, user):
    _require_role(user, config.EDIT_ROLES, "你的账号没有创建页面的权限")
    slug = (payload.get("slug") or "").strip().lower()
    title = (payload.get("title") or "").strip()
    content = payload.get("content") or ""
    if not re.match(r"^[a-z0-9\-]{2,40}$", slug):
        raise ApiError(400, "页面标识(slug)只能包含小写字母、数字和连字符")
    if not title:
        raise ApiError(400, "请填写页面标题")
    if db.get_page(slug):
        raise ApiError(409, "该页面标识已存在")
    if slug in ("admin", "login", "register", "editor", "api"):
        raise ApiError(400, "该标识为系统保留字，请更换")

    # 子管理员（普通 admin）的新建需要超级管理员审核
    if user["role"] != config.ROLE_ADMIN:
        change = _note_pending(user, "create", slug, title, content)
        return 200, {"status": "pending", "change": _serialize_change(change)}

    db.create_page(slug, title, content, user["username"])
    return 200, {"status": "applied", "page": dict(db.get_page(slug))}


def delete_page(slug, user):
    _require_role(user, config.EDIT_ROLES, "你的账号没有删除页面的权限")
    page = db.get_page(slug)
    if not page:
        raise ApiError(404, "页面不存在")
    if slug in config.PROTECTED_PAGES:
        raise ApiError(403, "该页面为站点受保护页面，不允许删除")

    # 子管理员（普通 admin）的删除需要超级管理员审核
    if user["role"] != config.ROLE_ADMIN:
        change = _note_pending(user, "delete", slug, page["title"], "")
        return 200, {"status": "pending", "change": _serialize_change(change)}

    db.delete_page(slug)
    return 200, {"status": "applied", "slug": slug}


def _serialize_change(row):
    d = dict(row)
    d["content_length"] = len(d.get("content") or "")
    return d


# ---------------- 审核 ----------------
def list_pending(user):
    _require_role(user, (config.ROLE_ADMIN,), "仅超级管理员可以查看待审核列表")
    status = "pending"
    rows = db.list_pending_changes(status)
    return 200, {
        "changes": [_serialize_change(r) for r in rows],
        "pending_count": db.count_pending_changes(),
    }


def my_submissions(user):
    _require_auth(user)
    rows = db.list_pending_by_user(user["username"])
    return 200, {"changes": [_serialize_change(r) for r in rows]}


def _apply_change(change, reviewer):
    """把审核通过的变更真正写入页面。"""
    if change["action"] == "delete":
        if db.get_page(change["slug"]) and change["slug"] not in config.PROTECTED_PAGES:
            db.delete_page(change["slug"])
        return

    if change["action"] == "create":
        if db.get_page(change["slug"]):
            db.update_page(change["slug"], change["title"], change["content"], change["submitted_by"])
        else:
            db.create_page(change["slug"], change["title"], change["content"], change["submitted_by"])
    else:
        if db.get_page(change["slug"]):
            db.update_page(change["slug"], change["title"], change["content"], change["submitted_by"])
        else:
            db.create_page(change["slug"], change["title"], change["content"], change["submitted_by"])


def approve_pending(change_id, payload, user):
    _require_role(user, (config.ROLE_ADMIN,), "仅超级管理员可以审核")
    change = db.get_pending_change(int(change_id))
    if not change:
        raise ApiError(404, "该审核记录不存在")
    if change["status"] != "pending":
        raise ApiError(409, "该申请已被处理")
    _apply_change(change, user["username"])
    updated = db.set_pending_status(change["id"], "approved", user["username"], payload.get("note"))
    db.add_notification(
        title="你的页面申请已通过",
        body=f"页面「{change['title']}」的申请已由 {user['username']} 审核通过。",
        link=f"/wiki/{change['slug']}",
        target_user_id=change["submitted_by_id"],
    )
    return 200, {"change": _serialize_change(updated)}


def reject_pending(change_id, payload, user):
    _require_role(user, (config.ROLE_ADMIN,), "仅超级管理员可以审核")
    change = db.get_pending_change(int(change_id))
    if not change:
        raise ApiError(404, "该审核记录不存在")
    if change["status"] != "pending":
        raise ApiError(409, "该申请已被处理")
    note = payload.get("note") or ""
    updated = db.set_pending_status(change["id"], "rejected", user["username"], note)
    db.add_notification(
        title="你的页面申请被驳回",
        body=f"页面「{change['title']}」的申请被驳回。{('理由：' + note) if note else ''}",
        link="/admin",
        target_user_id=change["submitted_by_id"],
    )
    return 200, {"change": _serialize_change(updated)}


# ---------------- 通知 ----------------
def list_notifications(user):
    _require_auth(user)
    rows = db.list_notifications(user)
    return 200, {
        "notifications": [dict(r) for r in rows],
        "unread": db.count_unread_notifications(user),
    }


def read_notifications(payload, user):
    _require_auth(user)
    ids = payload.get("ids")
    db.mark_notifications_read(user, ids)
    return 200, {"ok": True}


def page_history(slug, user):
    rows = db.get_page_history(slug)
    return 200, {"history": [dict(r) for r in rows]}


# ---------------- 后台管理 ----------------
def admin_list_users(user):
    _require_role(user, config.ADMIN_PANEL_ROLES, "仅管理员可访问")
    rows = db.list_users()
    return 200, {"users": [dict(r) for r in rows]}


def admin_set_role(user_id, payload, user):
    # 仅超级管理员可以授予/取消子管理员
    _require_role(user, (config.ROLE_ADMIN,), "仅超级管理员可以修改用户角色")
    role = payload.get("role")
    if role not in (config.ROLE_USER, config.ROLE_SUB_ADMIN):
        raise ApiError(400, "角色只能设置为 user 或 sub_admin")
    target = db.get_user_by_id(int(user_id))
    if not target:
        raise ApiError(404, "用户不存在")
    if target["username"] == config.ADMIN_USERNAME:
        raise ApiError(403, "不能修改内置超级管理员的角色")
    db.set_user_role(target["id"], role)
    return 200, {"user": auth.user_public(db.get_user_by_id(target["id"]))}


def admin_delete_user(user_id, user):
    _require_role(user, (config.ROLE_ADMIN,), "仅超级管理员可以删除用户")
    target = db.get_user_by_id(int(user_id))
    if not target:
        raise ApiError(404, "用户不存在")
    if target["username"] == config.ADMIN_USERNAME:
        raise ApiError(403, "不能删除内置超级管理员")
    db.delete_user(target["id"])
    return 200, {"ok": True}


def admin_stats(user):
    _require_role(user, config.ADMIN_PANEL_ROLES, "仅管理员可访问")
    users = db.list_users()
    pages = db.list_pages()
    stat = {
        "user_total": len(users),
        "sub_admin_total": sum(1 for u in users if u["role"] == config.ROLE_SUB_ADMIN),
        "page_total": len(pages),
        "pending_total": db.count_pending_changes(),
    }
    return 200, {"stats": stat}
