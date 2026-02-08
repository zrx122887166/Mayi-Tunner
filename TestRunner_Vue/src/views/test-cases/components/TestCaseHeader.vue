<script setup lang="ts">
import { ref } from 'vue'
import { IconFire, IconClose, IconCheck, IconPlayArrow, IconHistory } from '@arco-design/web-vue/es/icon'
import type { TestCaseBasicInfo as TestCaseBasicInfoType } from '@/types/testcase'
import TestCaseBasicInfoComp from './TestCaseBasicInfo.vue'
import GroupManager from './GroupManager.vue'
import TagManager from './TagManager.vue'
import TestCaseConfigDialog from './TestCaseConfigDialog.vue'
import { useEnvironmentStore } from '@/stores/environment'
import { Message } from '@arco-design/web-vue'

interface Props {
  modelValue: TestCaseBasicInfoType
  loading?: boolean
  readonly?: boolean
  projectId: number
  testCaseId?: number
  steps?: {
    id: number
    name: string
    interface_data: {
      extract?: Record<string, string>
    }
  }[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'cancel', 'save', 'run', 'show-report'])

const environmentStore = useEnvironmentStore()
const isRunning = ref(false)

const updateValue = (key: keyof TestCaseBasicInfoType, value: any) => {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

const handleCancel = () => {
  emit('cancel')
}

const handleSave = () => {
  emit('save')
}

// 运行用例
const handleRun = async () => {
  if (!props.testCaseId) {
    Message.warning('请先保存用例')
    return
  }
  
  if (!environmentStore.currentEnvironmentId) {
    Message.warning('请先选择环境')
    return
  }

  emit('run', {
    testCaseId: props.testCaseId,
    environmentId: Number(environmentStore.currentEnvironmentId)
  })
}

// 显示报告
const handleShowReport = () => {
  if (!props.testCaseId) {
    Message.warning('请先保存用例')
    return
  }
  
  emit('show-report', props.testCaseId)
}
</script>

<template>
  <div class="tw-flex tw-justify-between tw-items-center">
    <div class="tw-flex tw-items-center tw-gap-4 tw-flex-wrap">
      <!-- 基本信息 -->
      <test-case-basic-info-comp
        :model-value="modelValue"
        @update:model-value="val => emit('update:modelValue', val)"
        :readonly="readonly"
      />

      <!-- 分组 -->
      <group-manager
        :model-value="modelValue.group"
        @update:model-value="val => updateValue('group', val)"
        :readonly="readonly"
        :project-id="projectId"
      />

      <!-- 标签 -->
      <tag-manager
        :model-value="modelValue.tags"
        @update:model-value="val => updateValue('tags', val)"
        :readonly="readonly"
        :project-id="projectId"
      />

      <!-- 优先级 -->
      <a-select
        :model-value="modelValue.priority"
        @update:model-value="val => updateValue('priority', val)"
        placeholder="优先级"
        class="!tw-w-24"
        :disabled="readonly"
      >
        <template #prefix>
          <icon-fire />
        </template>
        <a-option value="P0">P0</a-option>
        <a-option value="P1">P1</a-option>
        <a-option value="P2">P2</a-option>
        <a-option value="P3">P3</a-option>
      </a-select>

      <!-- 用例配置弹窗 -->
      <test-case-config-dialog
        :model-value="modelValue.config"
        @update:model-value="val => updateValue('config', val)"
        :readonly="readonly"
        :steps="props.steps"
      />
    </div>

    <!-- 操作按钮 -->
    <div class="tw-flex tw-items-center tw-gap-3">
      <!-- 运行按钮 -->
      <a-button 
        v-if="testCaseId" 
        type="outline" 
        size="small" 
        status="normal"
        class="!tw-flex !tw-items-center !tw-gap-1 !tw-h-8 btn-run" 
        :loading="isRunning" 
        @click="handleRun"
      >
        <template #icon>
          <icon-play-arrow class="!tw-text-[#10B981]" />
        </template>
        <span class="!tw-text-[#10B981]">运行</span>
      </a-button>
      
      <!-- 报告按钮 -->
      <a-button 
        v-if="testCaseId" 
        type="outline" 
        size="small" 
        status="normal"
        class="!tw-flex !tw-items-center !tw-gap-1 !tw-h-8 btn-report" 
        @click="handleShowReport"
      >
        <template #icon>
          <icon-history class="!tw-text-[#F97316]" />
        </template>
        <span class="!tw-text-[#F97316]">报告</span>
      </a-button>
      
      <a-button 
        type="outline" 
        size="small" 
        status="normal"
        class="!tw-flex !tw-items-center !tw-gap-1 !tw-h-8 btn-cancel" 
        @click="handleCancel"
      >
        <template #icon>
          <icon-close class="!tw-text-gray-400" />
        </template>
        <span class="!tw-text-gray-400">取消</span>
      </a-button>
      
      <a-button 
        v-if="!readonly" 
        type="outline" 
        size="small" 
        status="normal"
        class="!tw-flex !tw-items-center !tw-gap-1 !tw-h-8 btn-save" 
        :loading="loading" 
        @click="handleSave"
      >
        <template #icon>
          <icon-check class="!tw-text-[#8B5CF6]" />
        </template>
        <span class="!tw-text-[#8B5CF6]">保存</span>
      </a-button>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
:global(.arco-modal-mask) {
  backdrop-filter: blur(4px) !important;
  @apply tw-bg-black/60 !important;
}

:deep(.arco-modal) {
  @apply tw-bg-gray-900 tw-rounded-lg;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1), 0 0 40px rgba(0, 0, 0, 0.8) !important;
  border: none !important;
}

:deep(.arco-modal-header) {
  @apply tw-bg-transparent tw-border-b tw-border-gray-700 tw-pb-4;
}

:deep(.arco-modal-title) {
  @apply tw-text-gray-200;
}

:deep(.arco-modal-body) {
  @apply tw-bg-transparent tw-py-6;
}

:deep(.arco-modal-footer) {
  @apply tw-bg-transparent tw-border-t tw-border-gray-700 tw-pt-4;
}

:deep(.arco-table) {
  @apply tw-bg-transparent;
}

:deep(.arco-table-th) {
  @apply tw-bg-gray-900/60 tw-text-gray-400 tw-border-gray-700;
  &::before {
    @apply tw-bg-gray-700;
  }
}

:deep(.arco-table-td) {
  @apply tw-bg-transparent tw-text-gray-300 tw-border-gray-700;
}

:deep(.arco-table-tr) {
  &:hover {
    .arco-table-td {
      @apply tw-bg-gray-700/50;
    }
  }
}

:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  input {
    @apply tw-text-gray-200;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-textarea-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  textarea {
    @apply tw-text-gray-200;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-btn-dashed) {
  @apply tw-border-gray-600 tw-text-gray-400;
  
  &:hover {
    @apply tw-border-blue-500 tw-text-blue-500;
  }
}

:deep(.arco-btn-text) {
  @apply tw-text-gray-400;
  
  &:hover {
    @apply tw-text-blue-500 tw-bg-blue-500/10;
    
    &[status="danger"] {
      @apply tw-text-red-500 tw-bg-red-500/10;
    }
  }
}

:deep(.arco-select-view) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  input {
    @apply tw-text-gray-200;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-select-dropdown) {
  @apply tw-bg-gray-800 tw-border-gray-700;
  
  .arco-select-option {
    @apply tw-text-gray-300;
    
    &:hover {
      @apply tw-bg-gray-700;
    }
    
    &.arco-select-option-active {
      @apply tw-bg-blue-500/20 tw-text-blue-500;
    }
  }
}

:deep(.arco-tag) {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  max-width: 60px !important;
  height: 22px !important;
  margin: 0 !important;
  padding: 0 4px !important;
  background: rgba(148, 163, 184, 0.1) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  border-radius: 2px !important;
  
  .arco-tag-content {
    flex: 1 !important;
    min-width: 0 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    font-size: 12px !important;
    line-height: 20px !important;
    text-align: center !important;
  }

  .arco-icon-hover {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .arco-tag-close-btn {
    flex-shrink: 0 !important;
    margin-left: 4px !important;
    width: 12px !important;
    height: 12px !important;
    font-size: 12px !important;
    line-height: 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
}

/* 运行按钮样式 */
.btn-run {
  border-color: rgba(16, 185, 129, 0.2) !important;
  background-color: rgba(16, 185, 129, 0.05) !important;
  line-height: 1 !important;
  padding: 4px 10px !important;
  
  &:hover {
    border-color: rgba(16, 185, 129, 0.4) !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
  }
}

/* 报告按钮样式 */
.btn-report {
  border-color: rgba(249, 115, 22, 0.2) !important;
  background-color: rgba(249, 115, 22, 0.05) !important;
  line-height: 1 !important;
  padding: 4px 10px !important;
  
  &:hover {
    border-color: rgba(249, 115, 22, 0.4) !important;
    background-color: rgba(249, 115, 22, 0.1) !important;
  }
}

/* 取消按钮样式 */
.btn-cancel {
  border-color: rgba(148, 163, 184, 0.2) !important;
  background-color: rgba(148, 163, 184, 0.05) !important;
  line-height: 1 !important;
  padding: 4px 10px !important;
  
  &:hover {
    border-color: rgba(148, 163, 184, 0.4) !important;
    background-color: rgba(148, 163, 184, 0.1) !important;
  }
}

/* 保存按钮样式 */
.btn-save {
  border-color: rgba(139, 92, 246, 0.3) !important;
  background-color: rgba(139, 92, 246, 0.05) !important;
  line-height: 1 !important;
  padding: 4px 10px !important;
  
  &:hover {
    border-color: rgba(139, 92, 246, 0.5) !important;
    background-color: rgba(139, 92, 246, 0.1) !important;
  }
}
</style>