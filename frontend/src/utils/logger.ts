/**
 * 日志工具 - 捕获应用日志并发送到后端
 */

interface LogEntry {
  timestamp: number
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  details?: any
  source?: string
}

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 1000
  private originalConsole = {
    log: console.log,
    warn: console.warn,
    error: console.error,
    debug: console.debug
  }
  private listeners: ((log: LogEntry) => void)[] = []

  constructor() {
    this.interceptConsole()
    this.interceptNetworkErrors()
    this.loadStoredLogs()
    this.logSystemInfo()
  }

  private logSystemInfo() {
    this.info('系统信息', {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      screenSize: `${window.screen.width}x${window.screen.height}`,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      timestamp: new Date().toISOString()
    })
  }

  private interceptConsole() {
    // 拦截 console.log
    console.log = (...args: any[]) => {
      this.originalConsole.log(...args)
      this.addLog('info', this.formatArgs(args), undefined, 'console')
    }

    // 拦截 console.warn
    console.warn = (...args: any[]) => {
      this.originalConsole.warn(...args)
      this.addLog('warn', this.formatArgs(args), undefined, 'console')
    }

    // 拦截 console.error
    console.error = (...args: any[]) => {
      this.originalConsole.error(...args)
      this.addLog('error', this.formatArgs(args), undefined, 'console')
    }

    // 拦截 console.debug
    console.debug = (...args: any[]) => {
      this.originalConsole.debug(...args)
      this.addLog('debug', this.formatArgs(args), undefined, 'console')
    }
  }

  private interceptNetworkErrors() {
    // 捕获未处理的Promise错误
    window.addEventListener('unhandledrejection', (event) => {
      this.error('未处理的Promise错误', {
        reason: event.reason?.message || event.reason,
        stack: event.reason?.stack
      }, 'unhandledrejection')
    })

    // 捕获全局错误
    window.addEventListener('error', (event) => {
      this.error('全局错误', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error?.stack
      }, 'global')
    })

    // 捕获资源加载错误
    window.addEventListener('error', (event) => {
      if (event.target && (event.target as any).src) {
        this.error('资源加载失败', {
          src: (event.target as any).src,
          tagName: (event.target as any).tagName
        }, 'resource')
      }
    }, true)
  }

  private formatArgs(args: any[]): string {
    return args.map(arg => {
      if (arg === null) return 'null'
      if (arg === undefined) return 'undefined'
      if (typeof arg === 'object') {
        try {
          return JSON.stringify(arg).substring(0, 1000)
        } catch {
          return String(arg)
        }
      }
      return String(arg)
    }).join(' ')
  }

  private addLog(level: LogEntry['level'], message: string, details?: any, source?: string) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      level,
      message: message.substring(0, 1000),
      details,
      source
    }

    this.logs.push(entry)

    // 限制日志数量
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs)
    }

    // 保存到 localStorage
    this.saveLogs()

    // 通知监听器
    this.listeners.forEach(listener => {
      try {
        listener(entry)
      } catch (e) {
        // 忽略监听器错误
      }
    })
  }

  private saveLogs() {
    try {
      localStorage.setItem('app_logs', JSON.stringify(this.logs))
    } catch (e) {
      // localStorage 可能已满，删除一半日志
      this.logs = this.logs.slice(-this.maxLogs / 2)
      try {
        localStorage.setItem('app_logs', JSON.stringify(this.logs))
      } catch (e2) {
        // 仍然失败则清空
        this.logs = []
      }
    }
  }

  private loadStoredLogs() {
    try {
      const stored = localStorage.getItem('app_logs')
      if (stored) {
        this.logs = JSON.parse(stored)
      }
    } catch (e) {
      this.logs = []
    }
  }

  // 添加监听器
  onLog(callback: (log: LogEntry) => void) {
    this.listeners.push(callback)
    return () => {
      const index = this.listeners.indexOf(callback)
      if (index > -1) {
        this.listeners.splice(index, 1)
      }
    }
  }

  // 公共方法
  info(message: string, details?: any, source?: string) {
    this.addLog('info', message, details, source)
  }

  warn(message: string, details?: any, source?: string) {
    this.addLog('warn', message, details, source)
  }

  error(message: string, details?: any, source?: string) {
    this.addLog('error', message, details, source)
  }

  debug(message: string, details?: any, source?: string) {
    this.addLog('debug', message, details, source)
  }

  getLogs(): LogEntry[] {
    return [...this.logs]
  }

  getRecentLogs(count: number = 50): LogEntry[] {
    return this.logs.slice(-count)
  }

  clearLogs() {
    this.logs = []
    localStorage.removeItem('app_logs')
    this.info('日志已清空', undefined, 'logger')
  }
}

// 导出单例
export const logger = new Logger()
export default logger
