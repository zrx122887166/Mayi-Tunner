<script setup lang="ts">
import { ref, computed } from 'vue'
import { useClipboard } from '@vueuse/core'
import { Message } from '@arco-design/web-vue'
import { IconCopy } from '@arco-design/web-vue/es/icon'

interface Response {
  status: number | null
  time: number | null
  size: number | null
  data: any
  request: any
  response: any
  validation_results: any
  extracted_variables: any
}

interface Props {
  response: Response | null
}

const props = defineProps<Props>()

const selectedContentType = ref('json')

const { copy } = useClipboard()

// 复制内容到剪贴板
const copyContent = async (content: string) => {
  await copy(content)
  Message.success('复制成功')
}

// 计算响应体的内容
const responseContent = computed(() => {
  const content = props.response?.data?.response?.content
  if (!content) return ''

  if (typeof content === 'object') {
    return JSON.stringify(content, null, 2)
  }
  return content
})

// 计算请求信息的内容
const requestContent = computed(() => {
  if (!props.response?.data?.request) return ''
  return JSON.stringify(props.response.data.request, null, 2)
})

// 计算响应头的内容
const responseHeadersContent = computed(() => {
  if (!props.response?.data?.response?.headers) return ''
  return JSON.stringify(props.response.data.response.headers, null, 2)
})

// 获取响应状态码
const statusCode = computed(() => {
  return props.response?.data?.response?.status_code
})

// 计算提取变量的内容
const extractedContent = computed(() => {
  if (!props.response?.data?.extracted_variables) return ''
  return JSON.stringify(props.response.data.extracted_variables, null, 2)
})

// 计算完整数据的内容
const completeContent = computed(() => {
  if (!props.response) return ''
  return JSON.stringify(props.response, null, 2)
})

// 判断响应内容的语言类型
const responseLanguage = computed(() => {
  if (!props.response?.data?.response) return 'text'
  const contentType = props.response.data.response.headers?.['Content-Type']?.toLowerCase() || ''
  if (contentType.includes('application/json')) return 'json'
  if (contentType.includes('text/html')) return 'html'
  if (contentType.includes('text/xml')) return 'xml'
  if (contentType.includes('text/css')) return 'css'
  if (contentType.includes('javascript')) return 'javascript'
  return 'text'
})

// 顶部显示的响应消息
const responseMessage = computed(() => {
  if (props.response?.response?.content?.detail) {
    return props.response.response.content.detail
  }
  return props.response?.data?.message || ''
})
</script>

<template>
  <div v-if="response" class="tw-h-full tw-flex tw-flex-col">
    <!-- 顶部响应概要 -->
    <div class="tw-flex tw-items-center tw-gap-4 tw-px-4 tw-pt-4 tw-pb-2 tw-border-t tw-border-b tw-border-gray-700">
      <div class="tw-text-gray-400">响应内容</div>
      <div class="tw-flex-1"></div>
      <div class="tw-flex tw-items-center tw-gap-4 tw-flex-shrink-0">
        <a-tag v-if="statusCode" :color="statusCode === 200 ? 'green' : 'red'" class="tw-w-10 tw-flex tw-justify-center tw-items-center">
          {{ statusCode }}
        </a-tag>
        <span v-if="response.time" class="tw-text-gray-400">{{ response.time.toFixed(3) }} ms</span>
        <span v-if="response.size" class="tw-text-gray-400">{{ response.size }} bytes</span>
      </div>
    </div>

    <!-- 响应内容页签 -->
    <div class="tw-flex-1 tw-overflow-hidden">
      <a-tabs class="tw-h-full">
        <!-- 响应体 -->
        <a-tab-pane key="response" title="响应体">
          <div class="tw-h-full tw-overflow-auto">
            <div class="tw-p-4">
              <div v-if="response.data?.response?.content" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-relative group">
                <div
                  class="tw-absolute tw-right-2 tw-top-2 tw-cursor-pointer copy-button"
                  @click="copyContent(responseContent)"
                  title="复制"
                >
                  <icon-copy />
                </div>
                <pre class="tw-p-4 tw-text-gray-300 tw-font-mono tw-text-sm tw-leading-6 tw-whitespace-pre-wrap tw-break-all">{{ responseContent }}</pre>
              </div>
              <a-empty v-else description="暂无响应数据" />
            </div>
          </div>
        </a-tab-pane>

        <!-- 响应头 -->
        <a-tab-pane key="headers" title="响应头">
          <div class="tw-h-full tw-overflow-auto">
            <div class="tw-p-4">
              <div v-if="response.data?.response?.headers" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-relative group">
                <div
                  class="tw-absolute tw-right-2 tw-top-2 tw-cursor-pointer copy-button"
                  @click="copyContent(responseHeadersContent)"
                  title="复制"
                >
                  <icon-copy />
                </div>
                <pre class="tw-p-4 tw-text-gray-300 tw-font-mono tw-text-sm tw-leading-6 tw-whitespace-pre-wrap tw-break-all">{{ responseHeadersContent }}</pre>
              </div>
              <a-empty v-else description="暂无响应头数据" />
            </div>
          </div>
        </a-tab-pane>

        <!-- 请求信息 -->
        <a-tab-pane key="request" title="请求信息">
          <div class="tw-h-full tw-overflow-auto">
            <div class="tw-p-4">
              <div v-if="response.data?.request" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-relative group">
                <div
                  class="tw-absolute tw-right-2 tw-top-2 tw-cursor-pointer copy-button"
                  @click="copyContent(requestContent)"
                  title="复制"
                >
                  <icon-copy />
                </div>
                <pre class="tw-p-4 tw-text-gray-300 tw-font-mono tw-text-sm tw-leading-6 tw-whitespace-pre-wrap tw-break-all">{{ requestContent }}</pre>
              </div>
              <a-empty v-else description="暂无请求数据" />
            </div>
          </div>
        </a-tab-pane>

        <!-- 验证结果 -->
        <a-tab-pane key="validation" title="验证结果">
          <div class="tw-h-full tw-overflow-auto">
            <div class="tw-p-4">
              <div v-if="response.data?.validation_results?.length" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-p-4">
                <div v-for="(result, index) in response.data.validation_results" :key="index"
                  class="tw-flex tw-flex-col tw-p-3 tw-rounded-md tw-mb-3"
                  :class="{'tw-bg-green-900/10': result.check_result === 'pass', 'tw-bg-red-900/10': result.check_result !== 'pass'}"
                >
                  <!-- 验证结果标题栏 -->
                  <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <a-tag :color="result.check_result === 'pass' ? 'green' : 'red'" class="!tw-font-medium !tw-flex-shrink-0">
                        {{ result.check_result === 'pass' ? '通过' : '失败' }}
                      </a-tag>
                      <span class="tw-text-gray-300">{{ result.comparator }}: {{ result.check }}</span>
                    </div>
                  </div>

                  <!-- 验证详细信息 -->
                  <div class="tw-ml-1 tw-flex tw-flex-col tw-gap-2">
                    <!-- 实际值 -->
                    <div class="tw-flex tw-flex-col tw-gap-1">
                      <div class="tw-text-gray-400 tw-text-sm">实际值:
                        <span class="tw-text-gray-300 tw-font-mono">{{ result.check_value }}</span>
                      </div>
                    </div>

                    <!-- 期望值 -->
                    <div class="tw-flex tw-flex-col tw-gap-1">
                      <div class="tw-text-gray-400 tw-text-sm">期望值:
                        <span class="tw-text-gray-300 tw-font-mono">{{ result.expect_value }}</span>
                      </div>
                    </div>

                    <!-- 错误信息 -->
                    <div v-if="result.message" class="tw-mt-1 tw-text-red-400 tw-text-sm">
                      {{ result.message }}
                    </div>
                  </div>
                </div>
              </div>
              <a-empty v-else description="暂无验证结果" />
            </div>
          </div>
        </a-tab-pane>

        <!-- 提取变量 -->
        <a-tab-pane key="variables" title="提取变量">
          <div class="tw-h-full tw-overflow-auto">
            <div class="tw-p-4">
              <div v-if="response.data?.extracted_variables" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-p-4">
                <div v-for="(value, key) in response.data.extracted_variables" :key="key"
                  class="tw-flex tw-flex-col tw-p-3 tw-rounded-md tw-mb-3 tw-bg-gray-800/30 hover:tw-bg-gray-800/50"
                >
                  <div class="tw-flex tw-items-center">
                    <span class="tw-text-blue-400 tw-font-medium tw-font-mono">${{ key }}</span>
                  </div>
                  <div class="tw-mt-2 tw-text-gray-300 tw-font-mono tw-text-sm tw-break-all">{{ value }}</div>
                </div>
              </div>
              <a-empty v-else description="暂无提取变量" />
            </div>
          </div>
        </a-tab-pane>

        <!-- 完整数据 -->
        <a-tab-pane key="complete" title="完整数据">
          <div class="tw-h-full tw-overflow-auto">
            <div class="tw-p-4">
              <div v-if="response" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-relative group">
                <div
                  class="tw-absolute tw-right-2 tw-top-2 tw-cursor-pointer copy-button"
                  @click="copyContent(completeContent)"
                  title="复制"
                >
                  <icon-copy />
                </div>
                <pre class="tw-p-4 tw-text-gray-300 tw-font-mono tw-text-sm tw-leading-6 tw-whitespace-pre-wrap tw-break-all">{{ completeContent }}</pre>
              </div>
              <a-empty v-else description="暂无响应数据" />
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>

  <!-- 无响应时的提示 -->
  <div v-else class="tw-h-full tw-flex tw-flex-col">
    <div class="tw-flex tw-items-center tw-gap-4 tw-px-4 tw-pt-4 tw-pb-2 tw-border-t tw-border-b tw-border-gray-700">
      <div class="tw-text-gray-400">响应内容</div>
    </div>
    <div class="tw-flex-1 tw-flex tw-items-center tw-justify-center">
      <div class="tw-flex tw-flex-col tw-items-center tw-justify-center tw-text-gray-500">
        <div class="tw-w-16 tw-h-16 tw-mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1Z" />
          </svg>
        </div>
        <div class="tw-text-base">暂无响应数据</div>
        <div class="tw-text-sm tw-mt-2">点击调试按钮发送请求</div>
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-tabs) {
  @apply tw-h-full tw-flex tw-flex-col;

  .arco-tabs-content {
    @apply tw-flex-1 tw-min-h-0;
  }

  .arco-tabs-header {
    @apply tw-border-b tw-border-gray-700;
  }

  .arco-tabs-nav-tab {
    @apply tw-border-b-0;
  }

  .arco-tabs-tab {
    @apply tw-text-gray-400;

    &.arco-tabs-tab-active {
      @apply tw-text-blue-500;
    }
  }
}

:deep(.arco-tag) {
  &.arco-tag-green {
    @apply tw-bg-green-500/20 tw-text-green-500 tw-border-green-500/20;
  }

  &.arco-tag-red {
    @apply tw-bg-red-500/20 tw-text-red-500 tw-border-red-500/20;
  }
}

:deep(.arco-empty) {
  @apply tw-py-8;
}

:deep(.arco-btn-text) {
  @apply tw-bg-gray-800/80 tw-p-2 tw-rounded hover:tw-bg-blue-500/20 hover:tw-text-blue-500;
}

/* 复制按钮样式 */
.copy-button {
  @apply tw-opacity-0 tw-transition-opacity tw-duration-300;
  @apply tw-flex tw-items-center tw-justify-center tw-w-8 tw-h-8 tw-bg-gray-800/80 tw-rounded hover:tw-bg-blue-500/20 hover:tw-text-blue-500;

  :deep(svg) {
    @apply tw-w-5 tw-h-5 tw-text-gray-300 hover:tw-text-white;
  }
}

/* 当鼠标悬停在代码区域上时显示复制按钮 */
.group:hover .copy-button {
  @apply tw-opacity-100;
}
</style>