// Markdown 渲染（marked + DOMPurify 防 XSS）
import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  gfm: true,
  breaks: true
})

export function renderMarkdown(src) {
  if (!src) return ''
  const raw = marked.parse(src)
  return DOMPurify.sanitize(raw, { ADD_ATTR: ['target', 'rel'] })
}
