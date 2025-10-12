<script setup lang="ts">
import { ref, computed } from 'vue'
import { IconSearch, IconPlus } from '@arco-design/web-vue/es/icon'
import { type ApiInterface } from '@/api/interface'

const props = defineProps<{
  interfaces: ApiInterface[]
  selectedKeys: number[]
  loading: boolean
  currentModuleName?: string
}>()

const emit = defineEmits(['selection-change', 'row-click', 'confirm'])

const searchKeyword = ref('')

const filteredInterfaces = computed(() => {
  if (!searchKeyword.value) return props.interfaces

  const keyword = searchKeyword.value.toLowerCase()
  return props.interfaces.filter(item =>
    item.name.toLowerCase().includes(keyword) ||
    item.url.toLowerCase().includes(keyword)
  )
})
</script>

<template>
  <div class="tw-flex-1 tw-bg-gray-800 tw-rounded-lg tw-border tw-border-gray-700 tw-overflow-hidden">
    <div class="tw-p-4 tw-border-b tw-border-gray-700">
      <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
        <div class="tw-flex tw-items-center tw-gap-2">
          <span class="tw-text-[#e5e6e8]">接口列表</span>
          <span v-if="currentModuleName" class="tw-text-sm tw-text-gray-400">{{ currentModuleName }}</span>
        </div>
        <a-button
          type="primary"
          :disabled="!selectedKeys.length"
          @click="$emit('confirm')"
        >
          确定
        </a-button>
      </div>
      <div class="tw-flex tw-items-center tw-gap-2">
        <a-input-search
          v-model="searchKeyword"
          placeholder="搜索接口名称或URL"
          allow-clear
          class="!tw-bg-[rgb(70,84,102,0.4)] !tw-border-gray-600"
        >
          <template #prefix>
            <icon-search />
          </template>
        </a-input-search>
      </div>
    </div>
    <div class="tw-overflow-y-auto hide-scrollbar" style="height: 400px">
      <div class="tw-p-2">
        <a-table
          v-if="interfaces.length > 0"
          :data="filteredInterfaces"
          :loading="loading"
          :pagination="false"
          :bordered="false"
          :row-selection="{
            type: 'checkbox',
            showCheckedAll: true,
            selectedRowKeys: selectedKeys,
            onlyCurrent: false
          }"
          :row-key="'id'"
          @selection-change="(selectedRowKeys: (string | number)[]) => {
            console.log('Selection changed:', selectedRowKeys)
            const newKeys = selectedRowKeys.map(key => Number(key))
            console.log('New keys:', newKeys)
            $emit('selection-change', newKeys)
          }"
          :row-class="'tw-cursor-pointer hover:tw-bg-gray-700/50'"
          @row-click="(record) => $emit('row-click', record)"
          class="!tw-bg-transparent interface-table"
        >
          <template #columns>
            <a-table-column title="ID" data-index="id" :width="80">
              <template #cell="{ record }">
                <span class="tw-text-gray-400">{{ record.id }}</span>
              </template>
            </a-table-column>
            <a-table-column title="接口名称" data-index="name">
              <template #cell="{ record }">
                <span class="tw-text-gray-200">{{ record.name }}</span>
              </template>
            </a-table-column>
            <a-table-column title="请求方法" data-index="method" :width="100">
              <template #cell="{ record }">
                <a-tag
                  :color="record.method === 'GET' ? 'green' : record.method === 'POST' ? 'blue' : record.method === 'PUT' ? 'orange' : 'red'"
                  size="small"
                  class="!tw-min-w-[50px] !tw-text-center !tw-font-medium"
                >
                  {{ record.method }}
                </a-tag>
              </template>
            </a-table-column>
            <a-table-column title="URL" data-index="url">
              <template #cell="{ record }">
                <span class="tw-text-gray-400">{{ record.url }}</span>
              </template>
            </a-table-column>
          </template>
        </a-table>
        <div v-else class="tw-text-center tw-py-8 tw-text-gray-400">
          请选择左侧模块查看接口列表
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interface-table {
  --checkbox-size: 16px;
}

.interface-table :deep(.arco-checkbox) {
  background-color: transparent;
  border: 1px solid #4c5155;
  border-radius: 2px;
  width: var(--checkbox-size);
  height: var(--checkbox-size);
  display: flex;
  align-items: center;
  justify-content: center;
}

.interface-table :deep(.arco-checkbox:hover) {
  border-color: #165dff;
}

.interface-table :deep(.arco-checkbox-checked) {
  background-color: #165dff;
  border-color: #165dff;
}

.interface-table :deep(.arco-checkbox-checked .arco-checkbox-icon) {
  color: #fff;
  font-size: calc(var(--checkbox-size) * 0.75);
}

.interface-table :deep(.arco-table-th) {
  background-color: transparent !important;
  border-color: #4c5155 !important;
}

.interface-table :deep(.arco-table-td) {
  background-color: transparent !important;
  border-color: #4c5155 !important;
}

.interface-table :deep(.arco-table-tr) {
  background-color: transparent !important;
}

.interface-table :deep(.arco-table-tr:hover) {
  background-color: rgba(255, 255, 255, 0.04) !important;
}

.interface-table :deep(.arco-table-tr-checked) {
  background-color: rgba(22, 93, 255, 0.1) !important;
}

.hide-scrollbar {
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none;  /* IE and Edge */
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;  /* Chrome, Safari and Opera */
}
</style>