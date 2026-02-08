<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ApiModule, ApiInterface } from '@/api/interface'
import {
  IconPlus,
  IconDelete,
  IconRight,
  IconDown,
  IconSend,
  IconEdit
} from '@arco-design/web-vue/es/icon'
import request from '@/utils/request'
import { Message } from '@arco-design/web-vue'

interface Props {
  module: ApiModule
  level?: number
  expandedIds: number[]
  selectedId?: number
  formLoading?: boolean
  displayMode?: 'list' | 'detail'
}

const props = withDefaults(defineProps<Props>(), {
  level: 0,
  formLoading: false,
  displayMode: 'detail'
})

const emit = defineEmits<{
  (e: 'select', module: ApiModule): void
  (e: 'toggle-expand', id: number): void
  (e: 'edit', module: ApiModule): void
  (e: 'add-child', parentId: number): void
  (e: 'delete', module: ApiModule): void
  (e: 'edit-interface', api: ApiInterface): void
  (e: 'delete-interface', api: ApiInterface): void
  (e: 'run-interface', api: ApiInterface): void
  (e: 'select-interface', api: ApiInterface): void
}>()

// 接口列表相关状态
const interfaces = ref<ApiInterface[]>([])
const interfaceLoading = ref(false)

// 获取接口列表
const fetchInterfaces = async (moduleId: number) => {
  try {
    interfaceLoading.value = true
    const { data } = await request.get<{
      count: number
      next: string | null
      previous: string | null
      results: ApiInterface[]
    }>('/interfaces/', {
      params: {
        module_id: moduleId,
        project_id: props.module.project,
        page_size: 1000 // 设置较大的页面大小，确保能显示所有接口
      }
    })
    interfaces.value = data.results
    console.log(`模块${props.module.name}获取到${data.results.length}个接口`)
  } catch (error: any) {
    console.error('获取接口列表失败:', error)
  } finally {
    interfaceLoading.value = false
  }
}

// 导出刷新接口列表方法供父组件调用
defineExpose({
  refreshInterfaces: () => {
    if (props.module.id) {
      fetchInterfaces(props.module.id)
    }
  }
})

const paddingLeft = computed(() => {
  return props.level * 4 + 6
})

const isExpanded = computed(() => {
  return props.expandedIds.includes(props.module.id)
})

const isSelected = computed(() => {
  return props.selectedId === props.module.id
})

// 监听展开状态变化（仅在详情模式下加载接口）
watch(() => isExpanded.value, (newVal) => {
  if (newVal && props.module.id && props.displayMode === 'detail') {
    fetchInterfaces(props.module.id)
  }
})

// 记录已加载详情的接口ID
const loadedInterfaceIds = ref<Set<number>>(new Set())

// 获取接口详情
const fetchInterfaceDetail = async (api: ApiInterface) => {
  try {
    const { data } = await request.get<ApiInterface>(`/interfaces/${api.id}/`)
    // 更新接口数据
    const index = interfaces.value.findIndex(item => item.id === api.id)
    if (index !== -1) {
      interfaces.value[index] = data
    }
    // 标记为已加载
    if (api.id) {
      loadedInterfaceIds.value.add(api.id)
    }
    // 发送选择事件
    emit('select-interface', data)
  } catch (error: any) {
    console.error('获取接口详情失败:', error)
    Message.error('获取接口详情失败')
  }
}

// 处理接口选择
const handleInterfaceSelect = async (api: ApiInterface) => {
  console.log('接口被点击:', api)
  
  // 如果已经加载过详情，直接使用
  if (api.id && loadedInterfaceIds.value.has(api.id)) {
    console.log('接口已加载过详情，直接使用')
    emit('select-interface', api)
    return
  }
  
  console.log('接口未加载过详情，开始获取')
  // 否则请求详情
  await fetchInterfaceDetail(api)
}
</script>

<template>
  <div class="tw-space-y-1">
    <!-- 当前模块 -->
    <div
      class="tw-px-6 tw-py-2 tw-cursor-pointer tw-transition-colors tw-bg-[rgb(70,84,102,0.4)] hover:tw-bg-[rgb(47,66,114,0.4)] tw-rounded-lg"
      :class="{ 
        'tw-bg-[rgb(47,66,114,0.4)]': isSelected
      }"
      :style="{ paddingLeft: `${paddingLeft}px` }"
      @click.stop="emit('select', module)"
    >
      <div class="tw-flex tw-items-center tw-justify-between">
        <div class="tw-flex tw-items-center tw-gap-2">
          <div class="tw-w-4 tw-flex tw-items-center tw-justify-center">
            <a-button
              v-if="(displayMode === 'detail' && (module.children?.length || interfaces.length)) || (displayMode === 'list' && module.children?.length)"
              type="text"
              size="mini"
              class="!tw-w-4 !tw-h-4 !tw-p-0 !tw-min-w-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
              @click.stop="emit('toggle-expand', module.id)"
            >
              <template #icon>
                <icon-right v-if="!isExpanded" class="!tw-w-3 !tw-h-3" />
                <icon-down v-else class="!tw-w-3 !tw-h-3" />
              </template>
            </a-button>
            <div v-else class="tw-w-4"></div>
          </div>
          <a-spin :loading="interfaceLoading" dot>
            <span class="tw-text-[#e5e6e8]">{{ module.name }}</span>
          </a-spin>
        </div>
        <div class="tw-flex tw-items-center -tw-mr-4">
          <a-button
            v-if="level < 2"
            type="text"
            size="mini"
            class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
            @click.stop="emit('add-child', module.id)"
          >
            <template #icon><icon-plus /></template>
          </a-button>
          <a-button
            type="text"
            size="mini"
            class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
            @click.stop="emit('edit', module)"
          >
            <template #icon><icon-edit /></template>
          </a-button>
          <a-button
            type="text"
            size="mini"
            class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
            @click.stop="emit('delete', module)"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </div>
    </div>

    <div v-if="isExpanded" class="tw-space-y-1">
      <!-- 接口列表（仅在详情模式下显示） -->
      <template v-if="displayMode === 'detail' && interfaces.length">
        <div class="tw-space-y-1">
          <div
            v-for="api in interfaces"
            :key="api.id"
            class="tw-px-6 tw-py-2 tw-text-sm tw-text-gray-400 hover:tw-text-gray-300 tw-rounded tw-bg-[rgb(70,84,102,0.2)] hover:tw-bg-[rgb(70,84,102,0.4)] tw-min-w-0 tw-cursor-pointer"
            :style="{ paddingLeft: `${paddingLeft + 4}px` }"
            @click="handleInterfaceSelect(api)"
          >
            <div class="tw-flex tw-items-center tw-justify-between">
              <div class="tw-flex tw-items-center tw-gap-2 tw-min-w-0 tw-flex-1">
                <a-tag
                  :color="api.method === 'GET' ? 'blue' : api.method === 'POST' ? 'green' : api.method === 'PUT' ? 'orange' : 'red'"
                  class="!tw-w-16 !tw-flex !tw-justify-center !tw-flex-shrink-0"
                >
                  {{ api.method }}
                </a-tag>
                <span class="tw-truncate" :title="api.name">{{ api.name }}</span>
              </div>
              <div class="tw-flex tw-items-center -tw-mr-4 tw-ml-4">
                <a-button
                  type="text"
                  size="mini"
                  class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                  @click.stop="emit('run-interface', api)"
                  title="调试接口"
                >
                  <template #icon><icon-send /></template>
                </a-button>
                <a-button
                  type="text"
                  size="mini"
                  class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                  @click.stop="emit('edit-interface', api)"
                  title="编辑接口"
                >
                  <template #icon><icon-edit /></template>
                </a-button>
                <a-button
                  type="text"
                  size="mini"
                  class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                  @click.stop="emit('delete-interface', api)"
                  title="删除接口"
                >
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 子模块递归渲染 -->
      <div v-if="module.children?.length" class="tw-space-y-1">
        <ModuleTree
          v-for="child in module.children"
          :key="child.id"
          :module="child"
          :level="level + 1"
          :expanded-ids="expandedIds"
          :selected-id="selectedId"
          :form-loading="formLoading"
          :display-mode="displayMode"
          @select="emit('select', $event)"
          @toggle-expand="emit('toggle-expand', $event)"
          @edit="emit('edit', $event)"
          @add-child="emit('add-child', $event)"
          @delete="emit('delete', $event)"
          @edit-interface="emit('edit-interface', $event)"
          @delete-interface="emit('delete-interface', $event)"
          @run-interface="emit('run-interface', $event)"
          @select-interface="emit('select-interface', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
/* 隐藏滚动条但保留滚动功能 */
.tw-scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

.tw-scrollbar-hide::-webkit-scrollbar {
  display: none;  /* Chrome, Safari and Opera */
}
</style>