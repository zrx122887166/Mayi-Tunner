<script setup lang="ts">
import { ref, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconCode } from '@arco-design/web-vue/es/icon'
import type { StepVariable } from '@/types/testcase'

interface Props {
  modelValue: StepVariable[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const stepVariables = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const stepVariableModalVisible = ref(false)

const handleCopyVariable = async (key: string) => {
  try {
    const text = '${' + key + '}'
    await navigator.clipboard.writeText(text)
    Message.success('已复制到剪贴板')
  } catch (err) {
    console.error('Copy failed:', err)
    Message.error('复制失败')
  }
}
</script>

<template>
  <div class="tw-flex tw-items-center tw-gap-2">
    <a-button
      class="!tw-flex !tw-items-center !tw-gap-1"
      type="outline"
      size="small"
      @click="() => stepVariableModalVisible = true"
      status="normal"
    >
      <template #icon>
        <icon-code class="!tw-text-[#165DFF]" />
      </template>
      <span class="!tw-text-[#165DFF]">步骤变量</span>
      <span class="tw-inline-flex tw-items-center tw-justify-center tw-bg-[#165DFF] tw-text-white tw-rounded tw-text-xs tw-min-w-[16px] tw-h-4 tw-px-1">
        {{ stepVariables.length }}
      </span>
    </a-button>

    <!-- 步骤变量弹窗 -->
    <a-modal
      v-model:visible="stepVariableModalVisible"
      :width="800"
      title="步骤变量"
      :mask-style="{ backgroundColor: 'rgba(0, 0, 0, 0.65)' }"
    >
      <div class="tw-space-y-4">
        <!-- 步骤变量表格 -->
        <a-table :data="stepVariables" :pagination="false" :bordered="false">
          <template #columns>
            <a-table-column title="变量名" data-index="key" :width="250">
              <template #cell="{ record }">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <span class="tw-font-mono tw-text-[#165DFF]">$</span>
                  <span class="tw-font-mono">{{ record.key }}</span>
                  <a-button
                    type="text"
                    size="mini"
                    class="!tw-p-1"
                    @click="() => handleCopyVariable(record.key)"
                  >
                    复制
                  </a-button>
                </div>
              </template>
            </a-table-column>
            <a-table-column title="值" data-index="value">
              <template #cell="{ record }">
                <span class="tw-font-mono">{{ record.value }}</span>
              </template>
            </a-table-column>
            <a-table-column title="来源" data-index="from" :width="150">
              <template #cell="{ record }">
                <span class="tw-text-gray-400">{{ record.from }}</span>
              </template>
            </a-table-column>
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template> 