# -*- coding: utf-8 -*-
"""
YunJin-wiki 后端配置
纯 Python 架构，无第三方依赖。
"""
import os

# 项目根目录（YunJin-wiki/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录与 SQLite 数据库
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "wiki.db")

# 前端构建产物目录（Vite build 输出）
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

# 服务监听配置
HOST = "127.0.0.1"
PORT = int(os.environ.get("YUNJIN_PORT", "8000"))

# ---------------- 内置管理员账号 ----------------
# 该账号拥有最高权限：自由编辑页面、查看全部用户、授予/取消子管理员
ADMIN_USERNAME = "DiamondFlow"
ADMIN_PASSWORD = "Diamond#Flow#0515"

# ---------------- 角色定义 ----------------
ROLE_ADMIN = "admin"          # 超级管理员（内置账号）
ROLE_SUB_ADMIN = "sub_admin"  # 子管理员（由超级管理员授予）
ROLE_USER = "user"            # 普通用户

# 拥有「编辑页面」权限的角色
EDIT_ROLES = (ROLE_ADMIN, ROLE_SUB_ADMIN)
# 拥有「访问 /admin 后台」权限的角色
ADMIN_PANEL_ROLES = (ROLE_ADMIN, ROLE_SUB_ADMIN)

# 受保护的页面标识：不允许删除（首页为站点入口，删除会破坏站点）
PROTECTED_PAGES = ("index",)

# 会话有效期（秒），默认 7 天
SESSION_TTL = 7 * 24 * 3600

# PBKDF2 迭代次数
PBKDF2_ITERATIONS = 120_000
