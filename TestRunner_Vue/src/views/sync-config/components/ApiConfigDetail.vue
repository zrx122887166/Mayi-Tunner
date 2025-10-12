<script setup lang="ts">
import { computed } from 'vue'
import type { ApiSyncConfig } from '@/api/sync'

const props = defineProps<{
  visible: boolean
  config: ApiSyncConfig | null
  fieldOptions: { label: string; value: string }[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

const handleClose = () => {
  emit('update:visible', false)
}
</script>

<template>
  <a-modal
    :visible="visible"
    title="同步配置详情"
    :width="780"
    class="custom-card detail-modal"
    @ok="handleClose"
    @cancel="handleClose"
    @close="handleClose"
  >
    <div class="tw-bg-gray-900/50 tw-p-4 tw-rounded-lg tw-mb-6">
      <div class="tw-grid tw-grid-cols-2 tw-gap-8">
        <div>
          <div class="tw-text-gray-300 tw-text-base tw-font-medium tw-mb-4">基本信息</div>
          <div class="tw-space-y-4">
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.5rem]">接口名称：</span>
              <span class="tw-text-gray-200">{{ config?.interface_info?.name }}</span>
            </div>
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.5rem]">用例名称：</span>
              <span class="tw-text-gray-200">{{ config?.testcase_info?.name }}</span>
            </div>
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.5rem]">步骤名称：</span>
              <span class="tw-text-gray-200">{{ config?.step_info?.name }}</span>
            </div>
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[3.75rem]">创建者：</span>
              <span class="tw-text-gray-200">{{ config?.created_by_info?.username || '-' }}</span>
            </div>
          </div>
        </div>

        <div>
          <div class="tw-text-gray-300 tw-text-base tw-font-medium tw-mb-4">状态信息</div>
          <div class="tw-space-y-4">
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.5rem]">同步模式：</span>
              <a-tag color="arcoblue" size="medium" class="tw-rounded-md">
                {{ config?.sync_mode === 'auto' ? '自动同步' : '手动同步' }}
              </a-tag>
            </div>
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.5rem]">同步状态：</span>
              <a-tag :color="config?.sync_enabled ? 'green' : 'red'" size="medium" class="tw-rounded-md">
                {{ config?.sync_enabled ? '已启用' : '已禁用' }}
              </a-tag>
            </div>
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.25rem]">创建时间：</span>
              <span class="tw-text-gray-200">{{ config?.created_time ? new Date(config.created_time).toLocaleString() : '-' }}</span>
            </div>
            <div class="tw-flex tw-items-center tw-gap-3">
              <span class="tw-text-gray-400 tw-w-[4.25rem]">更新时间：</span>
              <span class="tw-text-gray-200">{{ config?.updated_time ? new Date(config.updated_time).toLocaleString() : '-' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template v-if="config">
      <div class="tw-space-y-6">
        <div class="tw-bg-gray-900/50 tw-p-4 tw-rounded-lg">
          <div class="tw-text-gray-300 tw-text-base tw-font-medium tw-mb-4">同步字段</div>
          <div class="tw-flex tw-flex-wrap tw-gap-2">
            <template v-for="field in config.sync_fields" :key="field">
              <a-tag color="arcoblue" size="medium" class="tw-rounded-md">
                {{ fieldOptions.find(opt => opt.value === field)?.label || field }}
              </a-tag>
            </template>
          </div>
        </div>

        <div v-if="config.sync_mode === 'auto'" class="tw-bg-gray-900/50 tw-p-4 tw-rounded-lg">
          <div class="tw-text-gray-300 tw-text-base tw-font-medium tw-mb-4">监视字段</div>
          <div class="tw-flex tw-flex-wrap tw-gap-2">
            <template v-for="field in config.sync_trigger?.fields_to_watch" :key="field">
              <a-tag color="arcoblue" size="medium" class="tw-rounded-md">
                {{ fieldOptions.find(opt => opt.value === field)?.label || field }}
              </a-tag>
            </template>
          </div>
        </div>
      </div>
    </template>
  </a-modal>
</template>

<style scoped>
:deep(.arco-modal) {
  @apply tw-bg-gray-800;
}

:deep(.arco-modal-header) {
  @apply tw-bg-gray-800 tw-border-gray-700 tw-pb-4;
}

:deep(.arco-modal-title) {
  @apply tw-text-gray-200 tw-text-lg tw-font-medium;
}

:deep(.arco-modal-footer) {
  @apply tw-bg-gray-800 tw-border-gray-700 tw-mt-6;
}

:deep(.detail-modal .arco-modal-body) {
  @apply tw-p-6;
}
</style> 