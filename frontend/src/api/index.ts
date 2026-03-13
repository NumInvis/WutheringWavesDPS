import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

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
        if (error.response) {
          const { status, data } = error.response
          
          if (status === 401) {
            this.removeAuthToken()
            localStorage.removeItem('token')
            ElMessage.error('登录已过期，请重新登录')
            window.location.href = '/login'
          } else if (status === 403) {
            ElMessage.error(data.detail || '没有权限执行此操作')
          } else if (status === 404) {
            ElMessage.error(data.detail || '请求的资源不存在')
          } else if (status >= 500) {
            ElMessage.error('服务器错误，请稍后重试')
          } else {
            ElMessage.error(data.detail || '请求失败')
          }
        } else if (error.request) {
          ElMessage.error('网络错误，请检查网络连接')
        } else {
          ElMessage.error('请求配置错误')
        }

        return Promise.reject(error)
      }
    )
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.get<ApiResponse<T>>(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put<ApiResponse<T>>(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete<ApiResponse<T>>(url, config)
    return response.data
  }

  async login(username: string, password: string) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await this.client.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    const { access_token } = response.data
    this.setAuthToken(access_token)
    localStorage.setItem('token', access_token)

    return response.data
  }

  async register(data: {
    username: string
    email: string
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
