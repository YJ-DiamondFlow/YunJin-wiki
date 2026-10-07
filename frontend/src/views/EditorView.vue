<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { renderMarkdown } from '../markdown'
import { isSubAdmin, roleLabel, state } from '../store'
import Icon from '../components/Icon.vue'

const route = useRoute()
const router = useRouter()

const title = ref('')
const content = ref('')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const okMsg = ref('')
const pageMeta = ref(null)

const slug = computed(() => route.params.slug)
const preview = computed(() => renderMarkdown(content.value))

async function load(s) {
  loading.value = true
  error.value = ''
  try {
    const data = await api.getPage(s)
    pageMeta.value = data.page
    title.value = data.page.title
    content.value = data.page.content
  } catch (e) {
    error.value = e.message || '页面加载失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  error.value = ''
  okMsg.value = ''
  saving.value = true
  try {
    const data = await api.updatePage(slug.value, {
      title: title.value.trim(),
      content: content.value
    })
    if (data.status === 'pending') {
      okMsg.value = '修改已提交，需等待超级管理员审核通过后才会正式生效。'
    } else {
      pageMeta.value = data.page
      okMsg.value = '保存成功，页面已更新'
    }
    setTimeout(() => (okMsg.value = ''), 5000)
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

watch(slug, (s) => load(s), { immediate: true })
</script>

<template>
  <div v-if="loading" class="loading">正在加载编辑器…</div>

  <div v-else>
    <div class="editor-bar">
      <div>
        <h1 class="page-title page-title--plain page-title--sub">
          编辑：{{ pageMeta ? pageMeta.title : slug }}
        </h1>
        <div class="page-subnote" style="margin-top:6px">
          <span class="dot"></span>支持 Markdown 语法，右侧实时预览
          <span v-if="pageMeta" class="tag" style="margin-left:8px">
            上次：{{ pageMeta.updated_by }} · {{ pageMeta.updated_at }}
          </span>
        </div>
        <div v-if="isSubAdmin()" class="alert alert--info" style="margin:14px 0 0">
          当前身份为「{{ roleLabel(state.user?.role) }}」，保存的修改将提交给超级管理员审核，审核通过后才会生效。
        </div>
      </div>
      <div class="actions">
        <router-link class="btn" :to="{ name: 'page', params: { slug } }">
          <Icon name="back" :size="15" /> 返回页面
        </router-link>
        <button class="btn btn--primary" :disabled="saving" @click="save">
          <Icon name="save" :size="15" /> {{ saving ? '保存中…' : '保存' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert--error">{{ error }}</div>
    <div v-if="okMsg" class="alert alert--success">{{ okMsg }}</div>

    <div class="field">
      <label>页面标题</label>
      <input class="input" v-model="title" placeholder="页面标题" />
    </div>

    <div class="editor-grid">
      <div>
        <div class="section-title" style="margin-top:0"><span class="bar"></span>编辑内容</div>
        <textarea class="textarea" style="min-height:520px" v-model="content"></textarea>
      </div>
      <div>
        <div class="section-title" style="margin-top:0"><span class="bar"></span>实时预览</div>
        <div class="editor-preview wiki-body" v-html="preview"></div>
      </div>
    </div>
  </div>
</template>
