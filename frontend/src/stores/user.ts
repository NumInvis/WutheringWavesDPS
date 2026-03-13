import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

interface User {
  id: string
  username: string
  email: string
  display_name: string
  avatar_url?: string
  bio?: string
  is_active: boolean
  is_verified: boolean
  role: string
  created_at: string
  updated_at: string
  last_login_at?: string
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const username = computed(() => user.value?.username || '')
  const displayName = computed(() => user.value?.display_name || '')

  async function fetchCurrentUser() {
    if (!api.isAuthenticated()) return

    loading.value = true
    try {
      const response = await api.get('/auth/me')
      user.value = response as unknown as User
    } catch (error) {
      console.error('Failed to fetch user:', error)
      user.value = null
      api.logout()
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      await api.login(username, password)
      await fetchCurrentUser()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(data: {
    username: string
    email: string
    password: string
    display_name?: string
    avatar_url?: string
    bio?: string
  }) {
    loading.value = true
    try {
      await api.register(data)
      await login(data.username, data.password)
      return true
    } catch (error) {
      console.error('Registration failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    user.value = null
    api.logout()
  }

  function initialize() {
    fetchCurrentUser()
  }

  return {
    user,
    loading,
    isAuthenticated,
    username,
    displayName,
    fetchCurrentUser,
    login,
    register,
    logout,
    initialize
  }
})
