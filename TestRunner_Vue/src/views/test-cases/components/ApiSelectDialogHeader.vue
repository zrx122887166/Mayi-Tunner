<script setup lang="ts">
import { IconClose } from '@arco-design/web-vue/es/icon'

defineEmits(['close'])
</script>

<template>
  <div class="tw-bg-gray-800 tw-rounded-lg tw-border tw-border-gray-700 tw-px-4 tw-py-3 tw-flex tw-justify-between tw-items-center">
    <span class="tw-text-[#e5e6e8] tw-font-medium">添加接口</span>
    <a-button class="!tw-bg-transparent !tw-border-0 !tw-p-0 hover:!tw-bg-gray-600/50" @click="$emit('close')">
      <template #icon>
        <icon-close />
      </template>
    </a-button>
  </div>
</template>