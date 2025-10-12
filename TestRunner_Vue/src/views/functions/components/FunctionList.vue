<script setup lang="ts">
import { ref, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconPlus, IconSearch, IconCode, IconEdit, IconDelete } from '@arco-design/web-vue/es/icon'
import type { Function } from '../../../api/function'

interface Props {
  loading?: boolean
  functions: Function[]
  selectedFunction: Function | null
}

interface Emits {
  (e: 'select', func: Function): void
  (e: 'create'): void
  (e: 'edit', func: Function): void
  (e: 'delete', func: Function): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const searchKeyword = ref('')

// 过滤后的函数列表
const filteredFunctions = computed(() => {
  if (!searchKeyword.value) return props.functions

  const keyword = searchKeyword.value.toLowerCase()
  return props.functions.filter(func => 
    func.name.toLowerCase().includes(keyword) || 
    func.description?.toLowerCase().includes(keyword)
  )
})

// 处理编辑按钮点击
const handleEditClick = (func: Function, event: Event) => {
  event.stopPropagation()
  emit('edit', func)
}

// 处理删除按钮点击
const handleDeleteClick = (func: Function, event: Event) => {
  event.stopPropagation()
  emit('delete', func)
}
</script>

<template>
  <div class="tw-w-56 tw-flex tw-flex-col">
    <div class="tw-flex-1 tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-overflow-hidden">
      <!-- 顶部标题和搜索栏 -->
      <div class="tw-p-4 tw-border-b tw-border-gray-700/50">
        <div class="tw-flex tw-justify-between tw-items-center tw-mb-4">
          <div class="tw-flex tw-items-center tw-gap-2">
            <h2 class="tw-text-lg tw-font-medium tw-text-gray-100">函数列表</h2>
          </div>
          <a-button type="text" size="small" @click="emit('create')">
            <template #icon><icon-plus /></template>
            新建
          </a-button>
        </div>
        <a-input-search
          v-model="searchKeyword"
          placeholder="搜索函数..."
          allow-clear
        >
          <template #prefix>
            <icon-search />
          </template>
        </a-input-search>
      </div>

      <!-- 函数列表内容 -->
      <div class="tw-flex-1 tw-overflow-hidden">
        <a-spin :loading="loading" dot class="!tw-block tw-h-full">
          <div class="tw-h-full tw-overflow-y-auto">
            <div class="tw-py-2">
              <a-empty v-if="filteredFunctions.length === 0" class="tw-p-4">
                暂无函数数据
              </a-empty>
              <template v-else>
                <div class="tw-space-y-1.5 tw-m-2">
                  <div
                    v-for="func in filteredFunctions"
                    :key="func.id"
                    class="tw-px-4 tw-py-2 tw-cursor-pointer tw-transition-colors tw-bg-[rgb(70,84,102,0.4)] hover:tw-bg-[rgb(47,66,114,0.4)] tw-rounded-lg"
                    :class="{ 
                      'tw-bg-[rgb(47,66,114,0.4)]': selectedFunction?.id === func.id
                    }"
                    @click="emit('select', func)"
                  >
                    <div class="tw-flex tw-items-center tw-justify-between">
                      <div class="tw-flex tw-items-center tw-gap-2">
                        <IconCode class="tw-text-blue-500 tw-w-4 tw-h-4" />
                        <span class="tw-text-[#e5e6e8] tw-truncate">{{ func.name }}</span>
                      </div>
                      <div class="tw-flex tw-items-center">
                        <a-button
                          type="text"
                          size="mini"
                          class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                          @click="(e) => handleEditClick(func, e)"
                        >
                          <template #icon><icon-edit /></template>
                        </a-button>
                        <a-button
                          type="text"
                          size="mini"
                          class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                          @click="(e) => handleDeleteClick(func, e)"
                        >
                          <template #icon><icon-delete /></template>
                        </a-button>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </a-spin>
      </div>
    </div>
  </div>
</template> 