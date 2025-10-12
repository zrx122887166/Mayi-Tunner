import request from '@/utils/request'
import type { PaginationParams } from '@/types/common'

export interface TestReport {
  id: number
  name: string
  status: string
  success_count: number
  fail_count: number
  error_count: number
  duration: number
  start_time: string
  testcase_name: string
  success_rate: number
  environment: number
  executed_by: number
  environment_name: string
  executed_by_name: string
}

export interface TestReportDetail extends TestReport {
  summary: {
    name: string
    success: boolean
    time: {
      start_at: string
      duration: number
    }
    in_out: {
      config_vars: any
      export_vars: any
    }
    log: string
  }
  details: Array<{
    id: number
    step_name: string
    success: boolean
    elapsed: number
    request: {
      method: string
      url: string
      headers: any
      body: any
    }
    response: {
      status_code: number
      headers: any
      body: any
      content_size: number
      response_time: number
    }
    validators: string[]
    extracted_variables: Record<string, any>
    attachment: string
  }>
}

export interface TestReportListParams extends PaginationParams {
  status?: string
  testcase?: number
  environment?: number
  executed_by?: number
  search?: string
  ordering?: string
  project?: number
}

export function getTestReports(params: TestReportListParams) {
  return request({
    url: '/testcases/reports/',
    method: 'get',
    params,
  })
}

export function getTestReportDetail(id: number) {
  return request({
    url: `/testcases/reports/${id}/`,
    method: 'get',
  })
} 