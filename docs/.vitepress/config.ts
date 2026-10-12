import { defineConfig } from 'vitepress'
import markdownItKatex from '@vscode/markdown-it-katex'
import footnote from 'markdown-it-footnote'

const katexPlugin = typeof markdownItKatex === 'function'
  ? markdownItKatex
  : (markdownItKatex as unknown as { default: typeof markdownItKatex }).default

export default defineConfig({
  lang: 'zh-CN',
  title: '洛谷档案馆文档',
  description: '洛谷档案馆使用文档',
  base: '/docs/',
  srcDir: './content',
  cleanUrls: true,
  appearance: true,
  head: [
    ['link', { rel: 'icon', href: '/docs/favicon.png' }],
    ['meta', { name: 'robots', content: 'noindex, nofollow, noarchive' }],
  ],
  markdown: {
    config(md) {
      md.use(katexPlugin, { throwOnError: false, enableBareBlocks: true })
      md.use(footnote)
    },
  },
  themeConfig: {
    logo: '/favicon.png',
    siteTitle: '洛谷档案馆文档',
    nav: [
      { text: '文档', link: '/' },
      { text: '返回档案馆', link: 'https://www.luogu.ac.cn/' },
    ],
    sidebar: [
      {
        text: '示例',
        items: [
          { text: '基础 Markdown', link: '/' },
          { text: '公式与内容块', link: '/examples/formatting' },
        ],
      },
    ],
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一页', next: '下一页' },
    sidebarMenuLabel: '目录',
    returnToTopLabel: '返回顶部',
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换浅色模式',
    darkModeSwitchTitle: '切换深色模式',
    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: { buttonText: '搜索文档', buttonAriaLabel: '搜索文档' },
              modal: {
                displayDetails: '显示详细结果',
                resetButtonTitle: '清空搜索',
                backButtonTitle: '关闭搜索',
                noResultsText: '没有找到相关内容',
                footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' },
              },
            },
          },
        },
      },
    },
    footer: { message: '第三方存档，与洛谷官方无关。' },
  },
})
