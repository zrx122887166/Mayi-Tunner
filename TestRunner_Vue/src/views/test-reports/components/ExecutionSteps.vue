<template>
  <!-- 执行步骤主容器 - 包含所有测试步骤的垂直列表 -->
  <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-rounded-lg tw-border tw-border-gray-700/30">
    <!-- 标题栏 -->
    <div class="tw-px-4 tw-py-3 tw-border-b tw-border-gray-700/30">
      <span class="tw-text-gray-300 tw-text-base tw-font-medium">执行步骤</span>
    </div>
    <!-- 步骤列表容器 -->
    <div class="tw-p-4">
      <!-- Arco Design垂直步骤组件 - 显示所有测试步骤 -->
      <a-steps :current="report?.details?.length" direction="vertical">
        <!-- 单个测试步骤容器 - 循环渲染每个测试步骤 -->
        <a-step
          v-for="(step, index) in report?.details"
          :key="step.id"
          :title="step.step_name"
          :status="getStepStatus(step.success)"
          class="step-item"
        >
          <!-- 步骤描述插槽 - 包含步骤的详细信息 -->
          <template #description>
            <!-- 步骤状态概览行 - 显示成功/失败状态、请求方法、状态码等 -->
            <div class="tw-flex tw-items-start tw-justify-between tw-mt-2" :class="{'last-step-status': index === (report?.details?.length ?? 0) - 1}">
              <!-- 左侧信息组 - 状态标签、请求方法、状态码、响应时间 -->
              <div class="tw-flex tw-items-center tw-gap-4">
                <!-- 状态标签 -->
                <a-tag size="small" :color="step.success ? 'green' : 'red'">
                  {{ step.success ? '成功' : '失败' }}
                </a-tag>

                <!-- 请求方法和状态码 -->
                <div v-if="step.request && step.response" class="tw-flex tw-items-center tw-gap-2">
                  <span class="tw-text-blue-400 tw-text-sm">{{ step.request.method }}</span>
                  <a-tag :color="getResponseStatusColor(step.response.status_code)" size="small">
                    {{ step.response.status_code }}
                  </a-tag>
                </div>

                <!-- 响应时间 -->
                <div v-if="step.response" class="tw-flex tw-items-center tw-gap-2">
                  <icon-clock-circle class="tw-text-gray-400" />
                  <span class="tw-text-gray-400 tw-text-sm">{{ step.response.response_time_ms }}ms</span>
                </div>
              </div>

              <!-- 右侧验证器统计 - 显示通过的验证器数量 -->
              <div v-if="step.validators?.validate_extractor?.length" class="tw-flex tw-items-center tw-gap-2 tw-min-w-[60px] tw-mr-2 tw-pr-8 tw-justify-end">
                <icon-check-circle class="tw-text-yellow-400 tw-flex-shrink-0" />
                <span class="tw-text-gray-400 tw-text-sm tw-whitespace-nowrap">
                  {{ getValidatorStats(step.validators.validate_extractor).pass }}/{{ step.validators.validate_extractor.length }}
                </span>
              </div>
            </div>

            <!-- 详细信息网格 - 包含请求、响应、断言和变量等四个卡片，使用4列网格布局 -->
            <div class="tw-mt-4 tw-grid tw-grid-cols-4 tw-gap-4 tw-w-[calc(100%-72px)]">
              <!-- 请求信息卡片 (网格第1列) - 显示HTTP请求详情 -->
              <div v-if="step.request" class="step-info-card">
                <!-- 卡片标题栏 -->
                <div class="tw-bg-blue-500/5 tw-px-3 tw-py-1.5 tw-border-b tw-border-gray-700/30">
                  <div class="tw-flex tw-items-center tw-justify-between">
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <span class="tw-text-blue-400 tw-text-sm">请求信息</span>
                      <a-tag size="small">{{ step.request.method }}</a-tag>
                    </div>
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <a-button type="text" size="mini" @click="copyToClipboard(JSON.stringify(step.request, null, 2))">
                        <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-blue-400" /></template>
                      </a-button>
                      <a-button type="text" size="mini" @click="toggleDrawer(step.id, 'request')">
                        <template #icon><icon-expand class="tw-text-gray-400 hover:tw-text-blue-400" /></template>
                      </a-button>
                    </div>
                  </div>
                </div>
                <div class="tw-p-2">
                  <!-- 请求信息容器 - 用于显示请求的JSON数据 -->
                  <pre class="tw-bg-gray-800/30 tw-p-2 tw-rounded tw-text-xs tw-font-mono tw-text-gray-300 tw-overflow-x-auto tw-border tw-border-gray-700/30 tw-max-h-[120px] tw-whitespace-pre-wrap tw-break-all card-content">{{ JSON.stringify(step.request, null, 2) }}</pre>
                </div>
              </div>

              <!-- 响应信息卡片 (网格第2列) - 显示HTTP响应详情 -->
              <div v-if="step.response" class="step-info-card">
                <!-- 卡片标题栏 -->
                <div class="tw-bg-purple-500/5 tw-px-3 tw-py-1.5 tw-border-b tw-border-gray-700/30">
                  <div class="tw-flex tw-items-center tw-justify-between">
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <span class="tw-text-purple-400 tw-text-sm">响应信息</span>
                      <a-tag size="small" :color="getResponseStatusColor(step.response.status_code)">
                        {{ step.response.status_code }}
                      </a-tag>
                    </div>
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <a-button type="text" size="mini" @click="copyToClipboard(JSON.stringify(step.response, null, 2))">
                        <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-purple-400" /></template>
                      </a-button>
                      <a-button type="text" size="mini" @click="toggleDrawer(step.id, 'response')">
                        <template #icon><icon-expand class="tw-text-gray-400 hover:tw-text-purple-400" /></template>
                      </a-button>
                    </div>
                  </div>
                </div>
                <div class="tw-p-2">
                  <!-- 响应信息容器 - 用于显示响应的JSON数据 -->
                  <pre class="tw-bg-gray-800/30 tw-p-2 tw-rounded tw-text-xs tw-font-mono tw-text-gray-300 tw-overflow-x-auto tw-border tw-border-gray-700/30 tw-max-h-[120px] tw-whitespace-pre-wrap tw-break-all card-content">{{ JSON.stringify(step.response, null, 2) }}</pre>
                </div>
              </div>

              <!-- 断言结果卡片 (网格第3列) - 显示验证结果 -->
              <div v-if="step.validators?.validate_extractor?.length" class="step-info-card">
                <!-- 卡片标题栏 -->
                <div class="tw-bg-yellow-500/5 tw-px-3 tw-py-1.5 tw-border-b tw-border-gray-700/30">
                  <div class="tw-flex tw-items-center tw-justify-between">
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <span class="tw-text-yellow-400 tw-text-sm">断言结果</span>
                    </div>
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <a-button type="text" size="mini" @click="copyToClipboard(JSON.stringify(step.validators.validate_extractor, null, 2))">
                        <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-yellow-400" /></template>
                      </a-button>
                      <a-button type="text" size="mini" @click="toggleDrawer(step.id, 'validators')">
                        <template #icon><icon-expand class="tw-text-gray-400 hover:tw-text-yellow-400" /></template>
                      </a-button>
                    </div>
                  </div>
                </div>
                <div class="tw-p-2 tw-max-h-[120px] tw-overflow-y-auto card-content">
                  <!-- 断言结果容器 - 用于显示验证器的结果列表 -->
                  <div class="tw-space-y-2">
                    <div 
                      v-for="(validator, vIndex) in step.validators.validate_extractor" 
                      :key="vIndex"
                      class="validator-item tw-p-2"
                    >
                      <div class="tw-flex tw-items-start tw-gap-1.5">
                        <icon-check-circle-fill 
                          v-if="validator.check_result === 'pass'"
                          class="tw-text-green-500 tw-mt-0.5 tw-text-sm"
                        />
                        <icon-close-circle-fill
                          v-else
                          class="tw-text-red-500 tw-mt-0.5 tw-text-sm"
                        />
                        <div class="tw-flex-1">
                          <div class="tw-flex tw-items-center tw-gap-1">
                            <span class="tw-text-gray-300 tw-text-xs">{{ validator.check }}</span>
                            <span class="tw-text-gray-500 tw-text-xs">({{ validator.comparator }})</span>
                          </div>
                          <div class="tw-mt-1 tw-space-y-1">
                            <div class="validator-value">
                              <span class="tw-text-gray-400 tw-text-xs">期望值:</span>
                              <span class="tw-text-blue-400 tw-text-xs tw-font-mono">{{ validator.expect_value }}</span>
                            </div>
                            <div class="validator-value">
                              <span class="tw-text-gray-400 tw-text-xs">实际值:</span>
                              <span class="tw-text-purple-400 tw-text-xs tw-font-mono">{{ validator.check_value }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 提取变量卡片 (网格第4列) - 显示从响应中提取的变量 -->
              <div v-if="step.extracted_variables && Object.keys(step.extracted_variables).length" class="step-info-card">
                <!-- 卡片标题栏 -->
                <div class="tw-bg-green-500/5 tw-px-3 tw-py-1.5 tw-border-b tw-border-gray-700/30">
                  <div class="tw-flex tw-items-center tw-justify-between">
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <span class="tw-text-green-400 tw-text-sm">提取变量</span>
                      <a-tag size="small" color="green">{{ Object.keys(step.extracted_variables).length }}个</a-tag>
                    </div>
                    <div class="tw-flex tw-items-center tw-gap-2">
                      <a-button type="text" size="mini" @click="copyToClipboard(JSON.stringify(step.extracted_variables, null, 2))">
                        <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-green-400" /></template>
                      </a-button>
                      <a-button type="text" size="mini" @click="toggleDrawer(step.id, 'variables')">
                        <template #icon><icon-expand class="tw-text-gray-400 hover:tw-text-green-400" /></template>
                      </a-button>
                    </div>
                  </div>
                </div>
                <div class="tw-p-2">
                  <!-- 提取变量容器 - 用于显示从响应中提取的变量 -->
                  <div class="tw-space-y-2 tw-max-h-[120px] tw-overflow-y-auto card-content">
                    <div v-for="(value, key) in step.extracted_variables" :key="key" class="tw-bg-gray-800/30 tw-rounded tw-p-2 tw-border tw-border-gray-700/30 hover:tw-bg-gray-800/50 hover:tw-border-gray-600/50 tw-transition-all tw-duration-200">
                      <div class="tw-flex tw-items-center tw-justify-between">
                        <span class="tw-text-gray-300 tw-text-xs">{{ key }}</span>
                        <a-button type="text" size="mini" @click="copyToClipboard(value)">
                          <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-green-400" /></template>
                        </a-button>
                      </div>
                      <div class="tw-mt-1 tw-bg-gray-900/30 tw-rounded tw-px-2 tw-py-1 tw-border tw-border-gray-700/30">
                        <span class="tw-text-green-400 tw-text-xs tw-font-mono tw-break-all">{{ value }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </a-step>
      </a-steps>
    </div>
  </div>

  <!-- 抽屉组件 - 用于显示完整的请求或响应详情 -->
  <a-drawer
    :visible="drawerVisible"
    :width="800"
    @cancel="drawerVisible = false"
    :title="currentDrawerType === 'request' ? '请求详情' : currentDrawerType === 'response' ? '响应详情' : currentDrawerType === 'validators' ? '验证器详情' : '变量详情'"
    :footer="false"
    class="custom-drawer"
    :mask="true"
    :mask-style="{ backgroundColor: 'transparent' }"
    :mask-closable="true"
    @close="drawerVisible = false"
  >
    <div class="tw-p-6">
      <!-- 根据不同的抽屉类型显示不同的内容 -->
      <template v-if="currentDrawerType === 'validators'">
        <div class="tw-space-y-3">
          <div 
            v-for="(validator, vIndex) in currentDrawerData" 
            :key="vIndex"
            class="validator-item tw-p-3"
          >
            <div class="tw-flex tw-items-start tw-gap-2">
              <icon-check-circle-fill 
                v-if="validator.check_result === 'pass'"
                class="tw-text-green-500 tw-mt-0.5"
              />
              <icon-close-circle-fill
                v-else
                class="tw-text-red-500 tw-mt-0.5"
              />
              <div class="tw-flex-1">
                <div class="tw-flex tw-items-center tw-gap-1">
                  <span class="tw-text-gray-300">{{ validator.check }}</span>
                  <span class="tw-text-gray-500">({{ validator.comparator }})</span>
                </div>
                <div class="tw-mt-2 tw-space-y-2">
                  <div class="validator-value">
                    <span class="tw-text-gray-400">期望值:</span>
                    <span class="tw-text-blue-400 tw-font-mono">{{ validator.expect_value }}</span>
                  </div>
                  <div class="validator-value">
                    <span class="tw-text-gray-400">实际值:</span>
                    <span class="tw-text-purple-400 tw-font-mono">{{ validator.check_value }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
      <template v-else-if="currentDrawerType === 'variables'">
        <div class="tw-space-y-3">
          <div v-for="(value, key) in currentDrawerData" :key="key" class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30 hover:tw-bg-gray-800/50 hover:tw-border-gray-600/50 tw-transition-all tw-duration-200">
            <div class="tw-flex tw-items-start tw-justify-between">
              <div class="tw-flex tw-items-center tw-gap-2">
                <icon-code class="tw-text-green-400" />
                <span class="tw-text-gray-300 tw-font-medium">{{ key }}</span>
              </div>
              <a-button type="text" size="mini" @click="copyToClipboard(value)">
                <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-green-400" /></template>
              </a-button>
            </div>
            <div class="tw-mt-2 tw-bg-gray-900/50 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
              <div class="tw-text-green-400 tw-font-mono tw-break-all">{{ value }}</div>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <pre class="tw-bg-gray-900/80 tw-backdrop-blur-sm tw-rounded-lg tw-p-4 tw-text-sm tw-font-mono tw-text-gray-300 tw-whitespace-pre-wrap tw-break-all tw-border tw-border-gray-700/30">{{ JSON.stringify(currentDrawerData, null, 2) }}</pre>
      </template>
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { 
  IconCheckCircleFill, 
  IconCloseCircleFill, 
  IconUp, 
  IconDown,
  IconClockCircle,
  IconCheckCircle,
  IconCopy,
  IconExpand,
  IconCode
} from '@arco-design/web-vue/es/icon'
import { formatDuration } from '@/utils/format'
import type { TestReportResponse } from '../detail.vue'

// 组件属性定义 - 接收测试报告数据
const props = defineProps<{
  report: TestReportResponse | null
}>()

// 跟踪展开的步骤ID列表
const expandedSteps = ref<number[]>([])

/**
 * 切换步骤的展开/折叠状态
 * @param index 步骤索引
 */
const toggleStep = (index: number) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx > -1) {
    expandedSteps.value.splice(idx, 1)
  } else {
    expandedSteps.value.push(index)
  }
}

/**
 * 根据步骤成功状态获取Arco Design步骤组件的状态
 * @param success 步骤是否成功
 * @returns Arco Design步骤状态
 */
const getStepStatus = (success: boolean) => {
  return success ? 'finish' : 'error'
}

/**
 * 根据HTTP状态码获取对应的颜色
 * @param status HTTP状态码
 * @returns 颜色名称
 */
const getResponseStatusColor = (status: number) => {
  if (status >= 500) return 'red'
  if (status >= 400) return 'orange'
  if (status >= 300) return 'blue'
  return 'green'
}

/**
 * 计算验证器的统计信息
 * @param validators 验证器数组
 * @returns 包含通过数量的对象
 */
const getValidatorStats = (validators: Array<{ check_result: 'pass' | 'fail' }>) => {
  const pass = validators.filter(v => v.check_result === 'pass').length
  return { pass }
}

/**
 * 将文本复制到剪贴板
 * @param text 要复制的文本
 */
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    Message.success('复制成功')
  } catch (err) {
    Message.error('复制失败')
  }
}

// 抽屉组件状态控制
const drawerVisible = ref(false)
const currentDrawerData = ref<any>(null)
const currentDrawerType = ref<'request' | 'response' | 'validators' | 'variables' | null>(null)

/**
 * 切换抽屉的显示状态，并设置要显示的数据
 * @param stepId 步骤ID
 * @param type 数据类型（请求、响应、验证器或变量）
 */
const toggleDrawer = (stepId: number, type: 'request' | 'response' | 'validators' | 'variables') => {
  const step = props.report?.details?.find((s: { id: number }) => s.id === stepId)
  if (step) {
    if (type === 'request') {
      currentDrawerData.value = step.request
    } else if (type === 'response') {
      currentDrawerData.value = step.response
    } else if (type === 'validators') {
      currentDrawerData.value = step.validators?.validate_extractor || []
    } else if (type === 'variables') {
      currentDrawerData.value = step.extracted_variables || {}
    }
    currentDrawerType.value = type
    drawerVisible.value = true
  }
}
</script>

<style scoped>
/* 覆盖Arco Design步骤组件的默认样式 */
:deep(.arco-steps) {
  .arco-step-content {
    @apply !tw-min-h-0;
  }

  .arco-step-title {
    @apply !tw-text-gray-300 !tw-text-base !tw-font-medium;
  }

  .arco-step-description {
    @apply !tw-text-gray-400 !tw-mt-2;
  }
}

/* 覆盖Arco Design折叠面板的默认样式 */
:deep(.arco-collapse) {
  @apply !tw-bg-transparent !tw-border-none;

  .arco-collapse-item {
    @apply !tw-border-none;

    .arco-collapse-item-header {
      @apply !tw-bg-transparent !tw-text-gray-400 !tw-border-none !tw-p-0;

      &:hover {
        @apply !tw-text-gray-300;
      }
    }

    .arco-collapse-item-content {
      @apply !tw-bg-transparent !tw-text-gray-300 !tw-p-0 !tw-mt-2;
    }
  }
}

/* 卡片内容区域的滚动样式 - 隐藏滚动条但保留滚动功能 */
.card-content {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  &::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera */
  }
}

/* 步骤状态栏样式 - 显示步骤的基本状态信息 */
.step-status-bar {
  @apply tw-flex tw-items-center tw-justify-between tw-bg-gray-800/30 tw-rounded-lg tw-px-3 tw-py-2 tw-border tw-border-gray-700/30 tw-transition-all tw-duration-200;

  &:hover {
    @apply tw-bg-gray-800/50 tw-border-gray-600/50;
  }
}

/* 步骤信息卡片样式 - 用于请求、响应、断言和变量等四个卡片 */
.step-info-card {
  @apply tw-bg-gray-800/30 tw-rounded-lg tw-overflow-hidden tw-border tw-border-gray-700/30 tw-transition-all tw-duration-200;

  &:hover {
    @apply tw-bg-gray-800/50 tw-border-gray-600/50;
  }
}

/* 验证器项目样式 - 断言结果中的每个验证项 */
.validator-item {
  @apply tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30 tw-transition-all tw-duration-200;

  &:hover {
    @apply tw-bg-gray-800/50 tw-border-gray-600/50;
  }
}

/* 验证器值样式 - 显示期望值和实际值的容器 */
.validator-value {
  @apply tw-flex tw-items-center tw-gap-2 tw-bg-gray-900/30 tw-rounded tw-px-2 tw-py-1 tw-border tw-border-gray-700/30;
}

/* 最后一个步骤的状态概览行样式 */
.last-step-status {
  /* 使用负边距抵消Arco Design步骤组件对最后一个步骤的特殊处理 */
  @apply tw-pr-8;
}

/* 自定义抽屉组件样式 - 用于显示完整的请求或响应详情 */
:deep(.custom-drawer) {
  .arco-drawer-container {
    @apply !tw-bg-transparent !important;
  }

  .arco-drawer-header {
    @apply !tw-bg-gray-900 !tw-border-b !tw-border-gray-700/30 !important;
    background-color: rgb(31, 41, 55) !important;
  }

  .arco-drawer-body {
    @apply !tw-bg-gray-900 !important;
    background-color: rgb(31, 41, 55) !important;
  }

  .arco-drawer-content {
    @apply !tw-bg-gray-900 !important;
    background-color: rgb(31, 41, 55) !important;
  }

  .arco-drawer-wrapper {
    @apply !tw-bg-gray-900 !important;
    background-color: rgb(31, 41, 55) !important;
  }
}

/* 全局样式覆盖 - 确保抽屉组件样式具有最高优先级 */
:global(.arco-drawer-container) {
  background-color: transparent !important;
}

:global(.arco-drawer-header),
:global(.arco-drawer-body),
:global(.arco-drawer-content),
:global(.arco-drawer-wrapper) {
  background-color: rgb(31, 41, 55) !important;
}
</style> 