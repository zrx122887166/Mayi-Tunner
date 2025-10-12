import request from '../utils/request'

interface ApiResponse<T> {
  status: string
  code: number
  message: string
  data: T
}

interface PageResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TestCase {
  id: number
  name: string
  description: string
  priority: string
  config: {
    export: string[]
    verify: boolean
    base_url: string
    variables: Record<string, any>
    parameters: Record<string, any>
  }
  project: number
  group: number
  tags: number[]
  tags_info: Array<{
    id: number
    name: string
    color: string
    project: number
    created_by: number
    created_time: string
  }>
  group_info: {
    id: number
    name: string
    parent: number | null
    project: number
    created_by: number
    created_time: string
    full_path: string
    children: any[]
  }
  created_by: number | null
  created_time: string
  updated_time: string
  steps: Array<{
    id: number
    name: string
    order: number
    interface_info: {
      id: number
      name: string
      method: string
      url: string
      module: {
        id: number
        name: string
      }
      project: {
        id: number
        name: string
      }
    } | null
    interface_data: {
      url: string
      body: {
        type: string
        content: any
      }
      method: string
      params: any[]
      extract: Record<string, string>
      headers: Array<{
        key: string
        value: string
        enabled: boolean
        description: string
      }>
      variables: Record<string, any>
      validators: Array<{
        eq: [string, string]
      }>
      setup_hooks: string[]
      teardown_hooks: string[]
    }
    sync_fields: any[]
    last_sync_time: string | null
  }>
  related_interfaces: Array<{
    module: string
    interfaces: Array<{
      id: number
      name: string
      method: string
      url: string
      step_name: string
      step_order: number
    }>
  }>
}

export interface TaskCase {
  id: number
  testcase_id: number
  testcase_name: string
  order: number
}

export interface TestTaskSuite {
  id: number
  name: string
  description: string
  priority: string
  fail_fast: boolean
  project: number
  project_name: string
  created_by: number
  created_by_name: string
  created_time: string
  updated_time: string
  task_cases: TaskCase[]
}

export interface TestTaskSuiteForm {
  name: string
  description: string
  priority: string
  fail_fast: boolean
  project: number
  test_cases?: number[] // 选中的测试用例ID列表
}

// 获取测试任务集列表
export const getTestTaskSuites = (params: {
  project: number
  page: number
  page_size: number
  search?: string
  priority?: string
}): Promise<ApiResponse<PageResponse<TestTaskSuite>>> => {
  return request.get('testtasks/suites/', { params })
}

// 创建测试任务集
export const createTestTaskSuite = (data: TestTaskSuiteForm): Promise<ApiResponse<TestTaskSuite>> => {
  return request.post('testtasks/suites/', data)
}

// 更新测试任务集
export const updateTestTaskSuite = (id: number, data: TestTaskSuiteForm): Promise<ApiResponse<TestTaskSuite>> => {
  return request.put(`testtasks/suites/${id}/`, data)
}

// 删除测试任务集
export const deleteTestTaskSuite = (id: number): Promise<ApiResponse<null>> => {
  return request.delete(`testtasks/suites/${id}/`)
}

// 获取测试任务集详情
export const getTestTaskSuite = (id: number): Promise<ApiResponse<TestTaskSuite>> => {
  return request.get(`testtasks/suites/${id}/`)
}

// 执行测试任务集
export const runTestTaskSuite = (id: number): Promise<ApiResponse<null>> => {
  return request.post(`testtasks/suites/${id}/run/`)
}

// 获取测试用例列表
export const getTestCases = (params: {
  project: number
  page: number
  page_size: number
  name?: string
  description?: string
  ordering?: string
}): Promise<ApiResponse<PageResponse<TestCase>>> => {
  return request.get('testcases/', { params })
}

// 添加测试用例到任务集
export const addTestCasesToSuite = (suiteId: number, testCaseIds: number[]): Promise<ApiResponse<null>> => {
  return request.post(`testtasks/suites/${suiteId}/add_cases/`, { test_cases: testCaseIds })
}

// 从任务集移除测试用例
export const removeTestCasesFromSuite = (suiteId: number, testCaseIds: number[]): Promise<ApiResponse<null>> => {
  return request.post(`testtasks/suites/${suiteId}/remove_cases/`, { test_cases: testCaseIds })
}

// 向测试任务集添加测试用例
export const addTestCaseToSuite = (suiteId: number, testcaseIds: number[]): Promise<ApiResponse<null>> => {
  return request.post(`testtasks/suites/${suiteId}/add-testcases/`, {
    testcase_ids: testcaseIds
  })
}

// 从任务集移除单个测试用例
export const removeTestCaseFromSuite = (suiteId: number, testCaseId: number): Promise<ApiResponse<null>> => {
  return request.delete(`testtasks/suites/${suiteId}/remove-testcase/${testCaseId}/`)
}

// 更新任务集中测试用例的顺序
export const updateTestCaseOrder = (suiteId: number, testCaseOrders: { id: number, order: number }[]): Promise<ApiResponse<null>> => {
  return request.post(`testtasks/suites/${suiteId}/update_case_order/`, { case_orders: testCaseOrders })
}

// 测试任务执行相关类型定义
export interface TestTaskExecution {
  id: number
  task_suite: number
  task_suite_name: string
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'error'
  environment: number | null
  environment_name: string | null
  start_time: string | null
  end_time: string | null
  duration: number | null
  total_count: number
  success_count: number
  fail_count: number
  error_count: number
  success_rate: string
  executed_by: number
  executed_by_name: string
  created_time: string
}

export interface CreateTestTaskExecutionData {
  task_suite_id: number
  environment_id?: number
}

// 创建测试任务执行
export function createTestTaskExecution(data: CreateTestTaskExecutionData): Promise<ApiResponse<TestTaskExecution>> {
  return request({
    url: '/testtasks/executions/',
    method: 'post',
    data: {
      task_suite_id: data.task_suite_id,
      environment_id: data.environment_id
    }
  })
}

// 获取测试任务执行详情
export function getTestTaskExecution(id: number): Promise<ApiResponse<TestTaskExecution>> {
  return request({
    url: `/testtasks/executions/${id}/`,
    method: 'get'
  })
}

// 获取测试任务执行记录列表
export function getTestTaskExecutions(params: {
  task_suite?: number
  page?: number
  page_size?: number
  status?: string
  environment?: number
  ordering?: string
}): Promise<ApiResponse<PageResponse<TestTaskExecution>>> {
  return request({
    url: '/testtasks/executions/',
    method: 'get',
    params
  })
}

// 取消测试任务执行
export function cancelTestTaskExecution(id: number): Promise<ApiResponse<void>> {
  return request({
    url: `/testtasks/executions/${id}/cancel/`,
    method: 'post'
  })
}

// 获取测试任务执行用例结果
export function getTestTaskExecutionCaseResults(id: number) {
  return request.get(`/testtasks/executions/${id}/case-results/`)
} 