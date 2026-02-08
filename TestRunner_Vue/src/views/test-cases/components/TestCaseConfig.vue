<script setup lang="ts">
import { 
  IconFile,
  IconSettings,
  IconLink,
} from '@arco-design/web-vue/es/icon'
import type { TestCaseBasicInfo, TestCaseConfig } from '@/types/testcase'

interface Props {
  modelValue: TestCaseBasicInfo
  readonly?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const updateValue = (key: keyof TestCaseBasicInfo, value: any) => {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

const updateConfig = (key: keyof TestCaseConfig, value: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    config: {
      ...props.modelValue.config,
      [key]: value
    }
  })
}
</script>

<template>
  <div class="tw-grid tw-grid-cols-3 tw-gap-6">
    <a-card class="tw-col-span-2 !tw-bg-gray-800/50 !tw-border-gray-700">
      <template #title>
        <div class="tw-flex tw-items-center tw-gap-2 tw-text-gray-300">
          <icon-file />
          <span>用例描述</span>
        </div>
      </template>
      <a-textarea 
        :model-value="modelValue.description" 
        @update:model-value="val => updateValue('description', val)"
        placeholder="请输入用例描述" 
        :auto-size="{ minRows: 3, maxRows: 6 }" 
      />
    </a-card>
    <a-card class="!tw-bg-gray-800/50 !tw-border-gray-700">
      <template #title>
        <div class="tw-flex tw-items-center tw-gap-2 tw-text-gray-300">
          <icon-settings />
          <span>用例配置</span>
        </div>
      </template>
      <div class="tw-space-y-4">
        <div class="tw-flex tw-justify-between tw-items-center">
          <span class="tw-text-gray-400">SSL验证</span>
          <a-switch 
            :model-value="modelValue.config.verify" 
            @update:model-value="val => updateConfig('verify', val)"
            size="small"
          >
            <template #checked>开启</template>
            <template #unchecked>关闭</template>
          </a-switch>
        </div>
        <a-input 
          :model-value="modelValue.config.base_url" 
          @update:model-value="val => updateConfig('base_url', val)"
          placeholder="请输入基础URL"
        >
          <template #prefix>
            <icon-link />
          </template>
        </a-input>
      </div>
    </a-card>
  </div>
</template>

<style lang="postcss" scoped>
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
</style>