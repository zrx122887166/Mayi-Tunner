import type { ApiResponse } from '@/utils/request'
import request from '@/utils/request'

// 数据库配置接口类型定义
export interface DatabaseConfig {
  id: number
  name: string
  host: string
  port: number
  database: string
  username: string
  type: string
  connection_params: Record<string, any>
  psm: string
  verify_ssl: boolean
  project: number
  description: string
  is_active: boolean
  created_by: number
  created_time: string
  updated_time: string
}

// 创建数据库配置请求参数
export interface CreateDatabaseConfigData {
  name: string
  host: string
  port?: number
  database: string
  username: string
  password: string
  type?: string
  connection_params?: Record<string, any>
  psm?: string
  verify_ssl?: boolean
  project: number
  description?: string
  is_active?: boolean
}

// 更新数据库配置请求参数
export interface UpdateDatabaseConfigData {
  name?: string
  host?: string
  port?: number
  database?: string
  username?: string
  password?: string
  type?: string
  connection_params?: Record<string, any>
  psm?: string
  verify_ssl?: boolean
  description?: string
  is_active?: boolean
}

// 测试连接请求参数
export interface TestConnectionData {
  host: string
  port: number
  database: string
  user: string
  password: string
}

// 获取数据库配置列表
export function getDatabaseConfigs(projectId: number) {
  return request.get<ApiResponse<DatabaseConfig[]>>('/database-configs/', {
    params: { project: projectId }
  })
}

// 获取数据库配置详情
export function getDatabaseConfigDetail(id: number) {
  return request.get<ApiResponse<DatabaseConfig>>(`/database-configs/${id}/`)
}

// 创建数据库配置
export function createDatabaseConfig(data: CreateDatabaseConfigData) {
  return request.post<ApiResponse<DatabaseConfig>>('/database-configs/', data)
}

// 更新数据库配置
export function updateDatabaseConfig(id: number, data: UpdateDatabaseConfigData) {
  return request.put<ApiResponse<DatabaseConfig>>(`/database-configs/${id}/`, data)
}

// 删除数据库配置
export function deleteDatabaseConfig(id: number) {
  return request.delete<ApiResponse<null>>(`/database-configs/${id}/`)
}

// 测试数据库连接（已保存的配置）
export function testDatabaseConnection(id: number) {
  return request.post<ApiResponse<{ test_result: any }>>(`/database-configs/${id}/test_connection/`)
}

// 测试数据库连接（不保存配置）
export function testConnection(data: TestConnectionData) {
  return request.post<ApiResponse<{ connected: boolean, test_result: any }>>('/database-configs/test-connection/', data)
} 