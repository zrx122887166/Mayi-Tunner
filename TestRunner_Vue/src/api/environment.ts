import request from '../utils/request'
import type { ApiResponse } from '../utils/request'

export const VARIABLE_TYPES = {
  string: '字符串',
  integer: '整数',
  float: '浮点数',
  boolean: '布尔值',
  json: 'JSON对象'
} as const

export type VariableType = keyof typeof VARIABLE_TYPES

export interface EnvironmentVariable {
  id: number
  name: string
  value: string
  type: VariableType
  description?: string
  is_sensitive: boolean
}

export interface Environment {
  id: number
  name: string
  base_url: string
  verify_ssl?: boolean
  description: string
  project: number
  project_name?: string
  project_info?: {
    id: number
    name: string
  }
  parent_info?: {
    id: number
    name: string
  } | null
  is_active: boolean
  created_by: number
  created_by_name?: string
  created_time: string
  updated_time: string
  variables: EnvironmentVariable[]
  database_config?: number | null
  database_config_name?: string
  database_config_info?: {
    id: number
    name: string
    db_type: string
    host: string
  } | null
}

export interface GetEnvironmentsParams {
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

export interface CreateEnvironmentData {
  id?: number
  name: string
  base_url: string
  verify_ssl?: boolean
  description: string
  project: number
  is_active: boolean
  variables: EnvironmentVariable[]
  database_config?: number | null
}

export interface ApiErrorResponse {
  status: 'error'
  code: number
  message: string
  data: Record<string, any>
  errors?: Record<string, string[]>
}

export interface CreateEnvironmentResponse {
  status: 'success' | 'error'
  message?: string
  data?: Environment
  errors?: Record<string, string[]>
}

export interface CloneEnvironmentData {
  project_id: number
  name: string
}

export interface BatchCreateVariableItem {
  name: string
  value: string
  type: VariableType
  description: string
  is_sensitive: boolean
}

export interface BatchCreateVariablesRequest {
  environment_id: number
  variables: BatchCreateVariableItem[]
}

export interface NewEnvironmentVariableData {
  name: string
  value: string
  type: VariableType
  description: string
  is_sensitive: boolean
}

export interface CreateEnvironmentVariableData {
  environment: number
  name: string
  value: string
  type: VariableType
  description: string
  is_sensitive: boolean
}

export function getEnvironments(params: GetEnvironmentsParams): Promise<ApiResponse<PaginatedResponse<Environment>>> {
  return request.get('/environments/environments/', {
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10,
      project_id: params.project_id
    }
  })
}

export function createEnvironment(data: CreateEnvironmentData): Promise<CreateEnvironmentResponse> {
  return request.post('/environments/environments/', data)
}

export const deleteEnvironment = (id: number) => {
  return request.delete<ApiResponse<null>>(`/environments/environments/${id}/`)
}

export function updateEnvironment(id: number, data: CreateEnvironmentData): Promise<ApiResponse<Environment>> {
  return request.put(`/environments/environments/${id}/`, data)
}

export function cloneEnvironment(id: number, data: CloneEnvironmentData): Promise<ApiResponse<Environment>> {
  return request.post(`/environments/environments/${id}/clone/`, data)
}

export function batchCreateVariables(data: BatchCreateVariablesRequest): Promise<ApiResponse<null>> {
  return request.post('/environments/variables/batch_create/', data)
}

export function deleteEnvironmentVariable(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/environments/variables/${id}/`)
}

export function createEnvironmentVariable(data: CreateEnvironmentVariableData): Promise<ApiResponse<EnvironmentVariable>> {
  return request.post('/environments/variables/', data)
}

export function updateEnvironmentVariable(id: number, data: CreateEnvironmentVariableData): Promise<ApiResponse<EnvironmentVariable>> {
  return request.put(`/environments/variables/${id}/`, data)
}

export function getEnvironmentDetail(id: number): Promise<ApiResponse<Environment>> {
  return request.get(`/environments/environments/${id}/`)
} 