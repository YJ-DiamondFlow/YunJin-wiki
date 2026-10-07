import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './style.css'
import { initTheme, loadMe, refreshNotifications, refreshPages } from './store'

initTheme()

const app = createApp(App)

app.config.errorHandler = (err) => {
  // 打印到控制台，方便排查（不影响页面继续运行）
  console.error('[YunJin-wiki]', err)
}

// 先完成登录态检查，再挂载，避免后台页守卫误判
loadMe()
  .then(() => Promise.all([refreshNotifications(), refreshPages()]))
  .finally(() => {
    app.use(router).mount('#app')
    // 路由首次解析完成 = 应用真正可用（分片加载成功）
    router
      .isReady()
      .then(() => {
        window.__yjBooted = true
        sessionStorage.removeItem('yj_chunk_recover_at')
      })
      .catch(() => {
        /* 首次导航失败时由 router.onError 兜底处理 */
      })
  })
