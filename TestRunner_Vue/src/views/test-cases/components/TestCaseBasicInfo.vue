<script setup lang="ts">
import { computed } from 'vue'
import { IconEdit, IconFile } from '@arco-design/web-vue/es/icon'
import type { TestCaseBasicInfo } from '@/types/testcase'

interface Props {
  modelValue: TestCaseBasicInfo
  readonly?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const name = computed({
  get: () => props.modelValue.name,
  set: (value) => updateValue('name', value)
})

const description = computed({
  get: () => props.modelValue.description,
  set: (value) => updateValue('description', value)
})

const updateValue = (key: keyof TestCaseBasicInfo, value: any) => {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <div class="tw-flex tw-items-center tw-gap-4">
    <!-- 用例名称 -->
    <a-input
      v-model="name"
      placeholder="请输入用例名称"
      class="tw-w-64"
      :readonly="readonly"
    >
      <template #prefix>
        <icon-edit />
      </template>
    </a-input>

    <!-- 描述 -->
    <a-input
      v-model="description"
      placeholder="请输入用例描述"
      class="tw-w-56"
      :readonly="readonly"
    >
      <template #prefix>
        <icon-file />
      </template>
    </a-input>
  </div>
</template> 