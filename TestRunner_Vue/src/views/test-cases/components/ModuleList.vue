<script setup lang="ts">
import { ref, computed } from 'vue'
import { IconSearch } from '@arco-design/web-vue/es/icon'
import { type ApiModule } from '@/api/interface'
import ModuleTreeSelect from './ModuleTreeSelect.vue'

const props = defineProps<{
  modules: ApiModule[]
  expandedIds: number[]
  selectedId?: number
  loading: boolean
}>()

const emit = defineEmits(['select', 'toggle-expand'])

const searchKeyword = ref('')

const filteredModules = computed(() => {
  if (!searchKeyword.value) return props.modules
  
  const keyword = searchKeyword.value.toLowerCase()
  return props.modules.filter(item => 
    item.name.toLowerCase().includes(keyword)
  )
})
</script>

<template>
  <div class="tw-w-[280px] tw-bg-gray-800 tw-rounded-lg tw-border tw-border-gray-700 tw-overflow-hidden">
    <div class="tw-p-4 tw-border-b tw-border-gray-700">
      <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
        <span class="tw-text-[#e5e6e8]">模块列表</span>
      </div>
      <div class="tw-flex tw-items-center tw-gap-2">
        <a-input-search
          v-model="searchKeyword"
          placeholder="搜索模块"
          allow-clear
          class="!tw-bg-[rgb(70,84,102,0.4)] !tw-border-gray-600"
        >
          <template #prefix>
            <icon-search />
          </template>
        </a-input-search>
      </div>
    </div>
    <div class="tw-overflow-y-auto hide-scrollbar" style="height: 480px">
      <div class="tw-p-2 tw-space-y-1">
        <ModuleTreeSelect
          v-for="module in filteredModules"
          :key="module.id"
          :module="module"
          :expanded-ids="expandedIds"
          :selected-id="selectedId"
          :loading="loading"
          @select="$emit('select', $event)"
          @toggle-expand="$emit('toggle-expand', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.hide-scrollbar {
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none;  /* IE and Edge */
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;  /* Chrome, Safari and Opera */
}
</style>