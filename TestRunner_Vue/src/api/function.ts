import request from '../utils/request'
import type { ApiResponse } from '../utils/request'

export interface Function {
  id: number
  name: string
  description: string | null
  code: string
  project: number
  project_name: string
  created_by: number
  created_by_name: string
  created_time: string
  updated_time: string
  is_active: boolean
  _loaded?: boolean
}

export interface GetFunctionsParams {
  page?: number
  page_size?: number
  project_id?: number
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiErrorResponse {
  status: 'error'
  code: number
  message: string
  data: Record<string, any>
  errors?: {
    name?: string[]
    code?: string[]
    [key: string]: string[] | undefined
  }
}

// 测试运行函数
export interface TestFunctionRequest {
  code: string;
  test_args: Record<string, any>;
}

export interface TestFunctionResponse {
  status: 'success' | 'error';
  code: number;
  message: string;
  data: {
    result: any;
  };
}

export const testFunction = (data: TestFunctionRequest) => {
  return request.post<TestFunctionResponse>('/functions/functions/test_function/', data).then(res => res.data);
};

// 获取函数列表
export function getFunctions(params: GetFunctionsParams): Promise<ApiResponse<PaginatedResponse<Function>>> {
  return request.get('/functions/functions/', {
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10,
      project_id: params.project_id
    }
  })
}

// 创建函数
export function createFunction(data: Partial<Function>): Promise<ApiResponse<Function> | ApiErrorResponse> {
  return request.post('/functions/functions/', data)
}

// 更新函数
export function updateFunction(id: number, data: Partial<Function>): Promise<ApiResponse<Function> | ApiErrorResponse> {
  return request.put(`/functions/functions/${id}/`, data)
}

// 删除函数
export function deleteFunction(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/functions/functions/${id}/`)
}

// 获取函数详情
export const getFunctionDetail = (id: number): Promise<ApiResponse<Function>> => {
  return request.get(`/functions/functions/${id}/`)
} 