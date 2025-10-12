<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message, Tag as ATag, Collapse as ACollapse, CollapseItem as ACollapseItem, 
         Progress as AProgress, Tooltip as ATooltip } from '@arco-design/web-vue'
import { IconExclamationCircleFill } from '@arco-design/web-vue/es/icon'
import { getTestTaskExecutionCaseResults } from '@/api/testtask'
import ApiDetailCard from './ApiDetailCard.vue'

interface ValidateExtractor {
  check: string
  expect: string
  message: string
  comparator: string
  check_value: string
  check_result: string
  expect_value: string
}

interface StepDetail {
  id: number
  step_name: string
  success: boolean
  elapsed: number
  request: {
    url: string
    method: string
    headers: Record<string, string>
    body?: any
  }
  response: {
    status_code: number
    headers: Record<string, string>
    body: any
    response_time_ms: number
  }
  validators: {
    success: boolean
    validate_extractor: ValidateExtractor[]
  }
  extracted_variables: Record<string, any>
  attachment: string
}

interface TestReport {
  id: number
  name: string
  status: string
  success_count: number
  fail_count: number
  error_count: number
  duration: number
  start_time: string
  summary: {
    success: boolean
    step_results: any[]
  }
  details: StepDetail[]
  success_rate: string
  environment_info: {
    name: string
    base_url: string
    project: {
      name: string
    }
  }
  executed_by_info: {
    username: string
  }
}

interface CaseResult {
  id: number
  testcase: number
  testcase_name: string
  status: string
  start_time: string
  end_time: string
  duration: number
  error_message: string
  report: TestReport
}

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const caseResults = ref<CaseResult[]>([])
const expandedStepIds = ref<Record<number, number[]>>({})

// 获取用例执行结果
const fetchCaseResults = async () => {
  const id = route.params.id
  if (!id) {
    Message.warning('未指定执行记录ID')
    return
  }

  loading.value = true
  try {
    const { data } = await getTestTaskExecutionCaseResults(Number(id))
    if (data) {
      caseResults.value = data
    }
  } catch (error) {
    console.error('获取用例执行结果失败', error)
    Message.error(error instanceof Error ? error.message : '获取用例执行结果失败')
  } finally {
    loading.value = false
  }
}

// 返回历史记录页面
const goBack = () => {
  console.log('返回按钮被点击');
  
  try {
    // 获取当前执行记录ID
    const executionId = Number(route.params.id);
    console.log('当前执行记录ID:', executionId);
    
    // 尝试使用动态导入，避免循环依赖
    import('@/api/testtask')
      .then(({ getTestTaskExecution }) => {
        // 添加超时处理，确保即使API请求超时也能返回
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('请求超时')), 5000);
        });
        
        // 使用Promise.race确保请求不会无限等待
        // 使用any类型避免类型错误
        const racePromise: Promise<any> = Promise.race([
          getTestTaskExecution(executionId),
          timeoutPromise
        ]);
        
        racePromise
          .then(response => {
            if (response && response.status === 'success' && response.data && response.data.task_suite) {
              const taskSuiteId = response.data.task_suite;
              console.log('获取到测试任务ID:', taskSuiteId);
              
              // 导航到测试任务执行历史页面
              router.push({
                name: 'testtask-history',
                params: { id: taskSuiteId }
              });
            } else {
              console.warn('无法获取有效的测试任务ID，返回测试任务列表');
              router.push({ name: 'testtasks' });
            }
          })
          .catch(error => {
            console.error('获取执行详情失败:', error);
            router.push({ name: 'testtasks' });
          });
      })
      .catch(error => {
        console.error('导入API模块失败:', error);
        router.push({ name: 'testtasks' });
      });
  } catch (error) {
    // 捕获所有可能的错误，确保返回按钮总是有效的
    console.error('返回操作发生错误:', error);
    router.push({ name: 'testtasks' });
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return '-'
    }
    return date.toLocaleString('zh-CN')
  } catch (error) {
    console.error('日期格式化错误:', error)
    return '-'
  }
}

// 格式化持续时间
const formatDuration = (seconds: number) => {
  if (seconds === undefined || seconds === null || isNaN(seconds)) return '-'
  try {
    return `${Number(seconds).toFixed(2)}秒`
  } catch (error) {
    console.error('持续时间格式化错误:', error)
    return '-'
  }
}

// 展开行渲染函数
const expandedRowRender = (record: any) => {
  // 如果 report 为 null，显示错误信息
  if (!record.report) {
    return h('div', { 
      class: 'tw-bg-gray-900/30 tw-rounded-lg tw-p-4 tw-mt-4' 
    }, [
      h('div', { class: 'tw-flex tw-items-center tw-gap-2' }, [
        h('span', { class: 'tw-text-red-400' }, '错误信息：'),
        h('span', { class: 'tw-text-red-300' }, record.error_message || '未知错误')
      ])
    ])
  }

  try {
    // 确保该记录在 expandedStepIds 中有对应的数组
    if (!expandedStepIds.value[record.id]) {
      expandedStepIds.value[record.id] = []
    }

    return h('div', { 
      class: 'tw-bg-gray-900/30 tw-rounded-lg tw-p-4 tw-mt-4' 
    }, [
      // 添加基本信息
      h('div', { class: 'tw-mb-4 tw-grid tw-grid-cols-2 tw-gap-4' }, [
        h('div', { class: 'tw-flex tw-items-center tw-gap-2' }, [
          h('span', { class: 'tw-text-gray-400' }, '报告名称：'),
          h('span', { class: 'tw-text-gray-200' }, record.report.name || '-')
        ]),
        h('div', { class: 'tw-flex tw-items-center tw-gap-2' }, [
          h('span', { class: 'tw-text-gray-400' }, '项目名称：'),
          h('span', { class: 'tw-text-gray-200' }, 
            record.report.environment_info?.project?.name || '-'
          )
        ])
      ]),
      // 步骤详情
      record.report.details && record.report.details.length > 0 ? 
        h(ACollapse, {
          class: 'custom-collapse',
          modelValue: expandedStepIds.value[record.id],
          'onUpdate:modelValue': (val: number[]) => {
            expandedStepIds.value[record.id] = val
          }
        }, () => record.report.details.map((detail: StepDetail) => 
          h(ACollapseItem, {
            key: detail.id,
            name: detail.id,
            header: detail.step_name,
          }, {
            default: () => [
              // 使用ApiDetailCard组件展示接口详情
              h(ApiDetailCard, {
                detail: detail
              })
            ],
            extra: () => h('div', { class: 'tw-flex tw-items-center tw-gap-4' }, [
              h(ATag, {
                color: detail.success ? 'green' : 'red'
              }, () => detail.success ? '成功' : '失败'),
              h('span', { class: 'tw-text-gray-400' }, formatDuration(detail.elapsed || 0))
            ])
          })
        ))
        : h('div', { class: 'tw-text-gray-400 tw-text-center tw-py-4' }, '暂无步骤详情')
    ])
  } catch (error) {
    console.error('展开行渲染函数发生错误:', error)
    return h('div', { 
      class: 'tw-bg-gray-900/30 tw-rounded-lg tw-p-4 tw-mt-4' 
    }, [
      h('div', { class: 'tw-flex tw-items-center tw-gap-2' }, [
        h('span', { class: 'tw-text-red-400' }, '错误信息：'),
        h('span', { class: 'tw-text-red-300' }, record.error_message || '未知错误')
      ])
    ])
  }
}

onMounted(() => {
  fetchCaseResults()
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 标题区域 -->
    <div class="tw-bg-gray-800/85 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5 tw-flex tw-justify-between tw-items-center">
      <div class="tw-flex tw-items-center tw-gap-2">
        <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">
          测试任务执行结果
        </h2>
        <a-tag v-if="route.params.id" color="blue">ID: {{ route.params.id }}</a-tag>
      </div>
      <a-button type="outline" @click="goBack">返回</a-button>
    </div>

    <!-- 内容区域 -->
    <div class="tw-flex-1 tw-bg-gray-800/85 tw-rounded-lg tw-shadow-dark tw-overflow-hidden">
      <a-spin :loading="loading" class="!tw-block tw-h-full">
        <div class="tw-h-full tw-overflow-auto">
          <template v-if="caseResults.length > 0">
            <!-- 汇总信息卡片 -->
            <div class="tw-p-6 tw-border-b tw-border-gray-700/50">
              <div class="tw-bg-gray-900/30 tw-rounded-lg tw-p-6">
                <h3 class="tw-text-lg tw-font-medium tw-text-gray-200 tw-mb-4">执行概况</h3>
                <div class="tw-grid tw-grid-cols-4 tw-gap-6">
                  <!-- 总用例数 -->
                  <div class="tw-bg-gray-800/50 tw-rounded-lg tw-p-4">
                    <div class="tw-flex tw-flex-col tw-items-center">
                      <span class="tw-text-gray-400 tw-text-sm">总用例数</span>
                      <span class="tw-text-gray-100 tw-text-2xl tw-font-semibold tw-mt-2">
                        {{ caseResults.length }}
                      </span>
                    </div>
                  </div>
                  <!-- 成功用例 -->
                  <div class="tw-bg-green-900/20 tw-rounded-lg tw-p-4">
                    <div class="tw-flex tw-flex-col tw-items-center">
                      <span class="tw-text-green-400 tw-text-sm">成功用例</span>
                      <span class="tw-text-green-300 tw-text-2xl tw-font-semibold tw-mt-2">
                        {{ caseResults.filter(r => r.status === 'success').length }}
                      </span>
                    </div>
                  </div>
                  <!-- 失败用例 -->
                  <div class="tw-bg-amber-900/20 tw-rounded-lg tw-p-4">
                    <div class="tw-flex tw-flex-col tw-items-center">
                      <span class="tw-text-amber-400 tw-text-sm">失败用例</span>
                      <span class="tw-text-amber-300 tw-text-2xl tw-font-semibold tw-mt-2">
                        {{ caseResults.filter(r => r.status === 'fail' || r.status === 'failure').length }}
                      </span>
                    </div>
                  </div>
                  <!-- 错误用例 -->
                  <div class="tw-bg-red-900/20 tw-rounded-lg tw-p-4">
                    <div class="tw-flex tw-flex-col tw-items-center">
                      <span class="tw-text-red-400 tw-text-sm">错误用例</span>
                      <span class="tw-text-red-300 tw-text-2xl tw-font-semibold tw-mt-2">
                        {{ caseResults.filter(r => r.status === 'error').length }}
                      </span>
                    </div>
                  </div>
                </div>
                <!-- 执行时间信息 -->
                <div class="tw-mt-4 tw-grid tw-grid-cols-2 tw-gap-4">
                  <div class="tw-flex tw-items-center tw-gap-2">
                    <span class="tw-text-gray-400">开始时间：</span>
                    <span class="tw-text-gray-200">{{ formatDate(caseResults[0]?.start_time || '') }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-gap-2">
                    <span class="tw-text-gray-400">总执行时长：</span>
                    <span class="tw-text-gray-200">{{ formatDuration(caseResults.reduce((sum, r) => sum + (r.duration || 0), 0)) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 用例列表 -->
            <div class="tw-p-6">
              <h3 class="tw-text-lg tw-font-medium tw-text-gray-200 tw-mb-4">用例详情</h3>
              <a-table 
                :data="caseResults" 
                :pagination="false" 
                :bordered="false"
                row-key="id"
                :expandable="{
                  expandedRowRender
                }"
                class="custom-table"
              >
                <template #columns>
                  <a-table-column 
                    title="ID" 
                    data-index="id"
                    :width="80"
                    align="center"
                  />
                  <a-table-column 
                    title="用例名称" 
                    data-index="testcase_name"
                    :width="250"
                    :sortable="{
                      sortDirections: ['ascend', 'descend']
                    }"
                  >
                    <template #cell="{ record }">
                      <div class="tw-flex tw-items-center tw-gap-2">
                        <span class="tw-text-gray-200">{{ record.testcase_name }}</span>
                        <a-tooltip v-if="record.error_message" position="right">
                          <template #content>
                            <span class="tw-text-red-300">{{ record.error_message }}</span>
                          </template>
                          <icon-exclamation-circle-fill class="tw-text-red-500" />
                        </a-tooltip>
                      </div>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="状态" 
                    align="center"
                    :width="100"
                    :sortable="{
                      sortDirections: ['ascend', 'descend']
                    }"
                    :sort-field="(record: any) => record.status"
                  >
                    <template #cell="{ record }">
                      <a-tag :color="record.status === 'success' ? 'green' : (record.status === 'fail' || record.status === 'failure') ? 'orange' : 'red'">
                        {{ record.status === 'success' ? '成功' : (record.status === 'fail' || record.status === 'failure') ? '失败' : '错误' }}
                      </a-tag>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="执行环境" 
                    :width="120"
                  >
                    <template #cell="{ record }">
                      <span class="tw-text-gray-400 tw-text-sm">{{ record.report?.environment_info?.name || '-' }}</span>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="执行人" 
                    :width="100"
                  >
                    <template #cell="{ record }">
                      <span class="tw-text-gray-400 tw-text-sm">{{ record.report?.executed_by_info?.username || '-' }}</span>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="执行时间" 
                    align="center"
                    :sortable="{
                      sortDirections: ['ascend', 'descend']
                    }"
                    :width="180"
                    :sort-field="(record: any) => new Date(record.start_time).getTime()"
                  >
                    <template #cell="{ record }">
                        <span class="tw-text-gray-400 tw-text-sm">{{ formatDate(record.start_time) }}</span>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="执行时长" 
                    align="center"
                    :sortable="{
                      sortDirections: ['ascend', 'descend']
                    }"
                    :width="100"
                    :sort-field="(record: any) => record.duration"
                  >
                    <template #cell="{ record }">
                        <span class="tw-text-gray-400 tw-text-sm">{{ formatDuration(record.duration) }}</span>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="步骤统计" 
                    align="center"
                    :width="250"
                    :sortable="{
                      sortDirections: ['ascend', 'descend']
                    }"
                    :sort-field="(record: any) => record.report?.success_count || 0"
                  >
                    <template #cell="{ record }">
                      <div class="tw-flex tw-items-center tw-gap-2 tw-justify-center">
                        <a-space v-if="record.report">
                          <a-tag color="green">成功: {{ record.report.success_count }}</a-tag>
                          <a-tag color="orange">失败: {{ record.report.fail_count }}</a-tag>
                          <a-tag color="red">错误: {{ record.report.error_count }}</a-tag>
                        </a-space>
                        <a-tag v-else color="red">数据异常</a-tag>
                      </div>
                    </template>
                  </a-table-column>
                  <a-table-column 
                    title="成功率" 
                    align="center"
                    :width="100"
                    :sortable="{
                      sortDirections: ['ascend', 'descend']
                    }"
                    :sort-field="(record: any) => Number(record.report?.success_rate || 0)"
                  >
                    <template #cell="{ record }">
                      <template v-if="record.report">
                        <a-progress
                          :percent="Number(record.report.success_rate || 0)"
                          :stroke-color="Number(record.report.success_rate || 0) === 1 ? '#00b42a' : '#ff7d00'"
                          :size="'small'"
                        />
                      </template>
                      <span v-else class="tw-text-gray-400 tw-text-sm">-</span>
                    </template>
                  </a-table-column>
                </template>
              </a-table>
            </div>
          </template>
          <div v-else class="tw-h-full tw-flex tw-items-center tw-justify-center">
            <div class="tw-text-gray-400 tw-text-lg">暂无执行结果数据</div>
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<style scoped lang="postcss">
/* 自定义滚动条 */
.custom-scrollbar {
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
  &::-webkit-scrollbar {
    display: none !important;
  }
}

:deep(.arco-collapse) {
  @apply !tw-bg-transparent !tw-border-none;
}

:deep(.arco-collapse-item) {
  @apply !tw-bg-gray-900/30 !tw-rounded-lg !tw-mb-4 !tw-border-none;
}

:deep(.arco-collapse-item-header) {
  @apply !tw-bg-transparent !tw-border-b !tw-border-gray-700/50;
}

:deep(.arco-collapse-item-content) {
  @apply !tw-bg-transparent !tw-text-gray-300;
}

:deep(.arco-tabs) {
  @apply !tw-text-gray-300;
}

:deep(.arco-tabs-nav) {
  @apply !tw-border-gray-700/50;
}

:deep(.arco-tabs-nav-tab) {
  @apply !tw-border-none;
}

:deep(.arco-tabs-nav-tab-list) {
  @apply !tw-border-none;
}

:deep(.arco-tabs-tab) {
  @apply !tw-text-gray-400;
}

:deep(.arco-tabs-tab-active) {
  @apply !tw-text-blue-400;
}

:deep(.arco-tabs-content) {
  @apply !tw-border-none;
}

pre {
  @apply !tw-bg-gray-800/50 !tw-rounded !tw-p-2 !tw-overflow-auto;
  max-height: 300px;
}

/* 优化表格样式 */
:deep(.custom-table) {
  @apply !tw-bg-transparent;
}

:deep(.custom-table .arco-table-th) {
  @apply !tw-bg-gray-800/50 !tw-text-gray-300 !tw-border-gray-700/50 !tw-font-medium;
}

:deep(.custom-table .arco-table-td) {
  @apply !tw-bg-transparent !tw-text-gray-300 !tw-border-gray-700/50;
}

:deep(.custom-table .arco-table-tr:hover .arco-table-td) {
  @apply !tw-bg-gray-800/30;
}

:deep(.custom-table .arco-table-tr-expand) {
  @apply !tw-bg-transparent;
}

:deep(.custom-table .arco-table-expand-content) {
  @apply !tw-bg-transparent !tw-border-none;
}

:deep(.custom-table .arco-table-expand-icon) {
  @apply !tw-text-gray-400;
}

:deep(.custom-table .arco-table-th-item-title) {
  @apply !tw-text-gray-300;
}

:deep(.custom-table .arco-table-sorter) {
  @apply !tw-text-gray-400;
}

:deep(.custom-table .arco-table-sorter-icon) {
  @apply !tw-text-gray-500;
}

:deep(.custom-table .arco-table-sorter-icon.active) {
  @apply !tw-text-blue-400;
}

/* 进度条样式 */
:deep(.arco-progress-line-text) {
  @apply !tw-text-gray-300;
}

:deep(.arco-progress-line-trail) {
  @apply !tw-bg-gray-700/50;
}

/* spin组件样式 */
:deep(.arco-spin) {
  @apply !tw-h-full;
}

:deep(.arco-spin-children) {
  @apply !tw-h-full;
}

:deep(.arco-spin-loading) {
  @apply !tw-bg-gray-900/60;
}
</style> 