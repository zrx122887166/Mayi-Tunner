<script setup lang="ts">
import { ref } from 'vue'
import type { NewEnvironmentVariableData, VariableType } from '../../../api/environment'
import { VARIABLE_TYPES } from '../../../api/environment'
import {
  IconPlus,
  IconCode,
  IconEdit,
  IconInfoCircle,
  IconLock,
} from '@arco-design/web-vue/es/icon'

interface Props {
  modelValue: NewEnvironmentVariableData
}

interface Emits {
  (e: 'update:modelValue', value: NewEnvironmentVariableData): void
  (e: 'submit'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const updateField = (field: keyof NewEnvironmentVariableData, value: string | boolean) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

const handleSubmit = () => {
  if (!props.modelValue.name || !props.modelValue.value) {
    return
  }
  emit('submit')
}
</script>

<template>
  <div class="tw-p-5 tw-border tw-border-dashed tw-border-gray-700/50 tw-rounded-lg tw-space-y-4 hover:tw-border-gray-600/50 tw-transition-colors">
    <div class="tw-flex tw-items-center tw-gap-2">
      <div class="tw-w-6 tw-h-6 tw-rounded tw-bg-purple-500/10 tw-flex tw-items-center tw-justify-center">
        <icon-plus class="tw-text-purple-400 tw-text-sm" />
      </div>
      <span class="tw-text-sm tw-font-medium tw-text-gray-300">添加新变量</span>
    </div>
    
    <div class="tw-space-y-3">
      <a-input
        :model-value="modelValue.name"
        @update:model-value="val => updateField('name', val)"
        placeholder="变量名"
        allow-clear
        class="!tw-bg-gray-900/60"
      >
        <template #prefix>
          <icon-code class="tw-text-purple-400" />
        </template>
      </a-input>
      <a-input
        :model-value="modelValue.value"
        @update:model-value="val => updateField('value', val)"
        placeholder="变量值"
        allow-clear
        class="!tw-bg-gray-900/60"
      >
        <template #prefix>
          <icon-edit class="tw-text-purple-400" />
        </template>
      </a-input>

      <!-- 变量类型选择 -->
      <a-select
        :model-value="modelValue.type"
        @update:model-value="val => updateField('type', val)"
        placeholder="选择变量类型"
        class="!tw-bg-gray-900/60"
      >
        <a-option
          v-for="(label, type) in VARIABLE_TYPES"
          :key="type"
          :value="type"
        >
          {{ label }}
        </a-option>
      </a-select>

      <a-input
        :model-value="modelValue.description"
        @update:model-value="val => updateField('description', val)"
        placeholder="变量描述（选填）"
        allow-clear
        class="!tw-bg-gray-900/60"
      >
        <template #prefix>
          <icon-info-circle class="tw-text-purple-400" />
        </template>
      </a-input>

      <!-- 敏感变量开关 -->
      <div class="tw-flex tw-items-center tw-gap-3 tw-p-3 tw-bg-gray-900/40 tw-rounded-lg">
        <a-switch
          :model-value="modelValue.is_sensitive"
          @update:model-value="val => updateField('is_sensitive', val)"
          class="!tw-scale-110"
        />
        <div class="tw-flex tw-items-center tw-gap-2">
          <icon-lock class="tw-text-purple-400" />
          <span class="tw-text-gray-300">敏感变量</span>
        </div>
      </div>
    </div>

    <div class="tw-flex tw-justify-end">
      <a-button
        type="outline"
        status="success"
        @click="handleSubmit"
      >
        <template #icon><icon-plus /></template>
        添加变量
      </a-button>
    </div>
  </div>
</template> 