import request from '@/utils/request'
import type { ApiResponse } from '@/utils/request'

// 仪表盘数据接口
export interface DashboardSummary {
  total_projects: number
  total_interfaces: number
  total_testcases: number
  total_tasks: number
  success_rate: number
  recent_tasks: RecentTask[]
}

// 最近任务接口
export interface RecentTask {
  id: number
  task_suite__name: string
  status: string
  created_time: string
  success_count: number
  total_count: number
  success_rate: number
}

/**
 * 获取仪表盘摘要数据
 * @returns Promise<ApiResponse<DashboardSummary>>
 */
export function getDashboardSummary(): Promise<ApiResponse<DashboardSummary>> {
  return request.get('/dashboard/summary/')
} 