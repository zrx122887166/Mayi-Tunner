import request from '../utils/request'
import type { ApiResponse, PaginatedResponse } from '../utils/request'

export interface GlobalHeader {
  id: number
  name: string
  value: string
  description: string
  project: number
  is_enabled: boolean
  created_by: number
  created_by_name: string
  created_time: string
  updated_time: string
}

export interface CreateGlobalHeaderData {
  name: string
  value: string
  description: string
  project: number
  is_enabled: boolean
}

export function getGlobalHeaders(projectId: number): Promise<ApiResponse<PaginatedResponse<GlobalHeader>>> {
  return request.get('/environments/global-headers/', {
    params: {
      project_id: projectId
    }
  })
}

export function createGlobalHeader(data: CreateGlobalHeaderData): Promise<ApiResponse<GlobalHeader>> {
  return request.post('/environments/global-headers/', data)
}

export function updateGlobalHeader(id: number, data: CreateGlobalHeaderData): Promise<ApiResponse<GlobalHeader>> {
  return request.put(`/environments/global-headers/${id}/`, data)
}

export function deleteGlobalHeader(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/environments/global-headers/${id}/`)
} 