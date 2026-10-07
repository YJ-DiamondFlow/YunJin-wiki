// 全局状态：登录用户 + 主题
import { reactive } from 'vue'
import { api, getToken, setToken } from './api'

const THEME_KEY = 'yj_theme'

export const state = reactive({
  user: null,
  ready: false,   // 是否已完成首次 me() 检查
  theme: localStorage.getItem(THEME_KEY) || 'light',
  notifications: [],
  unread: 0,
  pages: []       // 页面列表（用于侧边栏动态导航）
})

// ---------------- 主题 ----------------
export function applyTheme(theme) {
  state.theme = theme
  localStorage.setItem(THEME_KEY, theme)
  document.documentElement.setAttribute('data-theme', theme)
}

export function toggleTheme() {
  applyTheme(state.theme === 'light' ? 'dark' : 'light')
}

export function initTheme() {
  applyTheme(state.theme)
}

// ---------------- 认证 ----------------
export async function loadMe() {
  if (!getToken()) {
    state.user = null
    state.ready = true
    return
  }
  try {
    const data = await api.me()
    state.user = data.user
  } catch (e) {
    state.user = null
    setToken('')
  } finally {
    state.ready = true
  }
}

export async function login(username, password) {
  const data = await api.login(username, password)
  setToken(data.token)
  state.user = data.user
  await refreshNotifications()
  return data.user
}

export async function register(username, password) {
  const data = await api.register(username, password)
  setToken(data.token)
  state.user = data.user
  await refreshNotifications()
  return data.user
}

export async function logout() {
  try {
    await api.logout()
  } catch (e) {
    /* 忽略 */
  }
  setToken('')
  state.user = null
  state.notifications = []
  state.unread = 0
}

// ---------------- 页面列表 ----------------
export async function refreshPages() {
  try {
    const data = await api.listPages()
    state.pages = data.pages
  } catch (e) {
    /* 静默失败 */
  }
}

// ---------------- 消息通知 ----------------
export async function refreshNotifications() {
  if (!state.user) {
    state.notifications = []
    state.unread = 0
    return
  }
  try {
    const data = await api.notifications()
    state.notifications = data.notifications
    state.unread = data.unread
  } catch (e) {
    /* 静默失败 */
  }
}

export async function markAllRead() {
  try {
    await api.readNotifications()
  } catch (e) {
    /* 忽略 */
  }
  state.notifications = state.notifications.map((n) => ({ ...n, is_read: 1 }))
  state.unread = 0
}

// ---------------- 权限辅助 ----------------
export const isLoggedIn = () => !!state.user
export const isAdmin = () => state.user && state.user.role === 'admin'
export const isSubAdmin = () => state.user && state.user.role === 'sub_admin'
export const canEdit = () => !!state.user && (state.user.role === 'admin' || state.user.role === 'sub_admin')
export const canAccessAdmin = () => canEdit()
export const needsReview = () => isSubAdmin()
export const roleLabel = (role) =>
  ({ admin: '超级管理员', sub_admin: '子管理员', user: '普通用户' }[role] || role)
