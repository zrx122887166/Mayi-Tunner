// API响应接口
export interface ApiResponse<T> {
  status: string
  code: number
  message: string
  data: T
}

// API分页响应接口
export interface PaginatedData<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// API模块接口类型定义
export interface ApiModule {
  id: number
  name: string
  project: number
  parent: number | null
  description: string | null
  create_time: string
  update_time: string
  children?: ApiModule[]
}

// API接口验证器类型定义
export interface ApiValidator {
  // 基础比较断言
  eq?: [string, any]  // 等于
  ne?: [string, any]  // 不等于
  gt?: [string, any]  // 大于
  ge?: [string, any]  // 大于等于
  gte?: [string, any] // 大于等于（别名）
  lt?: [string, any]  // 小于
  le?: [string, any]  // 小于等于
  lte?: [string, any] // 小于等于（别名）
  
  // 字符串相关断言
  contains?: [string, any]     // 包含
  contained_by?: [string, any]  // 被包含
  startswith?: [string, any]   // 以...开头
  endswith?: [string, any]     // 以...结尾
  regex_match?: [string, any]  // 正则匹配
  str_eq?: [string, any]       // 字符串等于
  
  // 长度相关断言
  length_equal?: [string, any]              // 长度等于
  length_equals?: [string, any]             // 长度等于（别名）
  length_greater_than?: [string, any]       // 长度大于
  length_less_than?: [string, any]          // 长度小于
  length_greater_or_equals?: [string, any]  // 长度大于等于
  length_less_or_equals?: [string, any]     // 长度小于等于
  
  // 其他断言
  type_match?: [string, any]  // 类型匹配
  
  // 兼容格式
  check?: string   // 检查字段
  expect?: any     // 期望值
}

// 通用的键值对类型定义
export interface KeyValuePair {
  key: string
  value: string
  description: string
  enabled: boolean
}

// SQL钩子类型定义
export interface SqlHook {
  type: 'sql'
  db_key?: string  // 保留向后兼容性
  db_id?: number   // 添加新的数据库ID字段
  sql: string
  var_name?: string
}

// API接口类型定义
export interface ApiInterface {
  id?: number
  name: string
  method: string
  url: string
  project: number
  module: number
  headers: KeyValuePair[]
  params: KeyValuePair[]
  body: {
    type: 'none' | 'form-data' | 'x-www-form-urlencoded' | 'raw' | 'binary'
    content: KeyValuePair[] | string | null
  }
  setup_hooks: string[] | SqlHook[]
  teardown_hooks: string[] | SqlHook[]
  variables: Record<string, string>
  validators: ApiValidator[]
  extract: Record<string, string>
  create_time?: string
  update_time?: string
}

import request from '@/utils/request'

// 创建接口
export function createInterface(data: ApiInterface) {
  return request.post<ApiResponse<ApiInterface>>('/interfaces/', data)
}

// 更新接口
export function updateInterface(id: number, data: ApiInterface) {
  return request.put<ApiResponse<ApiInterface>>(`/interfaces/${id}/`, data)
}

// 获取接口列表
export function getInterfaces(params?: GetInterfacesParams) {
  return request.get<PaginatedData<ApiInterface>>('/interfaces/', { params })
}

// 删除接口
export function deleteInterface(id: number) {
  return request.delete<ApiResponse<null>>(`/interfaces/${id}/`)
}

// 获取接口详情
export function getInterfaceDetail(id: number) {
  return request.get<ApiResponse<ApiInterface & { module_info: ApiModule }>>(`/interfaces/${id}/`)
}

export interface GetInterfacesParams {
  module_id?: number | null
  project_id?: number
  page?: number
  page_size?: number
  no_module?: boolean
}

// 调试接口请求参数类型
export interface DebugInterfaceRequest {
  environment_id?: number
  method: string
  url: string
  headers?: KeyValuePair[]
  params?: KeyValuePair[]
  body?: {
    type: 'none' | 'form-data' | 'x-www-form-urlencoded' | 'raw' | 'binary'
    content: KeyValuePair[] | string | null
  }
  variables?: Record<string, any>
  setup_hooks?: string[] | SqlHook[]
  teardown_hooks?: string[] | SqlHook[]
  validators?: ApiValidator[]
  extract?: Record<string, string>
}

// 调试接口响应类型
export interface DebugInterfaceResponse {
  request: {
    method: string
    url: string
    headers: Record<string, string>
    body: any
  }
  response: {
    status_code: number
    headers: Record<string, string>
    content: string
    content_size: number
    content_type: string
    response_time_ms: number
  }
  validation_results: Array<{
    comparator: string
    check: string
    expect: any
    actual: any
    result: boolean
  }>
  extracted_variables: Record<string, any>
  elapsed: number
  status: string
  error?: string
  sql_results?: Record<string, any>
  setup_hooks_info?: Array<{
    type: string
    sql?: string
    db_key?: string
    var_name?: string
    executed: boolean
  }>
}

// 调试接口
export const debugInterface = (id: number, data: DebugInterfaceRequest) => {
  return request.post<ApiResponse<DebugInterfaceResponse>>(`/interfaces/${id}/debug/`, data)
}

// 快速调试接口请求参数类型
export interface QuickDebugInterfaceRequest {
  project_id: number
  method: string
  url: string
  headers?: Record<string, string>
  params?: Record<string, any>
  body?: any
  body_type?: 'none' | 'form-data' | 'x-www-form-urlencoded' | 'raw' | 'binary'
  environment_id?: number
  extract?: Record<string, string>
  validators?: ApiValidator[]
  setup_hooks?: string[] | SqlHook[]
  teardown_hooks?: string[] | SqlHook[]
}

// 快速调试接口
export const quickDebugInterface = (data: QuickDebugInterfaceRequest) => {
  return request.post<ApiResponse<DebugInterfaceResponse>>('/interfaces/quick_debug/', data)
}