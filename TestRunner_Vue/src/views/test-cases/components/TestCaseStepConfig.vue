<script setup lang="ts">
import type { TestCaseStep } from '@/api/testcase'
import ApiHeadersConfig from '@/views/apis/components/ApiHeadersConfig.vue'
import ApiParamsConfig from '@/views/apis/components/ApiParamsConfig.vue'
import ApiBodyConfig from '@/views/apis/components/ApiBodyConfig.vue'
import ApiSetupHooksConfig from '@/views/apis/components/ApiSetupHooksConfig.vue'
import ApiTeardownHooksConfig from '@/views/apis/components/ApiTeardownHooksConfig.vue'
import ApiExtractConfig from '@/views/apis/components/ApiExtractConfig.vue'
import ApiAssertConfig from '@/views/apis/components/ApiAssertConfig.vue'
import { ref, watch } from 'vue'

interface Props {
  modelValue: TestCaseStep
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits(['update:modelValue'])

// 组件引用
const headersRef = ref()
const paramsRef = ref()
const bodyRef = ref()
const setupHooksRef = ref()
const teardownHooksRef = ref()
const extractRef = ref()
const assertRef = ref()

// 当前选中的配置tab
const activeTab = ref('headers')

// 添加调试代码
watch(() => props.modelValue, (newValue) => {
  console.log('步骤配置接收到的数据:', {
    headers: newValue.interface_data.headers,
    params: newValue.interface_data.params,
    body: newValue.interface_data.body
  })
}, { immediate: true, deep: true })

// 更新接口数据
const updateInterfaceData = (key: keyof TestCaseStep['interface_data'], value: any) => {
  console.log('更新接口数据:', { key, value })
  const updatedStep = {
    ...props.modelValue,
    interface_data: {
      ...props.modelValue.interface_data,
      [key]: value
    }
  }
  console.log('更新后的步骤数据:', updatedStep)
  emit('update:modelValue', updatedStep)
}

// 更新配置数据
const updateConfig = (key: keyof TestCaseStep['config'], value: any) => {
  console.log('更新配置数据:', { key, value })
  const updatedStep = {
    ...props.modelValue,
    config: {
      ...props.modelValue.config,
      [key]: value
    }
  }
  console.log('更新后的步骤数据:', updatedStep)
  emit('update:modelValue', updatedStep)
}

// 暴露组件引用给父组件
defineExpose({
  headersRef,
  paramsRef,
  bodyRef,
  setupHooksRef,
  teardownHooksRef,
  extractRef,
  assertRef
})
</script>

<template>
  <div class="tw-flex-1 tw-min-h-0 tw-bg-gray-900/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden">
    <a-tabs v-model:active-key="activeTab" class="tw-h-full">
      <!-- Headers配置 -->
      <a-tab-pane key="headers" title="Headers">
        <div class="tw-p-4">
          <api-headers-config
            ref="headersRef"
            :model-value="modelValue.interface_data.headers"
            @update:model-value="val => updateInterfaceData('headers', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>

      <!-- 参数配置 -->
      <a-tab-pane key="params" title="Params">
        <div class="tw-p-4">
          <api-params-config
            ref="paramsRef"
            :model-value="modelValue.interface_data.params"
            @update:model-value="val => updateInterfaceData('params', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>

      <!-- Body配置 -->
      <a-tab-pane key="body" title="Body">
        <div class="tw-p-4">
          <api-body-config
            ref="bodyRef"
            :model-value="modelValue.interface_data.body"
            @update:model-value="val => updateInterfaceData('body', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>

      <!-- Setup Hooks配置 -->
      <a-tab-pane key="setup_hooks" title="Setup Hooks">
        <div class="tw-p-4">
          <api-setup-hooks-config
            ref="setupHooksRef"
            :model-value="modelValue.config.setup_hooks"
            @update:model-value="val => updateConfig('setup_hooks', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>

      <!-- Teardown Hooks配置 -->
      <a-tab-pane key="teardown_hooks" title="Teardown Hooks">
        <div class="tw-p-4">
          <api-teardown-hooks-config
            ref="teardownHooksRef"
            :model-value="modelValue.config.teardown_hooks"
            @update:model-value="val => updateConfig('teardown_hooks', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>

      <!-- Extract配置 -->
      <a-tab-pane key="extract" title="Extract">
        <div class="tw-p-4">
          <api-extract-config
            ref="extractRef"
            :model-value="modelValue.config.extract"
            @update:model-value="val => updateConfig('extract', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>

      <!-- Assert配置 -->
      <a-tab-pane key="assert" title="Assert">
        <div class="tw-p-4">
          <api-assert-config
            ref="assertRef"
            :model-value="modelValue.config.validators"
            @update:model-value="val => updateConfig('validators', val)"
            :readonly="readonly"
          />
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-tabs) {
  @apply tw-h-full;
}

:deep(.arco-tabs-content) {
  @apply tw-flex-1 tw-min-h-0;
}

:deep(.arco-tabs-content-list) {
  @apply tw-h-full;
}

:deep(.arco-tabs-pane) {
  @apply tw-h-full tw-overflow-y-auto;
}

:deep(.arco-tabs-nav) {
  @apply tw-bg-gray-900/60 tw-border-b tw-border-gray-700;
}

:deep(.arco-tabs-nav-tab) {
  @apply tw-border-0;
}

:deep(.arco-tabs-nav-tab-list) {
  @apply tw-px-4;
}

:deep(.arco-tabs-tab) {
  @apply tw-text-gray-400 tw-border-0;

  &:hover {
    @apply tw-text-blue-400;
  }

  &.arco-tabs-tab-active {
    @apply tw-text-blue-500;
  }
}

:deep(.arco-tabs-nav-ink) {
  @apply tw-bg-blue-500;
}
</style> 