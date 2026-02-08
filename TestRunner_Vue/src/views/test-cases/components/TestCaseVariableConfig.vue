<script setup lang="ts">
interface Props {
  modelValue: Record<string, any>
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'add'])

const handleDelete = (key: string) => {
  const newVariables = { ...props.modelValue }
  delete newVariables[key]
  emit('update:modelValue', newVariables)
}

const handleAdd = () => {
  emit('add')
}

const updateVariable = (key: string, value: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value
  })
}
</script>

<template>
  <div class="tw-space-y-4">
    <div v-for="(value, key) in modelValue" :key="key" class="tw-flex tw-gap-2">
      <a-input 
        :model-value="key" 
        placeholder="变量名" 
        class="tw-w-48" 
        disabled
      />
      <a-input 
        :model-value="value" 
        @update:model-value="val => updateVariable(key, val)"
        placeholder="变量值" 
        class="tw-flex-1" 
      />
      <a-button status="danger" @click="handleDelete(key)">删除</a-button>
    </div>
    <div class="tw-flex tw-justify-between tw-items-center">
      <a-button @click="handleAdd">添加变量</a-button>
      <span class="tw-text-gray-400 tw-text-sm">提示: 变量可在后续步骤中使用</span>
    </div>
  </div>
</template>

<style scoped>
.arco-input-wrapper {
  background-color: rgba(30, 41, 59, 0.5) !important;
}

.arco-input-wrapper:hover,
.arco-input-wrapper:focus-within {
  border-color: #60a5fa !important;
}

.arco-input {
  color: #e2e8f0 !important;
}
</style>