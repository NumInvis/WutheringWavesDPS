import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTH = 'AUTH',
  PERMISSION = 'PERMISSION',
  VALIDATION = 'VALIDATION',
  NOT_FOUND = 'NOT_FOUND',
  SERVER = 'SERVER',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}

// 错误信息接口
export interface ErrorInfo {
  type: ErrorType
  message: string
  detail?: string
  code?: number
  timestamp: number
}

// 错误日志记录
class ErrorLogger {
  private maxLogs = 100
  private logs: ErrorInfo[] = []

  log(error: ErrorInfo) {
    this.logs.unshift(error)
    if (this.logs.length > this.maxLogs) {
      this.logs.pop()
    }
    
    // 开发环境输出到控制台
    if (import.meta.env.DEV) {
      console.error('[API Error]', error)
    }
    
    // 生产环境可以发送到监控服务
    if (import.meta.env.PROD && error.type === ErrorType.SERVER) {
      // TODO: 发送到 Sentry 等监控服务
      this.reportToMonitoring(error)
    }
  }

  private reportToMonitoring(error: ErrorInfo) {
    // 实现错误上报逻辑
    console.warn('Reporting to monitoring:', error)
  }

  getLogs(): ErrorInfo[] {
    return [...this.logs]
  }

  clear() {
    this.logs = []
  }
}

export const errorLogger = new ErrorLogger()

// 错误分类函数
export function classifyError(error: AxiosError): ErrorType {
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return ErrorType.TIMEOUT
    }
    return ErrorType.NETWORK
  }

  const status = error.response.status

  switch (status) {
    case 401:
      return ErrorType.AUTH
    case 403:
      return ErrorType.PERMISSION
    case 404:
      return ErrorType.NOT_FOUND
    case 422:
    case 400:
      return ErrorType.VALIDATION
    case 500:
    case 502:
    case 503:
    case 504:
      return ErrorType.SERVER
    default:
      return ErrorType.UNKNOWN
  }
}

// 用户友好的错误消息
const errorMessages: Record<ErrorType, string> = {
  [ErrorType.NETWORK]: '网络连接失败，请检查网络设置',
  [ErrorType.AUTH]: '登录已过期，请重新登录',
  [ErrorType.PERMISSION]: '没有权限执行此操作',
  [ErrorType.VALIDATION]: '请求参数有误，请检查输入',
  [ErrorType.NOT_FOUND]: '请求的资源不存在',
  [ErrorType.SERVER]: '服务器繁忙，请稍后重试',
  [ErrorType.TIMEOUT]: '请求超时，请稍后重试',
  [ErrorType.UNKNOWN]: '操作失败，请稍后重试'
}

// 错误处理器
export function handleError(error: AxiosError, options?: {
  showNotification?: boolean
  showMessage?: boolean
  redirect?: string
}): ErrorInfo {
  const { showNotification = false, showMessage = false, redirect } = options || {}
  
  const type = classifyError(error)
  const status = error.response?.status
  const detail = (error.response?.data as any)?.detail || error.message
  
  const errorInfo: ErrorInfo = {
    type,
    message: errorMessages[type],
    detail,
    code: status,
    timestamp: Date.now()
  }

  // 记录错误
  errorLogger.log(errorInfo)

  // 显示错误提示（默认不显示，减少用户看到的报错）
  if (showMessage) {
    if (type === ErrorType.SERVER || type === ErrorType.NETWORK) {
      // 严重错误使用通知
      ElNotification.error({
        title: '系统错误',
        message: errorInfo.message,
        duration: 5000
      })
    } else {
      // 一般错误使用消息
      ElMessage.error({ message: errorInfo.message, duration: 2000 })
    }
  }

  // 认证错误特殊处理
  if (type === ErrorType.AUTH) {
    // 清除本地认证状态
    localStorage.removeItem('token')
    
    // 延迟跳转，让用户看到提示
    if (redirect !== false) {
      setTimeout(() => {
        window.location.href = '/WutheringWavesDPS/login'
      }, 1500)
    }
  }

  return errorInfo
}

// 全局错误边界处理
export function setupGlobalErrorHandler() {
  window.onerror = (message, source, lineno, colno, error) => {
    errorLogger.log({
      type: ErrorType.UNKNOWN,
      message: String(message),
      detail: `Source: ${source}, Line: ${lineno}, Col: ${colno}`,
      timestamp: Date.now()
    })
    return false
  }

  window.onunhandledrejection = (event) => {
    errorLogger.log({
      type: ErrorType.UNKNOWN,
      message: 'Unhandled Promise Rejection',
      detail: String(event.reason),
      timestamp: Date.now()
    })
  }
}
