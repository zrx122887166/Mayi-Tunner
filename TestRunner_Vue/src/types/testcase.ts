export interface TestCaseConfig {
  export: string[]
  verify: boolean
  base_url: string
  variables: string
  parameters: string
}

export interface TestCaseBasicInfo {
  id?: number
  name: string
  description: string
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  group: number | null
  tags: number[]
  config: TestCaseConfig
}

export interface Variable {
  key: string
  value: string
  type: 'static' | 'function'
  functionId?: number
}

export interface StepVariable {
  key: string
  value: string
  from: string
}

export interface Tag {
  id: number
  name: string
  color: string
  project: number
}

export interface TagStatistics {
  id: number
  usage_count: number
}

export interface Group {
  id: number
  name: string
  parent: number | null
  project: number
  children?: Group[]
  created_time: string
} 