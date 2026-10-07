<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from './Icon.vue'
import { api } from '../api'
import {
  state, toggleTheme, logout, roleLabel, canEdit, refreshNotifications, markAllRead
} from '../store'

const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const notifOpen = ref(false)
const menuRef = ref(null)
const notifRef = ref(null)

const crumb = computed(() => {
  if (route.name === 'admin') return '后台管理'
  if (route.name === 'editor') return '编辑页面'
  if (route.name === 'create') return '添加新页面'
  if (route.meta && route.meta.title) return route.meta.title
  return '页面'
})

function toggleMobileNav() {
  const cur = document.documentElement.getAttribute('data-mobile-nav')
  document.documentElement.setAttribute('data-mobile-nav', cur === 'open' ? 'closed' : 'open')
}
function closeMobileNav() {
  document.documentElement.setAttribute('data-mobile-nav', 'closed')
}

async function onLogout() {
  menuOpen.value = false
  notifOpen.value = false
  await logout()
  router.push({ name: 'page', params: { slug: 'index' } })
}

function toggleNotif() {
  notifOpen.value = !notifOpen.value
  menuOpen.value = false
  if (notifOpen.value) refreshNotifications()
}

async function openNotif(n) {
  notifOpen.value = false
  if (!n.is_read) {
    try {
      await api.readNotifications([n.id])
    } catch (e) { /* 忽略 */ }
    n.is_read = 1
    state.unread = Math.max(0, state.unread - 1)
  }
  if (n.link) router.push(n.link)
}

async function readAll() {
  await markAllRead()
}

function onClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) menuOpen.value = false
  if (notifRef.value && !notifRef.value.contains(e.target)) notifOpen.value = false
}
onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
  <header class="topbar">
    <div class="topbar__left">
      <button class="icon-btn mobile-toggle" @click="toggleMobileNav" title="菜单">
        <Icon name="menu" />
      </button>
      <span class="topbar__crumb">
        <Icon name="home" :size="15" style="vertical-align:-3px;margin-right:6px;opacity:.6" />
        云锦巡梦 Wiki · {{ crumb }}
      </span>
    </div>

    <div class="topbar__right">
      <button class="icon-btn" @click="toggleTheme" :title="state.theme === 'light' ? '切换到暗色' : '切换到亮色'">
        <Icon :name="state.theme === 'light' ? 'moon' : 'sun'" />
      </button>

      <template v-if="state.user">
        <!-- 消息通知 -->
        <div class="menu" ref="notifRef">
          <button class="icon-btn notif-btn" @click.stop="toggleNotif" title="消息通知">
            <Icon name="bell" />
            <span v-if="state.unread > 0" class="notif-badge">{{ state.unread > 99 ? '99+' : state.unread }}</span>
          </button>
          <div v-if="notifOpen" class="menu__panel notif-panel">
            <div class="notif-head">
              <span>消息通知</span>
              <button v-if="state.unread > 0" class="notif-readall" @click="readAll">全部已读</button>
            </div>
            <div v-if="state.notifications.length === 0" class="notif-empty">暂无消息</div>
            <ul v-else class="notif-list">
              <li
                v-for="n in state.notifications"
                :key="n.id"
                class="notif-item"
                :class="{ unread: !n.is_read }"
                @click="openNotif(n)"
              >
                <div class="notif-title">{{ n.title }}</div>
                <div v-if="n.body" class="notif-body">{{ n.body }}</div>
                <div class="notif-time">{{ n.created_at }}</div>
              </li>
            </ul>
          </div>
        </div>

        <router-link v-if="canEdit()" class="btn btn--sm" :to="{ name: 'admin' }">
          <Icon name="shield" :size="15" /> 后台
        </router-link>
        <div class="menu" ref="menuRef">
          <button class="btn btn--sm" @click="menuOpen = !menuOpen">
            <Icon name="user" :size="15" />
            {{ state.user.username }}
          </button>
          <div v-if="menuOpen" class="menu__panel">
            <div class="menu__head">
              <div class="u">{{ state.user.username }}</div>
              <span class="role-badge" :class="state.user.role">{{ roleLabel(state.user.role) }}</span>
            </div>
            <router-link v-if="canEdit()" class="menu__item" :to="{ name: 'admin' }" @click="menuOpen = false">
              <Icon name="shield" :size="16" /> 进入后台管理
            </router-link>
            <button class="menu__item" @click="onLogout">
              <Icon name="logout" :size="16" /> 退出登录
            </button>
          </div>
        </div>
      </template>

      <template v-else>
        <router-link class="btn btn--sm" :to="{ name: 'login' }">
          <Icon name="login" :size="15" /> 登录
        </router-link>
        <router-link class="btn btn--sm btn--primary" :to="{ name: 'register' }">注册</router-link>
      </template>
    </div>
  </header>
</template>
