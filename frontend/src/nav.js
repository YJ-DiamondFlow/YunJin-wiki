// 侧边栏导航配置（与 YJ-wiki 站点结构保持一致）
export const NAV_GROUPS = [
  {
    title: '导航',
    items: [
      { slug: 'index', label: '首页', icon: 'home' },
      { slug: 'member', label: '成员', icon: 'users' },
      { slug: 'about', label: '关于', icon: 'info' }
    ]
  },
  {
    title: '帮助',
    items: [
      { slug: 'examrule', label: '考核规则', icon: 'check' },
      { slug: 'recent', label: '最近更改', icon: 'clock' }
    ]
  },
  {
    title: '其他',
    items: [
      { slug: 'history', label: '历史', icon: 'book' },
      { slug: 'words', label: '一些话', icon: 'quote' }
    ]
  }
]
