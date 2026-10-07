<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { renderMarkdown } from '../markdown'
import { state, roleLabel, isAdmin, isSubAdmin, refreshNotifications, refreshPages } from '../store'
import Icon from '../components/Icon.vue'

const route = useRoute()

const tab = ref('overview')
const users = ref([])
const pages = ref([])
const pending = ref([])
const mine = ref([])
const stats = ref({ user_total: 0, sub_admin_total: 0, page_total: 0, pending_total: 0 })
const loading = ref(true)
const error = ref('')
const okMsg = ref('')
const busyId = ref(null)
const previewOpen = ref({})

const isSuper = computed(() => isAdmin())

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const jobs = [api.adminUsers(), api.listPages(), api.adminStats(), api.mySubmissions()]
    if (isSuper.value) jobs.push(api.listPending())
    const res = await Promise.all(jobs)
    users.value = res[0].users
    pages.value = res[1].pages
    stats.value = res[2].stats
    mine.value = res[3].changes
    if (isSuper.value) pending.value = res[4].changes
    await Promise.all([refreshNotifications(), refreshPages()])
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function flash(msg) {
  okMsg.value = msg
  setTimeout(() => (okMsg.value = ''), 2600)
}

async function setRole(user) {
  error.value = ''
  busyId.value = user.id
  try {
    const isSub = user.role === 'sub_admin'
    await api.setRole(user.id, isSub ? 'user' : 'sub_admin')
    flash(isSub ? `已取消 ${user.username} 的子管理员` : `已将 ${user.username} 设为子管理员`)
    await refresh()
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function removeUser(user) {
  if (!window.confirm(`确定要删除用户「${user.username}」吗？此操作不可恢复。`)) return
  error.value = ''
  busyId.value = user.id
  try {
    await api.deleteUser(user.id)
    flash(`已删除用户 ${user.username}`)
    await refresh()
  } catch (e) {
    error.value = e.message || '删除失败'
  } finally {
    busyId.value = null
  }
}

async function removePage(p) {
  const extra = isSubAdmin() ? '\n注意：你的删除申请需提交给超级管理员审核，通过后才会生效。' : ''
  if (!window.confirm(`确定要删除页面「${p.title}」（${p.slug}）吗？此操作不可恢复。${extra}`)) return
  error.value = ''
  busyId.value = 'p' + p.slug
  try {
    const data = await api.deletePage(p.slug)
    if (data.status === 'pending') flash(`已提交删除「${p.title}」的申请，等待超级管理员审核`)
    else flash(`已删除页面「${p.title}」`)
    await refresh()
  } catch (e) {
    error.value = e.message || '删除失败'
  } finally {
    busyId.value = null
  }
}

async function approve(change) {
  error.value = ''
  busyId.value = 'c' + change.id
  try {
    await api.approvePending(change.id)
    flash(`已通过「${change.title}」的申请，页面已更新`)
    await refresh()
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

async function reject(change) {
  const note = window.prompt(`驳回「${change.title}」的原因（可留空）：`, '')
  if (note === null) return
  error.value = ''
  busyId.value = 'c' + change.id
  try {
    await api.rejectPending(change.id, note)
    flash(`已驳回「${change.title}」的申请`)
    await refresh()
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    busyId.value = null
  }
}

const actionLabel = (a) =>
  ({ create: '新增页面', update: '修改页面', delete: '删除页面' }[a] || a)
const statusLabel = (s) => ({ pending: '待审核', approved: '已通过', rejected: '已驳回' }[s] || s)

onMounted(() => {
  if (route.query.tab) tab.value = String(route.query.tab)
  refresh()
})
</script>

<template>
  <div>
    <div>
      <h1 class="page-title page-title--plain">后台管理</h1>
      <div class="page-subnote" style="margin-bottom:28px">
        <span class="dot"></span>
        欢迎，{{ state.user?.username }}
        <span class="role-badge" :class="state.user?.role" style="margin-left:8px">
          {{ roleLabel(state.user?.role) }}
        </span>
      </div>
    </div>

    <div v-if="error" class="alert alert--error">{{ error }}</div>
    <div v-if="okMsg" class="alert alert--success">{{ okMsg }}</div>

    <!-- 统计 -->
    <div class="stat-grid">
      <div class="stat">
        <div class="num">{{ stats.user_total }}</div>
        <div class="lbl">注册用户总数</div>
      </div>
      <div class="stat">
        <div class="num">{{ stats.sub_admin_total }}</div>
        <div class="lbl">子管理员数量</div>
      </div>
      <div class="stat">
        <div class="num">{{ stats.page_total }}</div>
        <div class="lbl">Wiki 页面数量</div>
      </div>
      <div class="stat">
        <div class="num" :style="stats.pending_total > 0 ? 'color:var(--warning)' : ''">{{ stats.pending_total }}</div>
        <div class="lbl">待审核申请</div>
      </div>
    </div>

    <!-- 标签页 -->
    <div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap">
      <button class="btn btn--sm" :class="{ 'btn--primary': tab === 'overview' }" @click="tab = 'overview'">
        <Icon name="file" :size="15" /> 页面管理
      </button>
      <button v-if="isSuper" class="btn btn--sm" :class="{ 'btn--primary': tab === 'review' }" @click="tab = 'review'">
        <Icon name="inbox" :size="15" /> 待审核
        <span v-if="stats.pending_total > 0" class="count-pill">{{ stats.pending_total }}</span>
      </button>
      <button class="btn btn--sm" :class="{ 'btn--primary': tab === 'mine' }" @click="tab = 'mine'">
        <Icon name="clock" :size="15" /> 我的提交
        <span v-if="mine.filter((m) => m.status === 'pending').length > 0" class="count-pill">
          {{ mine.filter((m) => m.status === 'pending').length }}
        </span>
      </button>
      <button class="btn btn--sm" :class="{ 'btn--primary': tab === 'users' }" @click="tab = 'users'">
        <Icon name="users" :size="15" /> 用户管理
      </button>
    </div>

    <div v-if="loading" class="loading">正在加载…</div>

    <!-- 页面管理 -->
    <div v-else-if="tab === 'overview'">
      <div class="section-title">
        <span class="bar"></span>页面列表
        <router-link class="btn btn--sm btn--primary" style="margin-left:auto" :to="{ name: 'create' }">
          <Icon name="plus" :size="14" /> 添加新页面
        </router-link>
      </div>
      <div class="table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>页面</th>
              <th>标识 (slug)</th>
              <th>最后编辑人</th>
              <th>更新时间</th>
              <th style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in pages" :key="p.slug">
              <td class="u-name">{{ p.title }}</td>
              <td><code>{{ p.slug }}</code></td>
              <td>{{ p.updated_by || '—' }}</td>
              <td>{{ p.updated_at }}</td>
              <td style="text-align:right;white-space:nowrap">
                <router-link class="btn btn--sm btn--ghost" :to="{ name: 'page', params: { slug: p.slug } }">
                  <Icon name="eye" :size="14" /> 查看
                </router-link>
                <router-link class="btn btn--sm" style="margin-left:6px" :to="{ name: 'editor', params: { slug: p.slug } }">
                  <Icon name="edit" :size="14" /> 编辑
                </router-link>
                <button
                  v-if="p.slug !== 'index'"
                  class="btn btn--sm btn--danger"
                  style="margin-left:6px"
                  :disabled="busyId === 'p' + p.slug"
                  @click="removePage(p)"
                >
                  <Icon name="trash" :size="14" /> 删除
                </button>
                <span v-else class="tag" style="margin-left:6px">受保护</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="form-hint" style="margin-top:12px">
        说明：首页（index）为站点入口，不允许删除。子管理员的删除申请需提交给超级管理员审核，通过后才会生效。
      </p>
    </div>

    <!-- 待审核 -->
    <div v-else-if="tab === 'review'">
      <div class="section-title"><span class="bar"></span>待审核的页面变更</div>
      <div v-if="pending.length === 0" class="empty">当前没有待审核的申请 🎉</div>
      <div v-else class="review-list">
        <div v-for="c in pending" :key="c.id" class="review-card">
          <div class="review-card__head">
            <div class="review-card__title">
              <span class="pill" :class="c.action">{{ actionLabel(c.action) }}</span>
              {{ c.title }}
            </div>
            <span class="pill pending">待审核</span>
          </div>
          <div class="review-meta">
            <span>提交人：<strong>{{ c.submitted_by }}</strong></span>
            <span>标识：<code>{{ c.slug }}</code></span>
            <span>提交时间：{{ c.created_at }}</span>
            <span v-if="c.action !== 'delete'">内容长度：{{ c.content_length }} 字符</span>
            <span v-else>该申请将删除整个页面</span>
          </div>
          <div v-if="c.action !== 'delete'" class="review-actions" style="margin-bottom:12px">
            <button class="btn btn--sm" @click="previewOpen[c.id] = !previewOpen[c.id]">
              <Icon name="eye" :size="14" /> {{ previewOpen[c.id] ? '收起预览' : '查看内容' }}
            </button>
          </div>
          <div v-else class="alert alert--error" style="margin-bottom:12px">
            审核通过后，页面「{{ c.title }}」（{{ c.slug }}）将被永久删除。
          </div>
          <div v-if="previewOpen[c.id]" class="review-body wiki-body" v-html="renderMarkdown(c.content)"></div>
          <div class="review-actions">
            <button class="btn btn--primary btn--sm" :disabled="busyId === 'c' + c.id" @click="approve(c)">
              <Icon name="check2" :size="14" /> 通过并生效
            </button>
            <button class="btn btn--danger btn--sm" :disabled="busyId === 'c' + c.id" @click="reject(c)">
              <Icon name="close" :size="14" /> 驳回
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 我的提交 -->
    <div v-else-if="tab === 'mine'">
      <div class="section-title"><span class="bar"></span>我的提交记录</div>
      <div v-if="mine.length === 0" class="empty">你还没有提交过页面变更</div>
      <div v-else class="table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>类型</th>
              <th>页面</th>
              <th>标识</th>
              <th>状态</th>
              <th>提交时间</th>
              <th>审核人 / 备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in mine" :key="c.id">
              <td><span class="pill" :class="c.action">{{ actionLabel(c.action) }}</span></td>
              <td class="u-name">{{ c.title }}</td>
              <td><code>{{ c.slug }}</code></td>
              <td><span class="pill" :class="c.status">{{ statusLabel(c.status) }}</span></td>
              <td>{{ c.created_at }}</td>
              <td>
                <span v-if="c.reviewed_by">{{ c.reviewed_by }}</span>
                <span v-else>—</span>
                <span v-if="c.review_note" style="color:var(--text-muted)">：{{ c.review_note }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 用户管理 -->
    <div v-else>
      <div class="section-title">
        <span class="bar"></span>全部用户
        <span v-if="!isSuper" class="tag" style="margin-left:8px">子管理员仅可查看</span>
      </div>
      <div class="table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>角色</th>
              <th>注册时间</th>
              <th>最近登录</th>
              <th v-if="isSuper" style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td class="u-name">
                <Icon v-if="u.role === 'admin'" name="crown" :size="14" style="vertical-align:-2px;margin-right:5px;color:var(--warning)" />
                {{ u.username }}
              </td>
              <td><span class="role-badge" :class="u.role">{{ roleLabel(u.role) }}</span></td>
              <td>{{ u.created_at }}</td>
              <td>{{ u.last_login || '—' }}</td>
              <td v-if="isSuper" style="text-align:right;white-space:nowrap">
                <template v-if="u.role !== 'admin'">
                  <button class="btn btn--sm" :disabled="busyId === u.id" @click="setRole(u)">
                    <Icon :name="u.role === 'sub_admin' ? 'back' : 'shield'" :size="14" />
                    {{ u.role === 'sub_admin' ? '取消子管理员' : '设为子管理员' }}
                  </button>
                  <button class="btn btn--sm btn--danger" style="margin-left:8px" :disabled="busyId === u.id" @click="removeUser(u)">
                    <Icon name="trash" :size="14" /> 删除
                  </button>
                </template>
                <span v-else class="tag">内置账号</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="form-hint" style="margin-top:12px">
        提示：只有超级管理员（DiamondFlow）可以授予 / 取消子管理员及删除用户。
      </p>
    </div>
  </div>
</template>
