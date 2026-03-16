import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { handleError, setupGlobalErrorHandler } from './errorHandler'

const API_BASE_URL = '/WutheringWavesDPS/api'

interface ApiResponse<T = any> {
  message?: string
  data?: T
  [key: string]: any
}

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
    this.loadToken()
    
    // 设置全局错误处理
    setupGlobalErrorHandler()
  }

  private loadToken() {
    this.token = localStorage.getItem('token')
    if (this.token) {
      this.setAuthToken(this.token)
    }
  }

  private setAuthToken(token: string) {
    this.token = token
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  private removeAuthToken() {
    this.token = null
    delete this.client.defaults.headers.common['Authorization']
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now()
          }
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      (error) => {
        const url = error.config?.url || ''
        const isAuthEndpoint = url.includes('auth/login') || url.includes('auth/register')
        
        if (!isAuthEndpoint) {
          handleError(error)
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }

  async login(username: string, password: string) {
    try {
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)

      console.log('[API] Attempting login for:', username)

      const response = await this.client.post('auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      const { access_token } = response.data
      this.setAuthToken(access_token)
      localStorage.setItem('token', access_token)

      console.log('[API] Login successful')
      return response.data
    } catch (error: any) {
      console.error('[API] Login error:', error.response?.data || error.message)
      throw error
    }
  }

  async register(data: {
    username: string
    password: string
    display_name?: string
    avatar_url?: string
    bio?: string
  }) {
    const response = await this.client.post('/auth/register', data)
    return response.data
  }

  logout() {
    this.removeAuthToken()
    localStorage.removeItem('token')
  }

  isAuthenticated(): boolean {
    return !!this.token
  }
}

export default new ApiClient()
