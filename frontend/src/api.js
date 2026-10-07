// 统一的 API 请求封装：自动携带 token，统一错误处理
const TOKEN_KEY = 'yj_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request(method, url, body) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token

  const res = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body)
  })

  let data = null
  try {
    data = await res.json()
  } catch (e) {
    data = null
  }

  if (!res.ok) {
    const msg = (data && data.error) || `请求失败 (${res.status})`
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  // 认证
  register: (username, password) => request('POST', '/api/auth/register', { username, password }),
  login: (username, password) => request('POST', '/api/auth/login', { username, password }),
  logout: () => request('POST', '/api/auth/logout'),
  me: () => request('GET', '/api/auth/me'),

  // 页面
  listPages: () => request('GET', '/api/pages'),
  getPage: (slug) => request('GET', `/api/pages/${encodeURIComponent(slug)}`),
  updatePage: (slug, payload) => request('PUT', `/api/pages/${encodeURIComponent(slug)}`, payload),
  createPage: (payload) => request('POST', '/api/pages', payload),
  deletePage: (slug) => request('DELETE', `/api/pages/${encodeURIComponent(slug)}`),
  pageHistory: (slug) => request('GET', `/api/pages/${encodeURIComponent(slug)}/history`),

  // 后台
  adminUsers: () => request('GET', '/api/admin/users'),
  adminStats: () => request('GET', '/api/admin/stats'),
  setRole: (uid, role) => request('POST', `/api/admin/users/${uid}/role`, { role }),
  deleteUser: (uid) => request('DELETE', `/api/admin/users/${uid}`),

  // 审核
  listPending: () => request('GET', '/api/admin/pending'),
  mySubmissions: () => request('GET', '/api/my-submissions'),
  approvePending: (id, note) => request('POST', `/api/admin/pending/${id}/approve`, { note }),
  rejectPending: (id, note) => request('POST', `/api/admin/pending/${id}/reject`, { note }),

  // 消息
  notifications: () => request('GET', '/api/notifications'),
  readNotifications: (ids) => request('POST', '/api/notifications/read', { ids })
}
