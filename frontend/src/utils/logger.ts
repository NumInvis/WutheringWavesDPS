/**
 * 日志工具 - 捕获应用日志并发送到后端
 */

interface LogEntry {
  timestamp: number
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
  details?: any
}

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 500
  private originalConsole = {
    log: console.log,
    warn: console.warn,
    error: console.error
  }

  constructor() {
    this.interceptConsole()
    this.loadStoredLogs()
  }

  private interceptConsole() {
    // 拦截 console.log
    console.log = (...args: any[]) => {
      this.originalConsole.log(...args)
      this.addLog('info', this.formatArgs(args))
    }

    // 拦截 console.warn
    console.warn = (...args: any[]) => {
      this.originalConsole.warn(...args)
      this.addLog('warn', this.formatArgs(args))
    }

    // 拦截 console.error
    console.error = (...args: any[]) => {
      this.originalConsole.error(...args)
      this.addLog('error', this.formatArgs(args))
    }
  }

  private formatArgs(args: any[]): string {
    return args.map(arg => {
      if (typeof arg === 'object') {
        try {
          return JSON.stringify(arg)
        } catch {
          return String(arg)
        }
      }
      return String(arg)
    }).join(' ')
  }

  private addLog(level: LogEntry['level'], message: string, details?: any) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      level,
      message: message.substring(0, 500), // 限制长度
      details
    }

    this.logs.push(entry)

    // 限制日志数量
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs)
    }

    // 保存到 localStorage
    this.saveLogs()
  }

  private saveLogs() {
    try {
      localStorage.setItem('app_logs', JSON.stringify(this.logs))
    } catch (e) {
      // localStorage 可能已满
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

  // 公共方法
  info(message: string, details?: any) {
    this.addLog('info', message, details)
  }

  warn(message: string, details?: any) {
    this.addLog('warn', message, details)
  }

  error(message: string, details?: any) {
    this.addLog('error', message, details)
  }

  debug(message: string, details?: any) {
    this.addLog('debug', message, details)
  }

  getLogs(): LogEntry[] {
    return [...this.logs]
  }

  clearLogs() {
    this.logs = []
    localStorage.removeItem('app_logs')
  }
}

// 导出单例
export const logger = new Logger()
export default logger
