export interface ApiValidator {
  eq: [string, string]
  contains: [string, string]
  startswith: [string, string]
  endswith: [string, string]
  regex_match: [string, string]
  length_equals: [string, string]
  greater_than: [string, string]
  less_than: [string, string]
} 