<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../store'
import Icon from '../components/Icon.vue'
import AuthBrand from '../components/AuthBrand.vue'

const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)
const userInput = ref(null)

onMounted(() => {
  // 进入登录页自动聚焦用户名，避免「页面打不了字」的错觉
  nextTick(() => userInput.value && userInput.value.focus())
})

async function submit() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  busy.value = true
  try {
    const user = await login(username.value.trim(), password.value)
    const redirect = route.query.redirect
    if (redirect) router.push(String(redirect))
    else if (user.role === 'admin' || user.role === 'sub_admin') router.push({ name: 'admin' })
    else router.push({ name: 'page', params: { slug: 'index' } })
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <AuthBrand />
    <div class="auth-card">
      <div class="auth-logo">云</div>
      <h1>登录云锦巡梦 Wiki</h1>
      <div class="sub">输入你的用户名和密码即可登录</div>

      <div v-if="error" class="alert alert--error">{{ error }}</div>

      <form @submit.prevent="submit">
        <div class="field">
          <label>用户名</label>
          <input
            ref="userInput"
            class="input"
            v-model="username"
            placeholder="请输入用户名"
            autocomplete="username"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
          />
        </div>
        <div class="field">
          <label>密码</label>
          <input
            class="input"
            type="password"
            v-model="password"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </div>
        <button class="btn btn--primary" type="submit" :disabled="busy">
          <Icon name="login" :size="16" />
          {{ busy ? '登录中…' : '登录' }}
        </button>
      </form>

      <div class="auth-switch">
        还没有账号？
        <router-link :to="{ name: 'register' }">立即注册</router-link>
        · <router-link :to="{ name: 'page', params: { slug: 'index' } }">返回首页</router-link>
      </div>
    </div>
  </div>
</template>
