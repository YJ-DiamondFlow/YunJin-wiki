<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TopBar from './components/TopBar.vue'

const route = useRoute()
// 登录 / 注册页使用独立布局（无侧边栏与顶栏）
const bare = computed(() => ['login', 'register'].includes(route.name))

function closeMobileNav() {
  document.documentElement.setAttribute('data-mobile-nav', 'closed')
}

// 切换页面时关闭移动端抽屉，避免蒙层残留挡住内容
watch(() => route.fullPath, closeMobileNav, { immediate: true })
</script>

<template>
  <div v-if="bare">
    <router-view />
  </div>

  <div v-else class="app-shell">
    <div class="sidebar-backdrop" @click="closeMobileNav"></div>
    <Sidebar />
    <div class="main">
      <TopBar />
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>
