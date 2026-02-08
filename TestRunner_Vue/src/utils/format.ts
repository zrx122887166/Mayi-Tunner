/**
 * 格式化日期时间
 * @param dateStr ISO格式的日期字符串
 * @returns 格式化后的日期时间字符串
 */
export function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

/**
 * 格式化为相对时间（如：刚刚、5分钟前、昨天等）
 * @param dateStr 日期字符串
 * @returns 格式化后的相对时间字符串
 */
export function formatRelativeTime(dateStr?: string): string {
  if (!dateStr) return '-'
  
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 时间差转换为各种单位
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)
  
  // 根据时间差返回相应的格式
  if (seconds < 10) {
    return '刚刚'
  } else if (seconds < 60) {
    return `${seconds}秒前`
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days === 2) {
    return '前天'
  } else if (days < 30) {
    return `${days}天前`
  } else if (months < 12) {
    return `${months}个月前`
  } else if (years === 1) {
    return '1年前'
  } else if (years > 1) {
    return `${years}年前`
  }
  
  // 如果是未来时间，显示具体日期
  return date.toLocaleDateString('zh-CN')
}

/**
 * 格式化为简短日期时间（如：09-13 14:00）
 * @param dateStr 日期字符串
 * @returns 格式化后的简短日期时间字符串
 */
export function formatShortDateTime(dateStr?: string): string {
  if (!dateStr) return '-'
  
  const date = new Date(dateStr)
  const now = new Date()
  
  // 获取年月日
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  
  // 如果是今年，不显示年份
  if (year === now.getFullYear()) {
    return `${month}-${day} ${hours}:${minutes}`
  }
  
  // 不是今年，显示完整年份
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

/**
 * 格式化时长（秒）
 * @param duration 时长（秒）
 * @returns 格式化后的时长字符串
 */
export function formatDuration(duration?: number): string {
  if (!duration && duration !== 0) return '-'
  
  if (duration < 1) {
    return `${Math.round(duration * 1000)}ms`
  }

  const hours = Math.floor(duration / 3600)
  const minutes = Math.floor((duration % 3600) / 60)
  const seconds = Math.floor(duration % 60)
  const parts = []

  if (hours > 0) {
    parts.push(`${hours}小时`)
  }
  if (minutes > 0) {
    parts.push(`${minutes}分钟`)
  }
  if (seconds > 0 || parts.length === 0) {
    parts.push(`${seconds}秒`)
  }

  return parts.join(' ')
} 