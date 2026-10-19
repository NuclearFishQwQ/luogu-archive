<script setup lang="ts">
import type { PluginComment } from '~/types/plugin'

const props = defineProps<{ articleId: string }>()

const auth = useAuthStore()
const api = useApi()
const route = useRoute()
const { render } = useMarkdown()
const { smart } = useTime()

const comments = ref<PluginComment[]>([])
const total = ref(0)
const page = ref(1)
const draft = ref('')
const loading = ref(true)
const loadingMore = ref(false)
const submitting = ref(false)
const errorText = ref('')
const pageSize = 20

const hasMore = computed(() => comments.value.length < total.value)
const loginUrl = computed(() => `/login?redirect=${encodeURIComponent(route.fullPath)}`)

async function load(reset = true) {
  if (reset) {
    loading.value = true
    page.value = 1
    errorText.value = ''
  } else {
    loadingMore.value = true
  }

  const nextPage = reset ? 1 : page.value + 1
  try {
    const result = await api<{
      items: PluginComment[]
      total: number
      page: number
    }>(`/plugins/${props.articleId}/comments`, {
      query: { page: nextPage, page_size: pageSize },
    })
    comments.value = reset ? result.items : [...comments.value, ...result.items]
    total.value = result.total
    page.value = result.page
  } catch (error: any) {
    errorText.value = error?.data?.message || '评论加载失败，请稍后重试。'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function submitComment() {
  const content = draft.value.trim()
  if (!content || submitting.value) return

  if (!auth.isLoggedIn) {
    await navigateTo(loginUrl.value)
    return
  }

  submitting.value = true
  errorText.value = ''
  try {
    await api(`/plugins/${props.articleId}/comments`, {
      method: 'POST',
      body: { content },
    })
    draft.value = ''
    await load(true)
  } catch (error: any) {
    errorText.value = error?.data?.message || '评论发送失败，请稍后重试。'
  } finally {
    submitting.value = false
  }
}

async function deleteComment(comment: PluginComment) {
  if (!comment.is_mine || !window.confirm('确定删除这条评论吗？')) return
  errorText.value = ''
  try {
    await api(`/plugins/${props.articleId}/comments/${comment.id}`, { method: 'DELETE' })
    await load(true)
  } catch (error: any) {
    errorText.value = error?.data?.message || '评论删除失败，请稍后重试。'
  }
}

onMounted(async () => {
  if (!auth.initialized) await auth.tryRefresh()
  await load()
})
</script>

<template>
  <section class="plugin-comments" aria-labelledby="plugin-comments-title">
    <header class="comments-heading">
      <div>
        <p class="section-kicker">插件留言</p>
        <h2 id="plugin-comments-title">评论 <span>{{ total }}</span></h2>
        <p class="comments-intro">分享使用体验、问题或建议。支持 Markdown。</p>
      </div>
    </header>

    <form v-if="auth.isLoggedIn" class="comment-composer" @submit.prevent="submitComment">
      <div class="composer-avatar" aria-hidden="true">
        {{ (auth.displayName || '我').slice(0, 1) }}
      </div>
      <div class="composer-main">
        <label class="sr-only" :for="`plugin-comment-${articleId}`">写一条评论</label>
        <textarea
          :id="`plugin-comment-${articleId}`"
          v-model="draft"
          maxlength="2000"
          rows="4"
          placeholder="写下你的想法…"
        />
        <div class="composer-footer">
          <span>{{ draft.length }}/2000 · 请保持友善并避免发布个人信息</span>
          <button type="submit" class="submit-button" :disabled="!draft.trim() || submitting">
            {{ submitting ? '发送中…' : '发表评论' }}
          </button>
        </div>
      </div>
    </form>
    <div v-else class="signin-prompt">
      <span class="signin-mark" aria-hidden="true">↳</span>
      <p>登录后即可参与讨论。</p>
      <NuxtLink :to="loginUrl">登录账号</NuxtLink>
    </div>

    <p v-if="errorText" class="comment-error" role="alert">
      {{ errorText }}
      <button type="button" @click="load()">重试</button>
    </p>

    <div class="comment-list" aria-live="polite">
      <p v-if="loading" class="list-state">正在载入评论…</p>
      <div v-else-if="!comments.length && !errorText" class="list-state empty-state">
        <span class="empty-rule" aria-hidden="true" />
        <strong>还没有评论</strong>
        <span>成为第一个分享使用体验的人。</span>
      </div>
      <article v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-avatar" aria-hidden="true">
          <img v-if="comment.avatar_url" :src="comment.avatar_url" alt="" loading="lazy">
          <span v-else>{{ (comment.display_name || '?').slice(0, 1) }}</span>
        </div>
        <div class="comment-main">
          <div class="comment-meta">
            <strong>{{ comment.display_name }}</strong>
            <time :datetime="comment.created_at" :title="comment.created_at">
              {{ smart(comment.created_at) }}
            </time>
            <span v-if="comment.is_mine" class="mine-label">我的评论</span>
            <button
              v-if="comment.is_mine"
              type="button"
              class="delete-button"
              @click="deleteComment(comment)"
            >删除</button>
          </div>
          <div class="lg-content comment-content" v-html="render(comment.content)" />
        </div>
      </article>
      <button
        v-if="!loading && hasMore"
        type="button"
        class="load-more"
        :disabled="loadingMore"
        @click="load(false)"
      >{{ loadingMore ? '载入中…' : '加载更多评论' }}</button>
    </div>
  </section>
</template>

<style scoped>
.plugin-comments {
  display: grid;
  gap: 20px;
  padding: 22px 24px 24px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
}
.comments-heading { display: flex; justify-content: space-between; gap: 18px; }
.section-kicker { margin: 0 0 5px; color: var(--link); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.comments-heading h2 { display: flex; align-items: baseline; gap: 9px; margin: 0; font-size: 21px; }
.comments-heading h2 span { color: var(--text-muted); font-size: 14px; font-weight: 500; }
.comments-intro { margin: 5px 0 0; color: var(--text-muted); font-size: 13px; }
.comment-composer { display: flex; align-items: flex-start; gap: 12px; }
.composer-avatar, .comment-avatar { display: grid; flex: 0 0 36px; width: 36px; height: 36px; place-items: center; overflow: hidden; border-radius: 50%; background: color-mix(in srgb, var(--link) 16%, var(--surface)); color: var(--link); font-size: 15px; font-weight: 700; }
.composer-main { min-width: 0; flex: 1; }
.composer-main textarea { display: block; box-sizing: border-box; width: 100%; min-height: 92px; resize: vertical; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text); padding: 11px 12px; font: inherit; line-height: 1.6; }
.composer-main textarea::placeholder { color: var(--text-muted); }
.composer-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 8px; color: var(--text-muted); font-size: 12px; }
.submit-button, .load-more { border: 1px solid var(--link); border-radius: 6px; background: var(--link); color: #fff; padding: 7px 13px; font: inherit; font-size: 13px; cursor: pointer; }
.submit-button:disabled, .load-more:disabled { cursor: wait; opacity: .58; }
.signin-prompt { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border: 1px dashed var(--border); border-radius: 6px; background: color-mix(in srgb, var(--hover) 60%, var(--surface)); }
.signin-prompt p { flex: 1; margin: 0; color: var(--text-muted); font-size: 13px; }
.signin-prompt a { color: var(--link); font-size: 13px; font-weight: 600; text-decoration: none; }
.signin-prompt a:hover { text-decoration: underline; }
.signin-mark { color: var(--link); font-size: 18px; }
.comment-list { display: grid; }
.comment-item { display: flex; gap: 12px; padding: 16px 0; border-top: 1px solid var(--border); }
.comment-avatar { flex-basis: 34px; width: 34px; height: 34px; background: var(--hover); color: var(--text-muted); font-size: 14px; }
.comment-avatar img { display: block; width: 100%; height: 100%; object-fit: cover; }
.comment-main { min-width: 0; flex: 1; }
.comment-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 7px 10px; min-height: 26px; font-size: 13px; }
.comment-meta strong { color: var(--text); }
.comment-meta time { color: var(--text-muted); font-size: 12px; }
.mine-label { padding: 1px 6px; border-radius: 3px; background: color-mix(in srgb, var(--link) 12%, var(--surface)); color: var(--link); font-size: 11px; }
.delete-button, .comment-error button { border: 0; background: transparent; color: var(--text-muted); padding: 2px 4px; font: inherit; font-size: 12px; cursor: pointer; }
.delete-button:hover, .comment-error button:hover { color: var(--lg-red); }
.comment-content { margin-top: 6px; color: var(--text); font-size: 14px; line-height: 1.7; overflow-wrap: anywhere; }
.comment-content :deep(> :first-child) { margin-top: 0; }
.comment-content :deep(> :last-child) { margin-bottom: 0; }
.comment-content :deep(pre) { max-width: 100%; overflow: auto; }
.list-state { margin: 0; padding: 21px 0; color: var(--text-muted); font-size: 13px; text-align: center; }
.empty-state { display: grid; justify-items: center; gap: 5px; border-top: 1px solid var(--border); }
.empty-state strong { color: var(--text); font-size: 14px; }
.empty-rule { width: 28px; height: 2px; margin-bottom: 5px; background: var(--link); }
.comment-error { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin: 0; color: var(--lg-red); font-size: 13px; }
.load-more { justify-self: center; border-color: var(--border); background: var(--surface); color: var(--link); }
.load-more:hover { background: var(--hover); }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
:is(textarea, button, a):focus-visible { outline: 3px solid color-mix(in srgb, var(--link) 60%, transparent); outline-offset: 2px; }
@media (max-width: 640px) {
  .plugin-comments { gap: 16px; padding: 18px 15px; }
  .comment-composer { gap: 9px; }
  .composer-avatar { flex-basis: 30px; width: 30px; height: 30px; }
  .composer-footer { align-items: flex-end; }
  .composer-footer > span { max-width: 56%; line-height: 1.5; }
  .comment-item { gap: 9px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; }
}
</style>
