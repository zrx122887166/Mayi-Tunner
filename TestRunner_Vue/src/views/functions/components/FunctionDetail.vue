<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { IconClose, IconEdit } from '@arco-design/web-vue/es/icon'
import * as monaco from 'monaco-editor'
import type { Function } from '../../../api/function'

interface Props {
  loading?: boolean
  functionData: Function
}

interface Emits {
  (e: 'close'): void
  (e: 'edit', func: Function): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

// 代码编辑器相关
const editorContainer = ref<HTMLElement>()
const editor = shallowRef<monaco.editor.IStandaloneCodeEditor>()

// 初始化编辑器
const initEditor = () => {
  if (!editorContainer.value || editor.value) return

  editor.value = monaco.editor.create(editorContainer.value, {
    value: props.functionData.code,
    language: 'python',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: {
      enabled: true
    },
    readOnly: true,
    scrollBeyondLastLine: false,
    fontSize: 14,
    tabSize: 4,
    renderLineHighlight: 'all',
    roundedSelection: false,
    occurrencesHighlight: 'off',
    padding: {
      top: 10,
      bottom: 10
    }
  })
}

// 监听函数数据变化
watch(
  () => props.functionData,
  (newData) => {
    if (editor.value) {
      editor.value.setValue(newData.code)
    }
  },
  { deep: true }
)

onMounted(() => {
  initEditor()
})

onUnmounted(() => {
  if (editor.value) {
    editor.value.dispose()
  }
})

// 处理编辑按钮点击
const handleEdit = () => {
  emit('edit', props.functionData)
}
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-overflow-hidden">
    <a-spin :loading="loading" dot class="!tw-block tw-h-full">
      <!-- 头部区域 -->
      <div class="tw-px-6 tw-pt-6">
        <div class="tw-flex tw-justify-between tw-items-center tw-mb-6">
          <h3 class="tw-text-lg tw-font-medium tw-text-gray-100">函数详情</h3>
          <div class="tw-flex tw-items-center tw-gap-2">
            <a-button type="text" @click="handleEdit">
              <template #icon>
                <icon-edit />
              </template>
              编辑
            </a-button>
            <a-button type="text" @click="emit('close')">
              <template #icon>
                <icon-close />
              </template>
            </a-button>
          </div>
        </div>
        
        <!-- 基本信息区域 -->
        <div class="tw-grid tw-grid-cols-2 tw-gap-4 tw-mb-4">
          <div class="tw-flex tw-flex-col tw-gap-1">
            <span class="tw-text-gray-400 tw-text-sm">函数名称</span>
            <span class="tw-text-gray-100">{{ functionData.name }}</span>
          </div>
          <div class="tw-flex tw-flex-col tw-gap-1">
            <span class="tw-text-gray-400 tw-text-sm">状态</span>
            <span class="tw-text-gray-100">{{ functionData.is_active ? '启用' : '禁用' }}</span>
          </div>
          <div class="tw-flex tw-flex-col tw-gap-1">
            <span class="tw-text-gray-400 tw-text-sm">创建时间</span>
            <span class="tw-text-gray-100">{{ functionData.created_time }}</span>
          </div>
          <div class="tw-flex tw-flex-col tw-gap-1">
            <span class="tw-text-gray-400 tw-text-sm">更新时间</span>
            <span class="tw-text-gray-100">{{ functionData.updated_time }}</span>
          </div>
          <div class="tw-col-span-2 tw-flex tw-flex-col tw-gap-1">
            <span class="tw-text-gray-400 tw-text-sm">函数描述</span>
            <span class="tw-text-gray-100">{{ functionData.description || '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 代码编辑器区域 -->
      <div class="tw-flex-1 tw-min-h-0 tw-px-6 tw-pb-6">
        <div class="tw-text-gray-400 tw-text-sm tw-mb-2">函数代码</div>
        <div ref="editorContainer" class="tw-h-[calc(100%-2rem)] tw-min-h-[500px] tw-w-full tw-border tw-border-gray-700 tw-rounded"></div>
      </div>
    </a-spin>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-btn-text) {
  @apply tw-text-gray-400;
  
  &:hover {
    @apply tw-text-gray-200 tw-bg-gray-700/50;
  }
}
</style> 