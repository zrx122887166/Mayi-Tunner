<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FormInstance } from '@arco-design/web-vue'
import type { ApiModule } from '@/api/interface'
import { IconClose } from '@arco-design/web-vue/es/icon'

interface Props {
  visible: boolean
  type: 'create' | 'edit'
  loading: boolean
  apis?: ApiModule[]
  currentModule?: ApiModule
  parentId?: number
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  (e: 'update:visible', visible: boolean): void
  (e: 'submit', formData: any): void
}>()

const formRef = ref<FormInstance>()

// 表单数据
const formData = ref({
  name: '',
  description: '',
  parent: undefined as number | undefined
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入模块名称' }
  ]
}

// 关闭弹窗
const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    parent: undefined
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    emit('submit', {
      ...formData.value,
      parent: formData.value.parent || props.parentId || undefined
    })
  } catch (error) {
    // 表单验证失败
    console.error('表单验证失败:', error)
  }
}

// 监听visible变化,初始化表单数据
watch(() => props.visible, (newVal) => {
  if (newVal && props.type === 'edit' && props.currentModule) {
    formData.value = {
      name: props.currentModule.name,
      description: props.currentModule.description || '',
      parent: props.currentModule.parent === null ? undefined : props.currentModule.parent
    }
  } else {
    resetForm()
  }
})
</script>

<template>
  <div v-if="visible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
    <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleClose"></div>
    <a-card 
      :bordered="false"
      class="tw-w-[500px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
    >
      <template #title>
        <div class="tw-flex tw-justify-between tw-items-center">
          <span class="tw-text-gray-100">{{ type === 'create' ? '新建模块' : '编辑模块' }}</span>
          <a-button type="text" @click="handleClose">
            <template #icon>
              <icon-close />
            </template>
          </a-button>
        </div>
      </template>
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
        autocomplete="off"
      >
        <a-form-item field="name" label="模块名称" validate-trigger="blur">
          <a-input
            v-model="formData.name"
            placeholder="请输入模块名称"
            allow-clear
            :disabled="loading"
            aria-label="模块名称输入框"
            autocomplete="off"
          />
        </a-form-item>
        <a-form-item v-if="type === 'create'" field="parent" label="父级模块" validate-trigger="blur">
          <a-select
            v-model="formData.parent"
            placeholder="请选择父级模块（可选）"
            allow-clear
            :disabled="loading || !!parentId"
          >
            <a-option
              v-for="api in apis"
              :key="api.id"
              :value="api.id"
            >
              {{ api.name }}
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item field="description" label="模块描述" validate-trigger="blur">
          <a-textarea
            v-model="formData.description"
            placeholder="请输入模块描述"
            allow-clear
            :disabled="loading"
          />
        </a-form-item>
        <div class="tw-flex tw-justify-end tw-gap-2 tw-mt-6">
          <a-button @click="handleClose" class="tw-w-24" :disabled="loading" aria-label="取消">取消</a-button>
          <a-button type="primary" :loading="loading" @click="handleSubmit" class="tw-w-24" aria-label="确定">
            确定
          </a-button>
        </div>
      </a-form>
    </a-card>
  </div>
</template>