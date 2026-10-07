<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../store'
import Icon from '../components/Icon.vue'
import AuthBrand from '../components/AuthBrand.vue'

const router = useRouter()

const username = ref('')
const password = ref('')
const confirm = ref('')
const error = ref('')
const busy = ref(false)
const userInput = ref(null)

onMounted(() => {
  nextTick(() => userInput.value && userInput.value.focus())
})

async function submit() {
  error.value = ''
  const name = username.value.trim()
  if (!name || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  if (name.length < 2) {
    error.value = '用户名至少 2 位'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码长度至少 6 位'
    return
  }
  if (password.value !== confirm.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  busy.value = true
  try {
    await register(name, password.value)
    router.push({ name: 'page', params: { slug: 'index' } })
  } catch (e) {
    error.value = e.message || '注册失败'
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
      <h1>注册新账号</h1>
      <div class="sub">只需用户名和密码，无需手机号或邮箱</div>

      <div v-if="error" class="alert alert--error">{{ error }}</div>

      <form @submit.prevent="submit">
        <div class="field">
          <label>用户名</label>
          <input
            ref="userInput"
            class="input"
            v-model="username"
            placeholder="2-20 位中文 / 字母 / 数字 / 下划线"
            autocomplete="username"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
          />
          <div class="form-hint">用户名不可重复</div>
        </div>
        <div class="field">
          <label>密码</label>
          <input class="input" type="password" v-model="password" placeholder="至少 6 位" autocomplete="new-password" />
        </div>
        <div class="field">
          <label>确认密码</label>
          <input class="input" type="password" v-model="confirm" placeholder="请再次输入密码" autocomplete="new-password" />
        </div>
        <button class="btn btn--primary" type="submit" :disabled="busy">
          <Icon name="user" :size="16" />
          {{ busy ? '注册中…' : '注册并登录' }}
        </button>
      </form>

      <div class="auth-switch">
        已有账号？
        <router-link :to="{ name: 'login' }">去登录</router-link>
        · <router-link :to="{ name: 'page', params: { slug: 'index' } }">返回首页</router-link>
      </div>
    </div>
  </div>
</template>
