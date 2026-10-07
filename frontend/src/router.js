import { createRouter, createWebHistory } from 'vue-router'
import { canAccessAdmin, canEdit, isLoggedIn } from './store'

// ---------------------------------------------------------------------------
// 分片加载容错（重要）
// 前端每次重新构建都会改变文件名（内容哈希）。如果用户的浏览器还停留在旧版本
// 的页面上，再点「登录 / 注册 / 后台 / 编辑」时，对应的 JS 分片已经不存在，
// 动态 import 会失败，表现就是「页面点不动、输入框打不了字」。
// 这里在检测到这类错误时，自动完整跳转到用户本来想去的地址，拿到最新版本。
// ---------------------------------------------------------------------------
const RECOVER_KEY = 'yj_chunk_recover_at'
const RECOVER_WINDOW = 10000 // 10 秒内只自愈一次，避免死循环

function isChunkLoadError(err) {
  if (!err) return false
  const msg = String(err.message || err)
  return (
    err.name === 'ChunkLoadError' ||
    /dynamically imported module/i.test(msg) ||
    /Importing a module script failed/i.test(msg) ||
    /Loading chunk .* failed/i.test(msg) ||
    /error loading dynamically imported module/i.test(msg)
  )
}

function recoverOnce(target) {
  const last = Number(sessionStorage.getItem(RECOVER_KEY) || 0)
  if (Date.now() - last < RECOVER_WINDOW) return false
  sessionStorage.setItem(RECOVER_KEY, String(Date.now()))
  // 用整页导航（而不是 reload）前往目标地址，确保拿到最新的 index.html 与分片
  window.location.replace(target || window.location.pathname + window.location.search)
  return true
}

const PageView = () => import('./views/PageView.vue')
const LoginView = () => import('./views/LoginView.vue')
const RegisterView = () => import('./views/RegisterView.vue')
const EditorView = () => import('./views/EditorView.vue')
const CreatePageView = () => import('./views/CreatePageView.vue')
const AdminView = () => import('./views/AdminView.vue')

const routes = [
  { path: '/', redirect: { name: 'page', params: { slug: 'index' } } },
  { path: '/wiki/:slug', name: 'page', component: PageView },
  { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { guestOnly: true } },
  { path: '/editor/:slug', name: 'editor', component: EditorView, meta: { requiresEdit: true } },
  { path: '/new-page', name: 'create', component: CreatePageView, meta: { requiresEdit: true } },
  { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAdmin: true } },
  { path: '/:pathMatch(.*)*', redirect: { name: 'page', params: { slug: 'index' } } }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 路由级错误兜底：分片失效 → 整页跳到目标地址；其他错误只记录
router.onError((err, to) => {
  if (isChunkLoadError(err)) {
    const target = to && to.fullPath ? to.fullPath : null
    if (recoverOnce(target)) {
      console.warn('[YunJin-wiki] 检测到前端资源已更新，正在自动加载最新版本…')
    }
    return
  }
  console.error('[router]', err)
})

router.beforeEach((to) => {
  // 非管理员 / 子管理员访问后台 → 直接退回首页
  if (to.meta.requiresAdmin && !canAccessAdmin()) {
    return { name: 'page', params: { slug: 'index' } }
  }
  // 无编辑权限访问编辑器 → 去登录页
  if (to.meta.requiresEdit && !canEdit()) {
    return isLoggedIn()
      ? { name: 'page', params: { slug: 'index' } }
      : { name: 'login', query: { redirect: to.fullPath } }
  }
  // 已登录用户不再访问登录/注册页
  if (to.meta.guestOnly && isLoggedIn()) {
    return { name: 'page', params: { slug: 'index' } }
  }
  return true
})
