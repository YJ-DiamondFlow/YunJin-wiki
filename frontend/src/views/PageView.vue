<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { renderMarkdown } from '../markdown'
import { canEdit } from '../store'
import Icon from '../components/Icon.vue'

const route = useRoute()
const page = ref(null)
const loading = ref(true)
const error = ref('')

const slug = computed(() => route.params.slug)
const html = computed(() => renderMarkdown(page.value ? page.value.content : ''))

async function load(s) {
  loading.value = true
  error.value = ''
  page.value = null
  try {
    const data = await api.getPage(s)
    page.value = data.page
  } catch (e) {
    error.value = e.message || '页面加载失败'
  } finally {
    loading.value = false
  }
}

watch(slug, (s) => load(s), { immediate: true })
</script>

<template>
  <div v-if="loading" class="loading">正在加载页面…</div>

  <div v-else-if="error" class="card">
    <h1 class="page-title">页面不存在</h1>
    <div class="page-subnote"><span class="dot"></span>来自云锦巡梦 Wiki</div>
    <div class="alert alert--error">{{ error }}</div>
    <router-link class="btn" :to="{ name: 'page', params: { slug: 'index' } }">
      <Icon name="back" :size="15" /> 返回首页
    </router-link>
  </div>

  <div v-else>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap">
      <h1 class="page-title" style="flex:1">{{ page.title }}</h1>
      <router-link
        v-if="canEdit()"
        class="btn"
        :to="{ name: 'editor', params: { slug: page.slug } }"
      >
        <Icon name="edit" :size="15" /> 编辑本页
      </router-link>
    </div>
    <div class="page-subnote">
      <span class="dot"></span>
      来自云锦巡梦 Wiki
      <span v-if="page.updated_by" class="tag" style="margin-left:8px">
        最后编辑：{{ page.updated_by }} · {{ page.updated_at }}
      </span>
    </div>

    <article class="wiki-body" v-html="html"></article>

    <div v-if="page.slug === 'index'" class="bottom-tip">
      Wiki 管理员的私货区域：
      <router-link :to="{ name: 'page', params: { slug: 'history' } }">历史</router-link>
      <span>|</span>
      <router-link :to="{ name: 'page', params: { slug: 'words' } }">一些话</router-link>
    </div>
  </div>
</template>
