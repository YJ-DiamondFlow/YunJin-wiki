<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { renderMarkdown } from '../markdown'
import { isSubAdmin, roleLabel, state, refreshPages } from '../store'
import Icon from '../components/Icon.vue'

const router = useRouter()

const slug = ref('')
const title = ref('')
const content = ref('')
const error = ref('')
const okMsg = ref('')
const busy = ref(false)
const submittedSlug = ref('')

const preview = computed(() => renderMarkdown(content.value))
const reviewRequired = computed(() => isSubAdmin())

async function submit() {
  error.value = ''
  okMsg.value = ''
  const s = slug.value.trim().toLowerCase()
  if (!/^[a-z0-9-]{2,40}$/.test(s)) {
    error.value = '页面标识只能包含小写字母、数字和连字符（2-40 位）'
    return
  }
  if (!title.value.trim()) {
    error.value = '请填写页面标题'
    return
  }
  busy.value = true
  try {
    const data = await api.createPage({ slug: s, title: title.value.trim(), content: content.value })
    if (data.status === 'pending') {
      submittedSlug.value = s
      okMsg.value = '已提交，等待超级管理员审核通过后即可上线。'
    } else {
      await refreshPages()
      router.push({ name: 'page', params: { slug: s } })
    }
  } catch (e) {
    error.value = e.message || '提交失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div>
    <div class="editor-bar">
      <div>
        <h1 class="page-title page-title--plain page-title--sub">添加新页面</h1>
        <div class="page-subnote" style="margin-top:6px">
          <span class="dot"></span>支持 Markdown 语法，右侧实时预览
          <span v-if="reviewRequired" class="tag" style="margin-left:8px">
            当前身份：{{ roleLabel(state.user?.role) }}（需超级管理员审核）
          </span>
        </div>
      </div>
      <div class="actions">
        <router-link class="btn" :to="{ name: 'admin' }">
          <Icon name="back" :size="15" /> 返回后台
        </router-link>
      </div>
    </div>

    <div v-if="error" class="alert alert--error">{{ error }}</div>
    <div v-if="okMsg" class="alert alert--success">
      {{ okMsg }}
      <div style="margin-top:10px">
        <router-link class="btn btn--sm" :to="{ name: 'admin', query: { tab: 'review' } }">去查看审核状态</router-link>
        <router-link class="btn btn--sm" style="margin-left:8px" :to="{ name: 'create' }">再建一个</router-link>
      </div>
    </div>

    <div class="field">
      <label>页面标识（slug，用于访问地址 /wiki/xxx）</label>
      <input class="input" v-model="slug" placeholder="例如：team-rules（小写字母、数字、连字符）" :disabled="!!submittedSlug" />
      <div class="form-hint">访问地址将是 <code>/wiki/{{ slug || 'xxx' }}</code></div>
    </div>
    <div class="field">
      <label>页面标题</label>
      <input class="input" v-model="title" placeholder="页面标题" :disabled="!!submittedSlug" />
    </div>

    <div class="editor-grid">
      <div>
        <div class="section-title" style="margin-top:0"><span class="bar"></span>页面内容</div>
        <textarea class="textarea" style="min-height:460px" v-model="content" placeholder="在这里输入 Markdown 内容…" :disabled="!!submittedSlug"></textarea>
      </div>
      <div>
        <div class="section-title" style="margin-top:0"><span class="bar"></span>实时预览</div>
        <div class="editor-preview wiki-body" v-html="preview"></div>
      </div>
    </div>

    <div style="margin-top:22px">
      <button class="btn btn--primary" :disabled="busy || !!submittedSlug" @click="submit">
        <Icon :name="reviewRequired ? 'inbox' : 'plus'" :size="16" />
        {{ busy ? '提交中…' : (reviewRequired ? '提交审核' : '创建页面') }}
      </button>
    </div>
  </div>
</template>
