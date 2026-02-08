<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { createTestCase, updateTestCase, getTestCaseById, runTestCase, getTestCaseHistoryReports, type CreateTestCaseData, type TestCaseStep } from '@/api/testcase'
import { getTestReportDetail } from '@/api/testreport'
import type { TestReportDetail } from '@/api/testreport'
import TestCaseHeader from './TestCaseHeader.vue'
import TestCaseStepList from './TestCaseStepList.vue'
import TestCaseStepDetail from './TestCaseStepDetail.vue'
import TestReportView from '@/views/test-reports/components/ExecutionSteps.vue'

interface Props {
  projectId: number
  mode?: 'create' | 'edit' | 'view'
  testCaseId?: number
}

const router = useRouter()
const route = useRoute()
const props = withDefaults(defineProps<Props>(), {
  mode: 'create'
})
const emit = defineEmits(['cancel', 'success'])

// 从路由参数中获取用例ID
const testCaseId = computed(() => {
  return props.testCaseId || Number(route.params.id)
})

const loading = ref(false)
const activeStep = ref<TestCaseStep | null>(null)

// 报告相关
const showReport = ref(false)
const reportLoading = ref(false)
const latestReport = ref<TestReportDetail | null>(null)

// 初始化表单数据
const formData = reactive<CreateTestCaseData>({
  name: '',
  description: '',
  project: props.projectId,
  priority: 'P3',
  config: {
    base_url: '',
    variables: '',
    parameters: '',
    export: '',
    verify: ''
  },
  steps_info: []
})

// 是否为只读模式
const readonly = computed(() => props.mode === 'view')

interface TestCaseStepForHeader {
  id: number
  name: string
  interface_data: {
    extract?: Record<string, string>
  }
}

// 步骤数据
const steps = ref<TestCaseStep[]>([])
// 用于header组件的步骤数据
const stepsForHeader = computed<TestCaseStepForHeader[]>(() => {
  return steps.value.map(step => ({
    id: step.id || 0,
    name: step.name,
    interface_data: {
      extract: step.interface_data.extract as Record<string, string>
    }
  }))
})

// 更新步骤数据
const updateSteps = (newSteps: TestCaseStep[]) => {
  // 确保每个步骤的模块信息都被正确处理
  steps.value = newSteps.map(step => ({
    ...step,
    interface_info: {
      ...step.interface_info,
      module_info: step.interface_info.module_info || {
        id: step.interface_info.module?.id || 0,
        name: step.interface_info.module?.name || ''
      }
    }
  }))

  // 转换步骤数据以匹配 CreateTestCaseData 的 steps_info 类型
  formData.steps_info = steps.value.map((step, index) => ({
    name: step.name,
    interface_id: step.interface_info.id || 0, // 使用0作为默认值避免undefined
    order: step.order || index + 1,  // 使用步骤现有的order，如果没有则根据索引计算
    interface_data: {
      ...step.interface_data,
      module: step.interface_info.module_info?.id || step.interface_data.module || 0 // 使用0作为默认值
    },
    config: step.config,
    sync_fields: step.sync_fields
  }))
}

// 获取用例详情
const fetchTestCaseDetail = async () => {
  if (props.mode !== 'create' && testCaseId.value) {
    try {
      loading.value = true
      const response = await getTestCaseById(testCaseId.value)
      console.log('获取到的用例详情:', response)

      if (!response || response.status !== 'success') {
        throw new Error(response?.message || '获取用例详情失败')
      }

      const testCase = response.data

      try {
        console.log('开始更新表单数据，测试用例数据:', testCase)

        // 更新表单数据
        formData.name = testCase.name || ''
        formData.description = testCase.description || ''
        formData.priority = testCase.priority || 'P3'
        formData.group = testCase.group === null ? undefined : testCase.group
        formData.tags = testCase.tags || []
        formData.config = {
          base_url: testCase.config?.base_url || '',
          variables: testCase.config?.variables || '',
          parameters: testCase.config?.parameters || '',
          export: testCase.config?.export || '',
          verify: testCase.config?.verify || ''
        }

        console.log('表单数据更新完成:', formData)

        // 更新步骤数据
        console.log('开始更新步骤数据:', testCase.steps)
        updateSteps(testCase.steps || [])
        console.log('步骤数据更新完成:', steps.value)
      } catch (parseError) {
        console.error('解析用例数据失败:', parseError)
        throw new Error('解析用例数据失败')
      }
    } catch (error) {
      console.error('获取用例详情失败:', error)
      Message.error(error instanceof Error ? error.message : '获取用例详情失败')
    } finally {
      loading.value = false
    }
  }
}

// 组件挂载时获取详情
onMounted(() => {
  fetchTestCaseDetail()
})

const handleAddStep = () => {
  if (readonly.value) return

  const newStep: TestCaseStep = {
    id: 0,
    name: `步骤${steps.value.length + 1}`,
    order: steps.value.length + 1,
    interface_info: {
      id: 0,
      name: '',
      method: 'GET',
      url: '',
      module: {
        id: 0,
        name: ''
      },
      project: {
        id: props.projectId,
        name: ''
      }
    },
    interface_data: {
      method: 'GET',
      url: '',
      headers: {},
      params: {},
      body: {},
      validators: [],
      extract: {},
      setup_hooks: [],
      teardown_hooks: [],
      variables: {}
    },
    config: {
      variables: {},
      validators: [],
      extract: {},
      setup_hooks: [],
      teardown_hooks: []
    },
    sync_fields: [
      'method',
      'url',
      'headers',
      'params',
      'body',
      'setup_hooks',
      'teardown_hooks',
      'variables',
      'validators',
      'extract'
    ],
    last_sync_time: null
  }

  const newSteps = [...steps.value, newStep]
  updateSteps(newSteps)
  // 选中新添加的步骤
  handleStepSelect(newSteps[newSteps.length - 1])
}

const handleStepSelect = (step: TestCaseStep | null) => {
  if (step) {
    // 切换到步骤详情模式
    showReport.value = false

    // 确保步骤数据的完整性
    activeStep.value = {
      ...step,
      interface_info: {
        ...step.interface_info,
        module: step.interface_info.module || { id: 0, name: '' },
        module_info: step.interface_info.module_info || step.interface_info.module || { id: 0, name: '' },
        project: step.interface_info.project || { id: props.projectId, name: '' }
      },
      interface_data: {
        ...step.interface_data,
        headers: step.interface_data.headers || {},
        params: step.interface_data.params || {},
        body: step.interface_data.body || {},
        validators: step.interface_data.validators || [],
        extract: step.interface_data.extract || {},
        setup_hooks: step.interface_data.setup_hooks || [],
        teardown_hooks: step.interface_data.teardown_hooks || [],
        variables: step.interface_data.variables || {}
      },
      config: {
        ...step.config,
        variables: step.config?.variables || {},
        validators: step.config?.validators || [],
        extract: step.config?.extract || {},
        setup_hooks: step.config?.setup_hooks || [],
        teardown_hooks: step.config?.teardown_hooks || []
      }
    }
  } else {
    activeStep.value = null
  }
}

const handleStepDelete = (step: TestCaseStep) => {
  if (readonly.value) return

  const index = steps.value.findIndex(s => s === step)
  if (index !== -1) {
    const newSteps = [...steps.value]
    newSteps.splice(index, 1)
    // 重新计算步骤顺序
    newSteps.forEach((s, i) => {
      s.order = i + 1
    })
    updateSteps(newSteps)
    // 如果删除的是当前选中的步骤，清空选中状态
    if (activeStep.value === step) {
      activeStep.value = null
    }
  }
}

const validateForm = () => {
  if (!formData.name) {
    Message.error('请输入用例名称')
    return false
  }
  if (!formData.priority) {
    Message.error('请选择优先级')
    return false
  }
  // 如果有步骤，验证步骤的完整性
  if (steps.value.length > 0) {
    for (const step of steps.value) {
      if (!step.name) {
        Message.error('请输入步骤名称')
        return false
      }
      if (!step.interface_info.id) {
        Message.error('请选择接口')
        return false
      }
    }
  }
  return true
}

// 保存测试用例，返回是否保存成功
const handleSubmit = async (continueAction?: () => void) => {
  if (readonly.value) return false
  if (!validateForm()) return false

  try {
    loading.value = true
    const submitData: CreateTestCaseData = {
      ...formData,
      steps_info: steps.value.map((step, index) => ({
        name: step.name,
        interface_id: step.interface_info.id || 0, // 使用0作为默认值避免undefined
        interface_data: step.interface_data,
        config: step.config,
        sync_fields: step.sync_fields,
        order: index + 1
      }))
    }

    if (props.mode === 'edit' && testCaseId.value) {
      await updateTestCase(testCaseId.value, submitData)
      Message.success('更新成功')
      // 更新成功后重新获取测试用例详情
      await fetchTestCaseDetail()
    } else {
      // 创建用例
      const response = await createTestCase(submitData)
      Message.success('创建成功，现在您可以添加测试步骤了')

      // 更新模式为编辑模式，并设置testCaseId（通过替换当前路由实现）
      if (response && response.data && response.data.id) {
        // 使用replace避免在浏览器历史中创建新条目
        router.replace({
          name: 'test-case-edit',
          params: { id: response.data.id },
          query: { projectId: props.projectId }
        })

        // 更新测试用例ID并保持在当前页面
        // 通过路由参数的变化，computed testCaseId会自动更新
        // 无需直接赋值
      }
    }

    // 如果有后续操作，执行它
    if (continueAction) {
      setTimeout(() => {
        continueAction()
      }, 500) // 延迟执行，确保路由和数据已更新
    }

    return true
  } catch (error) {
    Message.error(props.mode === 'edit' ? '更新失败' : '创建失败')
    return false
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  router.push({
    name: 'test-cases',
    query: { projectId: props.projectId }
  })
}

const updateHeaderData = (data: Pick<CreateTestCaseData, 'name' | 'description' | 'priority' | 'group' | 'tags'>) => {
  Object.assign(formData, data)
}

const updateStepData = (step: TestCaseStep) => {
  console.log('父组件接收到的更新数据:', step)
  const index = steps.value.findIndex(s => {
    if (activeStep.value) {
      // 对于未保存的步骤（自定义接口），通过order匹配
      if (!s.id) {
        return s.order === activeStep.value.order
      }
      // 对于已保存的步骤，通过id匹配
      return s.id === activeStep.value.id
    }
    return false
  })

  if (index !== -1) {
    console.log('找到要更新的步骤索引:', index)
    const newSteps = [...steps.value]
    // 如果是自定义接口（id为0），保持id为0
    if (!steps.value[index].id) {
      step.id = 0
    }
    newSteps[index] = step
    console.log('更新后的步骤列表:', newSteps)
    updateSteps(newSteps)
    // 同时更新当前选中的步骤
    activeStep.value = step
  } else {
    console.log('未找到要更新的步骤')
  }
}

// 测试用例运行相关
const runResultLoading = ref(false)

// 处理运行用例
const handleRun = async (data: { testCaseId: number, environmentId: number }) => {
  try {
    runResultLoading.value = true

    // 运行测试用例
    const response = await runTestCase(data.testCaseId, {
      environment: data.environmentId
    });

    // 只要response对象存在，且具有status和data属性，我们就认为接口调用成功
    if (response && typeof response === 'object' && 'status' in response &&
        String(response.status) === 'success' && 'data' in response) {
      Message.success('用例运行成功');

      // response.data包含report_id时，直接获取这个报告并显示
      const responseData = response.data;
      if (responseData && typeof responseData === 'object' && 'report_id' in responseData) {
        await fetchReportDetail(Number(responseData.report_id));
        return;
      }

      // 如果没有report_id，获取最新的测试报告
      try {
        const reportsResponse = await getTestCaseHistoryReports(data.testCaseId, {
          page: 1,
          page_size: 1
        });

        if (reportsResponse && reportsResponse.status === 'success' &&
            reportsResponse.data && reportsResponse.data.results &&
            reportsResponse.data.results.length > 0) {
          const latestReportData = reportsResponse.data.results[0];
          await fetchReportDetail(latestReportData.id);
        } else {
          Message.warning('获取运行结果失败，请前往报告列表查看');
        }
      } catch (error) {
        console.error('获取测试报告失败:', error);
        Message.warning('获取报告失败，请前往报告列表查看');
      }
    } else {
      // 接口调用失败
      const errorMsg = response && typeof response === 'object' && 'message' in response
        ? String(response.message)
        : '运行用例失败';
      throw new Error(errorMsg);
    }
  } catch (error) {
    console.error('运行用例失败:', error);
    Message.error(error instanceof Error ? error.message : '运行用例失败');
  } finally {
    runResultLoading.value = false;
  }
}

// 获取报告详情
const fetchReportDetail = async (reportId: number) => {
  try {
    reportLoading.value = true;
    const response = await getTestReportDetail(reportId);

    if (response && response.data) {
      // 深度转换报告数据结构以符合组件需要的格式
      latestReport.value = convertReportFormat(response.data);
      showReport.value = true;
      activeStep.value = null; // 清除当前选中的步骤
    } else {
      Message.error('获取报告详情失败');
    }
  } catch (error) {
    console.error('获取报告详情失败:', error);
    Message.error('获取报告详情失败，请稍后重试');
  } finally {
    reportLoading.value = false;
  }
}

// 转换报告格式以适应组件需要
const convertReportFormat = (reportData: any): TestReportDetail => {
  // 确保基本数据结构存在
  const report = { ...reportData };

  // 处理步骤详情
  if (report.details && Array.isArray(report.details)) {
    report.details = report.details.map((detail: any) => {
      // 处理响应时间字段
      if (detail.response) {
        detail.response.response_time_ms = detail.response.response_time_ms || detail.response.response_time || 0;
      }

      // 处理验证器格式
      if (typeof detail.validators === 'string' || Array.isArray(detail.validators)) {
        // 将字符串数组转换为符合格式的验证器对象
        detail.validators = {
          success: detail.success, // 使用步骤的成功状态
          validate_extractor: []  // 空数组，因为原始数据不包含详细验证信息
        };
      }

      return detail;
    });
  }

  return report as TestReportDetail;
}

// 处理显示报告按钮点击
const handleShowReport = async (testCaseId: number) => {
  try {
    reportLoading.value = true;
    // 获取该测试用例最新的报告
    const reportsResponse = await getTestCaseHistoryReports(testCaseId, {
      page: 1,
      page_size: 1
    });

    if (reportsResponse && reportsResponse.status === 'success' &&
        reportsResponse.data && reportsResponse.data.results &&
        reportsResponse.data.results.length > 0) {
      const latestReportData = reportsResponse.data.results[0];
      await fetchReportDetail(latestReportData.id);
    } else {
      Message.warning('该测试用例暂无报告，请先运行测试');
      showReport.value = false;
    }
  } catch (error) {
    console.error('获取报告列表失败:', error);
    Message.error('获取报告列表失败，请稍后重试');
  } finally {
    reportLoading.value = false;
  }
}
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4 tw-overflow-hidden">
    <!-- 顶部：基础信息 -->
    <div class="tw-flex-shrink-0 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-p-4">
      <test-case-header
        :model-value="{
          name: formData.name || '',
          description: formData.description || '',
          priority: formData.priority,
          group: formData.group !== undefined ? formData.group : null,
          tags: formData.tags || [],
          config: {
            base_url: formData.config?.base_url || '',
            variables: typeof formData.config?.variables === 'string' ? formData.config.variables : JSON.stringify(formData.config?.variables || {}),
            parameters: typeof formData.config?.parameters === 'string' ? formData.config.parameters : JSON.stringify(formData.config?.parameters || {}),
            export: Array.isArray(formData.config?.export) ? formData.config.export : [],
            verify: typeof formData.config?.verify === 'boolean' ? formData.config.verify : true
          }
        }"
        :loading="loading"
        :readonly="readonly"
        :project-id="projectId"
        :test-case-id="testCaseId"
        :steps="stepsForHeader"
        @update:model-value="updateHeaderData"
        @cancel="handleCancel"
        @save="handleSubmit"
        @run="handleRun"
        @show-report="handleShowReport"
      />
    </div>

    <!-- 主体内容：左侧步骤列表 + 右侧步骤详情 -->
    <div class="tw-flex-1 tw-flex tw-gap-4 tw-min-h-0">
      <!-- 左侧：步骤列表 -->
      <div class="tw-w-[20%] tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-p-4 tw-overflow-hidden">
        <test-case-step-list
          :steps="steps"
          :active-step="activeStep"
          :readonly="readonly"
          :test-case-id="testCaseId"
          :test-case="{
            name: formData.name || '',
            priority: formData.priority as 'P0' | 'P1' | 'P2' | 'P3',
            project: formData.project,
            description: formData.description,
            group: formData.group,
            tags: formData.tags || [],
            config: {
              base_url: formData.config?.base_url || '',
              variables: typeof formData.config?.variables === 'string' ? {} : (formData.config?.variables || {}),
              parameters: typeof formData.config?.parameters === 'string' ? {} : (formData.config?.parameters || {}),
              export: Array.isArray(formData.config?.export) ? formData.config.export : [],
              verify: typeof formData.config?.verify === 'boolean' ? formData.config.verify : true
            }
          }"
          @add="handleAddStep"
          @select="handleStepSelect"
          @delete="handleStepDelete"
          @update:steps="updateSteps"
          @save-test-case="(callback) => handleSubmit(callback)"
        />
      </div>

      <!-- 右侧：步骤详情或报告详情 -->
      <div class="tw-flex-1 tw-min-w-0 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden">
        <!-- 步骤详情 -->
        <test-case-step-detail
          v-if="activeStep && !showReport"
          :model-value="activeStep"
          :readonly="readonly"
          :test-case-id="testCaseId"
          @update:model-value="updateStepData"
        />

        <!-- 报告详情 -->
        <a-spin :loading="reportLoading" dot class="tw-h-full" v-else-if="showReport && latestReport">
          <div class="tw-h-full tw-overflow-auto tw-p-4">
            <test-report-view :report="latestReport as any" />
          </div>
        </a-spin>

        <!-- 空状态 -->
        <div v-else class="tw-flex tw-items-center tw-justify-center tw-h-full tw-text-gray-500">
          {{ showReport ? '暂无报告数据' : (readonly ? '请选择步骤查看详情' : '请选择或添加步骤') }}
        </div>
      </div>
    </div>
  </div>
</template>