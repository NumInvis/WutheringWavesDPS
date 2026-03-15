// 缓存类型
export enum CacheType {
  MEMORY = 'memory',      // 内存缓存（页面刷新丢失）
  LOCAL = 'localStorage', // 本地存储（长期）
  SESSION = 'sessionStorage' // 会话存储（标签页关闭丢失）
}

// 缓存项接口
interface CacheItem<T> {
  data: T
  timestamp: number
  expiresIn: number
}

// 内存缓存存储
const memoryCache = new Map<string, CacheItem<any>>()

/**
 * 前端缓存管理器
 * 支持内存缓存、localStorage、sessionStorage 三种类型
 */
export class CacheManager {
  private prefix: string

  constructor(prefix = 'wwdps_') {
    this.prefix = prefix
  }

  /**
   * 设置缓存
   * @param key 缓存键
   * @param data 缓存数据
   * @param expiresIn 过期时间（毫秒）
   * @param type 缓存类型
   */
  set<T>(key: string, data: T, expiresIn = 5 * 60 * 1000, type: CacheType = CacheType.MEMORY): void {
    const fullKey = this.prefix + key
    const item: CacheItem<T> = {
      data,
      timestamp: Date.now(),
      expiresIn
    }

    switch (type) {
      case CacheType.MEMORY:
        memoryCache.set(fullKey, item)
        break
      case CacheType.LOCAL:
        try {
          localStorage.setItem(fullKey, JSON.stringify(item))
        } catch (e) {
          console.warn('localStorage set failed:', e)
        }
        break
      case CacheType.SESSION:
        try {
          sessionStorage.setItem(fullKey, JSON.stringify(item))
        } catch (e) {
          console.warn('sessionStorage set failed:', e)
        }
        break
    }
  }

  /**
   * 获取缓存
   * @param key 缓存键
   * @param type 缓存类型
   * @returns 缓存数据或 null
   */
  get<T>(key: string, type: CacheType = CacheType.MEMORY): T | null {
    const fullKey = this.prefix + key
    let item: CacheItem<T> | null = null

    switch (type) {
      case CacheType.MEMORY:
        item = memoryCache.get(fullKey) || null
        break
      case CacheType.LOCAL:
        try {
          const stored = localStorage.getItem(fullKey)
          if (stored) item = JSON.parse(stored)
        } catch (e) {
          console.warn('localStorage get failed:', e)
        }
        break
      case CacheType.SESSION:
        try {
          const stored = sessionStorage.getItem(fullKey)
          if (stored) item = JSON.parse(stored)
        } catch (e) {
          console.warn('sessionStorage get failed:', e)
        }
        break
    }

    if (!item) return null

    // 检查是否过期
    if (Date.now() - item.timestamp > item.expiresIn) {
      this.remove(key, type)
      return null
    }

    return item.data
  }

  /**
   * 删除缓存
   * @param key 缓存键
   * @param type 缓存类型
   */
  remove(key: string, type: CacheType = CacheType.MEMORY): void {
    const fullKey = this.prefix + key

    switch (type) {
      case CacheType.MEMORY:
        memoryCache.delete(fullKey)
        break
      case CacheType.LOCAL:
        localStorage.removeItem(fullKey)
        break
      case CacheType.SESSION:
        sessionStorage.removeItem(fullKey)
        break
    }
  }

  /**
   * 清空所有缓存
   * @param type 缓存类型，不传则清空所有类型
   */
  clear(type?: CacheType): void {
    if (!type || type === CacheType.MEMORY) {
      memoryCache.clear()
    }
    
    if (!type || type === CacheType.LOCAL) {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key)
        }
      })
    }
    
    if (!type || type === CacheType.SESSION) {
      const keys = Object.keys(sessionStorage)
      keys.forEach(key => {
        if (key.startsWith(this.prefix)) {
          sessionStorage.removeItem(key)
        }
      })
    }
  }

  /**
   * 检查缓存是否存在且未过期
   * @param key 缓存键
   * @param type 缓存类型
   */
  has(key: string, type: CacheType = CacheType.MEMORY): boolean {
    return this.get(key, type) !== null
  }
}

// 导出单例实例
export const cache = new CacheManager()

/**
 * 缓存装饰器 - 用于自动缓存 API 请求
 * @param options 缓存配置
 */
export function withCache<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: {
    key: string | ((...args: Parameters<T>) => string)
    expiresIn?: number
    type?: CacheType
    condition?: (...args: Parameters<T>) => boolean
  }
): T {
  return (async (...args: Parameters<T>): Promise<ReturnType<T>> => {
    // 检查条件
    if (options.condition && !options.condition(...args)) {
      return fn(...args)
    }

    // 生成缓存键
    const cacheKey = typeof options.key === 'function' 
      ? options.key(...args) 
      : options.key

    // 尝试获取缓存
    const cached = cache.get<ReturnType<T>>(cacheKey, options.type)
    if (cached !== null) {
      return cached
    }

    // 执行原函数
    const result = await fn(...args)
    
    // 存储缓存
    cache.set(cacheKey, result, options.expiresIn, options.type)
    
    return result
  }) as T
}

/**
 * 智能缓存策略 - 根据数据类型自动选择缓存方式
 */
export const cacheStrategies = {
  // 用户数据 - 会话级缓存
  user: {
    type: CacheType.SESSION,
    expiresIn: 30 * 60 * 1000 // 30分钟
  },
  // 表格列表 - 内存缓存，短时间
  sheets: {
    type: CacheType.MEMORY,
    expiresIn: 2 * 60 * 1000 // 2分钟
  },
  // 分类数据 - 本地缓存，较长时间
  categories: {
    type: CacheType.LOCAL,
    expiresIn: 60 * 60 * 1000 // 1小时
  },
  // 表格详情 - 内存缓存
  sheetDetail: {
    type: CacheType.MEMORY,
    expiresIn: 5 * 60 * 1000 // 5分钟
  }
}
