<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NAV_GROUPS } from '../nav'
import { state } from '../store'
import Icon from './Icon.vue'

const route = useRoute()

// slug -> 图标
const ICON_MAP = {}
NAV_GROUPS.forEach((g) => g.items.forEach((i) => (ICON_MAP[i.slug] = i.icon)))

// 已知分组顺序（按 nav 配置）
const KNOWN_ORDER = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.slug))

const groups = computed(() => {
  // 页面列表尚未加载时，先用静态配置兜底，避免导航闪烁
  if (!state.pages.length) {
    return NAV_GROUPS.map((g) => ({ title: g.title, items: g.items.map((i) => ({ ...i })) }))
  }

  const byslug = {}
  state.pages.forEach((p) => (byslug[p.slug] = p))
  const used = new Set()

  const gs = NAV_GROUPS.map((g) => ({
    title: g.title,
    items: g.items
      .filter((i) => byslug[i.slug])
      .map((i) => {
        used.add(i.slug)
        return { slug: i.slug, label: byslug[i.slug].title, icon: i.icon }
      })
  })).filter((g) => g.items.length > 0)

  // 其余新增页面归入「其他」
  const extra = state.pages
    .filter((p) => !used.has(p.slug) && !KNOWN_ORDER.includes(p.slug))
    .map((p) => ({ slug: p.slug, label: p.title, icon: 'file' }))

  if (extra.length) {
    const other = gs.find((g) => g.title === '其他')
    if (other) other.items = other.items.concat(extra)
    else gs.push({ title: '其他', items: extra })
  }
  return gs
})
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="logo">云</div>
      <div class="name">云锦巡梦</div>
      <div class="sub">官方 WIKI</div>
    </div>

    <nav class="nav-group" v-for="group in groups" :key="group.title">
      <div class="nav-group__title">{{ group.title }}</div>
      <ul class="nav-list">
        <li v-for="item in group.items" :key="item.slug">
          <router-link
            class="nav-link"
            :class="{ active: route.params.slug === item.slug }"
            :to="{ name: 'page', params: { slug: item.slug } }"
          >
            <Icon :name="item.icon" />
            <span>{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="sidebar-foot">
      云锦巡梦音游战队<br />© 2026 YunJin-wiki
    </div>
  </aside>
</template>
