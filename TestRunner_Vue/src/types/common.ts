/**
 * 分页参数接口
 */
export interface PaginationParams {
  /** 当前页码 */
  page: number
  /** 每页条数 */
  page_size: number
}

/**
 * 分页响应接口
 */
export interface PaginationResponse<T> {
  /** 总条数 */
  count: number
  /** 下一页URL */
  next: string | null
  /** 上一页URL */
  previous: string | null
  /** 结果列表 */
  results: T[]
}

/**
 * API响应接口
 */
export interface ApiResponse<T = any> {
  /** 状态 */
  status: string
  /** 状态码 */
  code: number
  /** 消息 */
  message: string
  /** 数据 */
  data: T
} 