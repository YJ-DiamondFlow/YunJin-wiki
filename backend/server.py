# -*- coding: utf-8 -*-
"""
YunJin-wiki 后端入口 —— 纯 Python 标准库实现的 HTTP 服务器。
职责：
  1. 提供 /api/* 接口（认证、页面、后台管理）
  2. 托管前端构建产物（frontend/dist），支持 SPA 前端路由回退
无需安装任何第三方依赖，直接 `python backend/server.py` 即可运行。
"""
import json
import os
import re
import sys
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import api          # noqa: E402
import auth         # noqa: E402
import config       # noqa: E402
import db           # noqa: E402


# --------------------------- 路由表 ---------------------------
# (method, compiled_regex, handler(match, payload, user, token) -> (status, payload))
def _routes():
    def auth_user(req):
        return req.get("user")

    return [
        ("POST", re.compile(r"^/api/auth/register$"),
         lambda m, p, u, t: api.register(p, u)),
        ("POST", re.compile(r"^/api/auth/login$"),
         lambda m, p, u, t: api.login(p, u)),
        ("POST", re.compile(r"^/api/auth/logout$"),
         lambda m, p, u, t: api.logout(p, u, t)),
        ("GET", re.compile(r"^/api/auth/me$"),
         lambda m, p, u, t: api.me(u)),

        ("GET", re.compile(r"^/api/pages$"),
         lambda m, p, u, t: api.list_pages(u)),
        ("GET", re.compile(r"^/api/pages/(?P<slug>[\w\-]+)$"),
         lambda m, p, u, t: api.get_page(m.group("slug"), u)),
        ("PUT", re.compile(r"^/api/pages/(?P<slug>[\w\-]+)$"),
         lambda m, p, u, t: api.update_page(m.group("slug"), p, u)),
        ("DELETE", re.compile(r"^/api/pages/(?P<slug>[\w\-]+)$"),
         lambda m, p, u, t: api.delete_page(m.group("slug"), u)),
        ("GET", re.compile(r"^/api/pages/(?P<slug>[\w\-]+)/history$"),
         lambda m, p, u, t: api.page_history(m.group("slug"), u)),
        ("POST", re.compile(r"^/api/pages$"),
         lambda m, p, u, t: api.create_page(p, u)),

        ("GET", re.compile(r"^/api/admin/users$"),
         lambda m, p, u, t: api.admin_list_users(u)),
        ("POST", re.compile(r"^/api/admin/users/(?P<uid>\d+)/role$"),
         lambda m, p, u, t: api.admin_set_role(m.group("uid"), p, u)),
        ("DELETE", re.compile(r"^/api/admin/users/(?P<uid>\d+)$"),
         lambda m, p, u, t: api.admin_delete_user(m.group("uid"), u)),
        ("GET", re.compile(r"^/api/admin/stats$"),
         lambda m, p, u, t: api.admin_stats(u)),

        # 审核
        ("GET", re.compile(r"^/api/admin/pending$"),
         lambda m, p, u, t: api.list_pending(u)),
        ("GET", re.compile(r"^/api/my-submissions$"),
         lambda m, p, u, t: api.my_submissions(u)),
        ("POST", re.compile(r"^/api/admin/pending/(?P<cid>\d+)/approve$"),
         lambda m, p, u, t: api.approve_pending(m.group("cid"), p, u)),
        ("POST", re.compile(r"^/api/admin/pending/(?P<cid>\d+)/reject$"),
         lambda m, p, u, t: api.reject_pending(m.group("cid"), p, u)),

        # 消息通知
        ("GET", re.compile(r"^/api/notifications$"),
         lambda m, p, u, t: api.list_notifications(u)),
        ("POST", re.compile(r"^/api/notifications/read$"),
         lambda m, p, u, t: api.read_notifications(p, u)),

        ("GET", re.compile(r"^/api/health$"),
         lambda m, p, u, t: (200, {"ok": True})),
    ]


ROUTES = _routes()


class Handler(BaseHTTPRequestHandler):
    server_version = "YunJinWiki/1.0"
    # 使用 HTTP/1.1 以支持长连接（所有响应都必须带 Content-Length）
    protocol_version = "HTTP/1.1"

    # ---------------- 工具 ----------------
    def _send_bytes(self, status, content_type, body, cache=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if cache:
            self.send_header("Cache-Control", cache)
        self._cors()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status, payload, cache="no-store"):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, "application/json; charset=utf-8", body, cache)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def _token(self):
        authz = self.headers.get("Authorization", "")
        if authz.startswith("Bearer "):
            return authz[7:].strip()
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("yj_token="):
                return part[len("yj_token="):]
        return None

    # ---------------- 请求分发 ----------------
    def _handle(self, method):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path.startswith("/api/"):
            return self._handle_api(method, path)

        if method == "GET":
            return self._serve_static(path)
        return self._send_json(405, {"error": "方法不被允许"})

    def _handle_api(self, method, path):
        payload = self._read_body()
        token = self._token()
        user = auth.resolve_user(token)

        for route_method, pattern, fn in ROUTES:
            match = pattern.match(path)
            if not match:
                continue
            if route_method != method:
                continue
            try:
                status, data = fn(match, payload, user, token)
                return self._send_json(status, data)
            except api.ApiError as e:
                return self._send_json(e.status, {"error": e.message})
            except Exception as e:  # noqa: BLE001
                import traceback
                traceback.print_exc()
                return self._send_json(500, {"error": f"服务器内部错误: {e}"})

        return self._send_json(404, {"error": "接口不存在"})

    # ---------------- 静态文件 ----------------
    def _serve_static(self, path):
        dist = config.FRONTEND_DIST
        if not os.path.isdir(dist):
            return self._send_json(503, {
                "error": "前端尚未构建，请先运行 `cd frontend && npm install && npm run build`"
            })

        rel = path.lstrip("/") or "index.html"
        target = os.path.normpath(os.path.join(dist, rel))

        # 防止路径穿越
        if not target.startswith(os.path.abspath(dist)):
            target = os.path.join(dist, "index.html")

        if os.path.isdir(target) or not os.path.isfile(target):
            # 关键：带扩展名的静态资源（.js/.css/图片等）必须返回 404。
            # 如果这里回退成 index.html，浏览器会把 HTML 当成 JS 去解析，
            # 导致 Vite 的懒加载路由（登录页、注册页、后台页等）静默加载失败。
            # 只有「无扩展名的路由地址」（如 /login、/wiki/xxx）才回退到 index.html。
            if os.path.splitext(rel)[1]:
                return self._send_json(404, {"error": f"资源不存在: /{rel}"})
            target = os.path.join(dist, "index.html")

        if not os.path.isfile(target):
            return self._send_json(404, {"error": "资源不存在"})

        ctype, _ = mimetypes.guess_type(target)
        if ctype is None:
            ctype = "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"

        # 缓存策略：
        #  - 带内容哈希的 /assets/* 可以长期强缓存
        #  - 入口 index.html 必须每次校验，否则前端重新构建后
        #    浏览器仍会引用已被删除的旧文件名，导致页面打不开
        name = os.path.basename(target)
        if rel.replace("\\", "/").startswith("assets/"):
            cache = "public, max-age=31536000, immutable"
        elif name == "index.html":
            cache = "no-cache, no-store, must-revalidate"
        else:
            cache = "no-cache"

        with open(target, "rb") as f:
            data = f.read()
        self._send_bytes(200, ctype, data, cache)

    # ---------------- HTTP 方法 ----------------
    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def do_HEAD(self):
        self._handle("GET")

    def log_message(self, fmt, *args):
        sys.stderr.write("[YunJin-wiki] %s - %s\n" % (self.address_string(), fmt % args))


def main():
    db.init_db()
    db.purge_expired_sessions()
    httpd = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    print("=" * 56)
    print("  YunJin-wiki 服务已启动")
    print(f"  地址:  http://{config.HOST}:{config.PORT}")
    print(f"  数据库: {config.DB_PATH}")
    print(f"  管理员: {config.ADMIN_USERNAME}")
    print("  按 Ctrl+C 停止服务")
    print("=" * 56)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
