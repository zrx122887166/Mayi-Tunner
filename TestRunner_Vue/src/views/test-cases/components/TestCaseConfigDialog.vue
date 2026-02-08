<script setup lang="ts">
import { ref, computed } from 'vue'
import { IconSettings, IconInfoCircle } from '@arco-design/web-vue/es/icon'
import type { TestCaseConfig } from '@/types/testcase'

interface Props {
  modelValue: TestCaseConfig
  readonly?: boolean
  steps?: {
    id: number
    name: string
    interface_data: {
      extract?: Record<string, string>
    }
  }[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const activeTab = ref('basic')

const config = ref<TestCaseConfig>({
  export: [],
  verify: false,
  base_url: '',
  variables: '{}',
  parameters: '{}'
})

// 从步骤中提取的变量列表
const extractVariables = computed(() => {
  const variables: Array<{
    stepId: number
    stepName: string
    key: string
    extract: string
  }> = []

  props.steps?.forEach(step => {
    if (step.interface_data.extract) {
      Object.entries(step.interface_data.extract).forEach(([key, extract]) => {
        variables.push({
          stepId: step.id,
          stepName: step.name,
          key,
          extract
        })
      })
    }
  })

  return variables
})

const handleOpen = () => {
  visible.value = true
  Object.assign(config.value, props.modelValue)
}

const handleSubmit = () => {
  emit('update:modelValue', { ...config.value })
  visible.value = false
}
</script>

<template>
  <div>
    <!-- 用例配置按钮 -->
    <a-button
      class="!tw-flex !tw-items-center !tw-gap-1"
      type="outline"
      size="small"
      status="normal"
      @click="handleOpen"
      :disabled="readonly"
    >
      <template #icon>
        <icon-settings class="!tw-text-[#165DFF]" />
      </template>
      <span class="!tw-text-[#165DFF]">用例配置</span>
    </a-button>

    <!-- 用例配置弹窗 -->
    <a-modal
      v-model:visible="visible"
      :width="800"
      title="用例配置"
      :mask-style="{ backgroundColor: 'rgba(0, 0, 0, 0.65)' }"
      @ok="handleSubmit"
    >
      <a-tabs v-model:active-key="activeTab">
        <!-- 基础配置 -->
        <a-tab-pane key="basic" title="基础配置">
          <div class="tw-space-y-4">
            <!-- Base URL -->
            <div class="tw-flex tw-items-center tw-gap-4">
              <span class="tw-w-24 tw-text-gray-400">Base URL</span>
              <a-input
                v-model="config.base_url"
                placeholder="请输入基础URL"
                class="tw-flex-1"
                allow-clear
              />
            </div>

            <!-- Verify -->
            <div class="tw-flex tw-items-center tw-gap-4">
              <span class="tw-w-24 tw-text-gray-400">SSL验证</span>
              <a-switch v-model="config.verify">
                <template #checked>开启</template>
                <template #unchecked>关闭</template>
              </a-switch>
            </div>

            <!-- Variables -->
            <div class="tw-flex tw-items-start tw-gap-4">
              <span class="tw-w-24 tw-text-gray-400 tw-mt-2">变量定义</span>
              <a-textarea
                v-model="config.variables"
                placeholder="请输入JSON格式的变量定义"
                :auto-size="{ minRows: 3, maxRows: 8 }"
                class="tw-flex-1 tw-font-mono"
                allow-clear
              />
            </div>

            <!-- Parameters -->
            <div class="tw-flex tw-items-start tw-gap-4">
              <span class="tw-w-24 tw-text-gray-400 tw-mt-2">参数定义</span>
              <a-textarea
                v-model="config.parameters"
                placeholder="请输入JSON格式的参数定义"
                :auto-size="{ minRows: 3, maxRows: 8 }"
                class="tw-flex-1 tw-font-mono"
                allow-clear
              />
            </div>
          </div>
        </a-tab-pane>

        <!-- 步骤依赖 -->
        <a-tab-pane key="dependencies" title="步骤依赖">
          <div class="tw-space-y-4">
            <div class="tw-flex tw-items-center tw-gap-2 tw-mb-4">
              <icon-info-circle class="tw-text-gray-400" />
              <span class="tw-text-gray-400">展示步骤间的数据依赖关系，变量从步骤响应中提取后可在后续步骤中使用</span>
            </div>
            <a-table :data="extractVariables" :pagination="false" :bordered="false">
              <template #columns>
                <a-table-column title="步骤" data-index="step">
                  <template #cell="{ record }">
                    <span class="tw-text-gray-300">{{ record.stepName }}</span>
                  </template>
                </a-table-column>
                <a-table-column title="变量名" data-index="key">
                  <template #cell="{ record }">
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <span class="tw-font-mono tw-text-[#165DFF]">${{ record.key }}</span>
                    </div>
                  </template>
                </a-table-column>
                <a-table-column title="提取规则" data-index="extract">
                  <template #cell="{ record }">
                    <span class="tw-font-mono tw-text-gray-400">{{ record.extract }}</span>
                  </template>
                </a-table-column>
              </template>
            </a-table>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-modal>
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

:deep(.arco-tabs-nav) {
  @apply tw-border-gray-700;
}

:deep(.arco-tabs-tab) {
  @apply tw-text-gray-400;
  
  &.arco-tabs-tab-active {
    @apply tw-text-[#165DFF];
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
</style> 