<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getFunctions, type Function } from '@/api/function'
import { useProjectStore } from '@/stores/project'

interface Props {
  hooks?: string[]
}

const props = defineProps<Props>()

// 获取 project store
const projectStore = useProjectStore()

interface State {
  selectedFunctions: number[]
  functions: Function[]
  loading: boolean
}

const state = ref<State>({
  selectedFunctions: [],
  functions: [],
  loading: false
})

// 加载函数列表
const loadFunctions = async () => {
  if (!projectStore.currentProjectId) return
  
  state.value.loading = true
  try {
    const response = await getFunctions({
      project_id: Number(projectStore.currentProjectId),
      page: 1,
      page_size: 100
    })
    state.value.functions = response.data.results
    
    // 如果有初始 hooks，设置选中状态
    if (props.hooks && props.hooks.length > 0) {
      state.value.selectedFunctions = props.hooks.map(hook => {
        const functionId = parseInt(hook)
        return isNaN(functionId) ? -1 : functionId
      }).filter(id => id !== -1)
    }
  } catch (error) {
    console.error('Failed to load functions:', error)
  } finally {
    state.value.loading = false
  }
}

// 监听项目变化
watch(() => projectStore.currentProjectId, () => {
  loadFunctions()
})

// 监听 hooks 变化
watch(() => props.hooks, (newHooks) => {
  if (newHooks && newHooks.length > 0) {
    state.value.selectedFunctions = newHooks.map(hook => {
      const functionId = parseInt(hook)
      return isNaN(functionId) ? -1 : functionId
    }).filter(id => id !== -1)
  } else {
    state.value.selectedFunctions = []
  }
})

// 向父组件暴露数据
defineExpose({
  // 根据不同场景返回不同格式
  getHooks: () => {
    // 调试时返回数组对象格式
    if (state.value.selectedFunctions.length > 0) {
      return state.value.selectedFunctions.map(id => {
        const func = state.value.functions.find(f => f.id === id)
        return func ? String(func.id) : ''
      }).filter(Boolean)
    }
    return []
  }
})

// 组件加载时获取函数列表
onMounted(() => {
  loadFunctions()
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-gap-4">
    <a-select
      v-model="state.selectedFunctions"
      :loading="state.loading"
      placeholder="选择前置函数"
      allow-clear
      multiple
    >
      <a-option
        v-for="func in state.functions"
        :key="func.id"
        :value="func.id"
      >
        {{ func.name }}
      </a-option>
    </a-select>

    <!-- 已选择函数列表 -->
    <div v-if="state.selectedFunctions.length > 0" class="tw-flex tw-flex-col tw-gap-2">
      <div class="tw-text-gray-400 tw-text-sm">已选择的函数：</div>
      <div class="tw-flex tw-flex-wrap tw-gap-2">
        <a-tag
          v-for="id in state.selectedFunctions"
          :key="id"
          closable
          @close="state.selectedFunctions = state.selectedFunctions.filter(fid => fid !== id)"
        >
          {{ state.functions.find(f => f.id === id)?.name || `函数${id}` }}
        </a-tag>
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-select-view) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  input {
    @apply tw-text-gray-200 tw-bg-transparent;
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
  @apply tw-bg-blue-500/20 tw-border-blue-500/50 tw-text-blue-500;
}
</style>