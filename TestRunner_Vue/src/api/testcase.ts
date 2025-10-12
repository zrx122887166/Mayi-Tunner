import request from '@/utils/request'
import type { ApiResponse } from '@/utils/request'

export interface TestCaseListResponse {
  count: number
  next: string | null
  previous: string | null
  results: TestCase[]
}

export interface TestCase {
  id: number
  name: string
  description?: string
  priority: 'P0' | 'P1' | 'P2' | 'P3'  // 用例优先级
  steps_info?: Array<{
    name: string
    interface_id: number
    interface_data?: {
      method: string
      url: string
      headers: Record<string, any>
      params: Record<string, any>
      body: Record<string, any>
      validators: any[]
      extract: Record<string, any>
      setup_hooks: string[]
      teardown_hooks: string[]
      variables: Record<string, any>
    }
    config?: {
      variables?: Record<string, any>
      validators?: Array<{
        check: string
        expect: any
        comparator: string
      }>
      extract?: Record<string, any>
      setup_hooks?: string[]
      teardown_hooks?: string[]
    }
    sync_fields?: string[]
  }>
  project: number
  group?: number
  tags?: number[]
  config: {
    base_url: string
    variables: string | Record<string, any>
    parameters: string | Record<string, any>
    export: string | string[]
    verify: string | boolean
  }
  created_time: string
  updated_time: string
  steps: TestCaseStep[]
  created_by: string
  tags_info?: {
    id: number
    name: string
    color: string
    project: number
    created_by: string
    created_time: string
  }[]
  group_info?: {
    id: number
    name: string
    full_path: string
    project: number
    created_by: string
    created_time: string
  }
  related_interfaces?: {
    module: string
    interfaces: {
      id: number
      name: string
      method: string
      url: string
      step_name: string
      step_order: number
    }[]
  }[]
}

export interface TestCaseStep {
  id?: number
  name: string
  order: number
  interface_info: {
    id?: number
    name: string
    method: string
    url: string
    module: {
      id: number
      name: string
    }
    module_info?: {
      id: number
      name: string
    }
    project: {
      id: number
      name: string
    }
  }
  interface_data: {
    method: string
    url: string
    headers: Record<string, any>
    params: Record<string, any>
    body: Record<string, any>
    validators: any[]
    extract: Record<string, any>
    setup_hooks: string[]
    teardown_hooks: string[]
    variables: Record<string, any>
    module?: number
  }
  config: {
    variables: Record<string, any>
    validators: any[]
    extract: Record<string, any>
    setup_hooks: string[]
    teardown_hooks: string[]
  }
  sync_fields: string[]
  last_sync_time: string | null
}

export interface TestCaseQueryParams {
  project?: number
  module?: number
  priority?: string
  group?: string
  tags?: string[]
  name?: string
  description?: string
  ordering?: string
  page?: number
  page_size?: number
}

export interface CreateTestCaseData {
  name: string  // 必填，测试用例名称
  description?: string  // 选填，用例描述
  priority: 'P0' | 'P1' | 'P2' | 'P3'  // 必填，用例优先级
  project: number  // 必填，所属项目ID
  module?: number  // 选填，所属模块ID
  group?: number  // 选填，所属分组ID
  tags?: number[]  // 选填，标签ID列表
  config: {  // 用例配置
    base_url: string
    variables: string | Record<string, any>
    parameters: string | Record<string, any>
    export: string | string[]
    verify: string | boolean
  }
  steps_info?: Array<{
    name: string
    interface_id: number
    order: number
    interface_data?: {
      method: string
      url: string
      headers: Record<string, any>
      params: Record<string, any>
      body: Record<string, any>
      validators: any[]
      extract: Record<string, any>
      setup_hooks: string[]
      teardown_hooks: string[]
      variables: Record<string, any>
    }
    config?: {
      variables?: Record<string, any>
      validators?: Array<{
        check: string
        expect: any
        comparator: string
      }>
      extract?: Record<string, any>
      setup_hooks?: string[]
      teardown_hooks?: string[]
    }
    sync_fields?: string[]
  }>  // 选填，测试步骤
}

export function getTestCases(params: TestCaseQueryParams): Promise<ApiResponse<TestCaseListResponse>> {
  // 处理 tags 参数，确保它是一个数组
  const processedParams = { ...params }
  if (processedParams.tags) {
    // 如果是单个值，转换为数组
    processedParams.tags = Array.isArray(processedParams.tags) ? processedParams.tags : [processedParams.tags]
  }

  return request({
    url: '/testcases/',
    method: 'get',
    params: processedParams,
    paramsSerializer: {
      indexes: null // 这将使 axios 在序列化数组时不添加索引
    }
  })
}

export function createTestCase(data: CreateTestCaseData): Promise<ApiResponse<TestCase>> {
  return request({
    url: '/testcases/',
    method: 'post',
    data
  })
}

export function updateTestCase(id: number, data: CreateTestCaseData): Promise<ApiResponse<TestCase>> {
  return request({
    url: `/testcases/${id}/`,
    method: 'put',
    data
  })
}

// 标签相关接口
// 标签相关类型定义
export interface Tag {
  id: number
  name: string
  color: string
  project: number
  created_by: {
    id: number
    username: string
  }
  created_time: string
}

export interface TagListResponse {
  count: number
  results: Tag[]
}

export interface TagStatistics {
  id: number
  name: string
  color: string
  usage_count: number
}

export interface CreateTagData {
  name: string
  color: string
  project: number
}

// 标签相关接口
export const tagApi = {
  // 获取标签列表
  getTags(params: {
    project_id: number
    search?: string
    ordering?: string
    page?: number
    page_size?: number
  }): Promise<TagListResponse> {
    return request({
      url: '/testcases/tags/',
      method: 'get',
      params
    })
  },

  // 创建标签
  createTag(data: CreateTagData): Promise<Tag> {
    return request({
      url: '/testcases/tags/',
      method: 'post',
      data
    })
  },

  // 更新标签
  updateTag(id: number, data: CreateTagData): Promise<Tag> {
    return request({
      url: `/testcases/tags/${id}/`,
      method: 'put',
      data
    })
  },

  // 删除标签
  deleteTag(id: number): Promise<void> {
    return request({
      url: `/testcases/tags/${id}/`,
      method: 'delete'
    })
  },

  // 获取标签使用统计
  getTagStatistics(projectId: number): Promise<TagStatistics[]> {
    return request({
      url: '/testcases/tags/statistics/',
      method: 'get',
      params: { project_id: projectId }
    })
  }
}

export function getTestCaseById(id: number): Promise<ApiResponse<TestCase>> {
  return request({
    url: `/testcases/${id}/`,
    method: 'get'
  })
}

export function addTestCaseSteps(testCaseId: number, data: CreateTestCaseData): Promise<ApiResponse<TestCase>> {
  return request({
    url: `/testcases/${testCaseId}/`,
    method: 'put',
    data
  })
}

// export function deleteTestCaseStep(testCaseId: number, stepId: number): Promise<ApiResponse<void>> {
//   return request({
//     url: `/testcases/${testCaseId}/steps/${stepId}/`,
//     method: 'delete'
//   })
// }

export function deleteTestCaseStep(testCaseId: number, stepId: number) {
  return request({
    url: `/testcases/${testCaseId}/delete_step/`,
    method: 'delete',
    params: {
      step_id: stepId
    }
  })
}


// 运行用例
export const runTestCase = (id: number, data: { environment: number }) => {
  return request({
    url: `/testcases/${id}/run/`,
    method: 'post',
    data
  })
}

// 更新测试用例步骤
export const updateTestCaseStep = (testCaseId: number, data: {
  step_id: number,
  name: string,
  interface_data: {
    method: string,
    url: string,
    headers?: Record<string, any> | any[],
    params?: Record<string, any> | any[],
    body?: Record<string, any>,
    validators?: any[],
    extract?: Record<string, any>,
    setup_hooks?: string[],
    teardown_hooks?: string[],
    variables?: Record<string, any>
  },
  config?: {
    variables?: Record<string, any>,
    validators?: any[],
    extract?: Record<string, any>,
    setup_hooks?: string[],
    teardown_hooks?: string[]
  },
  sync_fields?: string[]
}): Promise<ApiResponse<TestCaseStep>> => {
  return request({
    url: `/testcases/${testCaseId}/update_step/`,
    method: 'put',
    data
  })
}

// 更新测试用例步骤顺序
export const updateTestCaseStepOrder = (testCaseId: number, data: {
  step_id: number,
  order: number
}): Promise<ApiResponse<TestCaseStep>> => {
  return request({
    url: `/testcases/${testCaseId}/update_step/`,
    method: 'put',
    data
  })
}

// 关联接口相关类型定义
export interface ReferencedInterface {
  interface: {
    id: number
    name: string
    method: string
    url: string
    module: {
      id: number
      name: string
    } | null
    project: {
      id: number
      name: string
    }
  }
  step: {
    id: number
    name: string
    order: number
  }
}

export interface ReferencedInterfacesResponse {
  status: string
  code: number
  message: string
  data: {
    count: number
    interfaces: ReferencedInterface[]
  }
}

// 获取测试用例关联接口列表
export function getTestCaseReferencedInterfaces(id: number): Promise<ReferencedInterfacesResponse> {
  return request({
    url: `/testcases/${id}/referenced_interfaces/`,
    method: 'get'
  })
}

// 删除测试用例
export function deleteTestCase(id: number): Promise<ApiResponse<void>> {
  return request({
    url: `/testcases/${id}/`,
    method: 'delete'
  })
}

// 测试报告相关类型定义
export interface TestCaseHistoryReport {
  id: number
  name: string
  status: 'success' | 'failure' | 'error'
  success_count: number
  fail_count: number
  error_count: number
  duration: number
  start_time: string
  testcase_name: string
  success_rate: string
  environment_name: string
  executed_by_name: string
  environment_info?: {
    id: number
    name: string
    base_url: string
    description: string
    project: {
      id: number
      name: string
    }
  } | null
  details: Array<{
    id: number
    step_name: string
    success: boolean
    elapsed: number
    request: {
      method: string
      url: string
      headers: Record<string, string>
      body: any
    }
    response: {
      status_code: number
      headers: Record<string, string>
      body: any
      content_size: number
      response_time_ms: number
    }
    validators: any[]
    extracted_variables: Record<string, any>
    attachment: string
  }>
}

export interface TestCaseHistoryReportsResponse {
  status: 'success' | 'error'
  code: number
  message: string
  data: {
    count: number
    next: string | null
    previous: string | null
    results: TestCaseHistoryReport[]
  }
}

// 获取测试用例历史报告
export function getTestCaseHistoryReports(
  testcaseId: number,
  params: {
    page?: number
    page_size?: number
  } = {}
): Promise<TestCaseHistoryReportsResponse> {
  return request({
    url: `/testcases/${testcaseId}/history_reports/`,
    method: 'get',
    params
  })
}

// 测试用例调试相关接口
export interface DebugTestCaseRequest {
  method: string
  url: string
  environment_id?: number
  headers?: Array<{ key: string, value: string, enabled?: boolean, description?: string }>
  params?: Array<{ key: string, value: string, enabled?: boolean, description?: string }>
  body?: {
    type: 'none' | 'form-data' | 'x-www-form-urlencoded' | 'raw' | 'binary'
    content: any
  }
  setup_hooks?: string[]
  teardown_hooks?: string[]
  extract?: Record<string, string>
  validators?: Array<Record<string, [string, string]>>
}

// 调试测试用例步骤
export const debugTestCase = (data: DebugTestCaseRequest): Promise<ApiResponse<any>> => {
  return request({
    url: '/testcases/debug/',
    method: 'post',
    data
  })
}