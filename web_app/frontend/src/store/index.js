import { createStore } from 'vuex'
import axios from 'axios'

export default createStore({
  state: {
    // 统计数据
    stats: null,
    
    // 筛选选项
    filters: null,
    
    // 角色列表
    characters: [],
    
    // 当前角色
    currentCharacter: null,
    
    // 动作列表
    actions: [],
    
    // 声骸列表
    echoes: [],
    
    // 加载状态
    loading: false
  },
  
  mutations: {
    SET_STATS(state, stats) {
      state.stats = stats
    },
    SET_FILTERS(state, filters) {
      state.filters = filters
    },
    SET_CHARACTERS(state, characters) {
      state.characters = characters
    },
    SET_CURRENT_CHARACTER(state, character) {
      state.currentCharacter = character
    },
    SET_ACTIONS(state, actions) {
      state.actions = actions
    },
    SET_ECHOES(state, echoes) {
      state.echoes = echoes
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    }
  },
  
  actions: {
    // 获取统计数据
    async fetchStats({ commit }) {
      try {
        const response = await axios.get('/api/stats')
        if (response.data.success) {
          commit('SET_STATS', response.data.data)
        }
      } catch (error) {
        console.error('获取统计数据失败:', error)
      }
    },
    
    // 获取筛选选项
    async fetchFilters({ commit }) {
      try {
        const response = await axios.get('/api/filters')
        if (response.data.success) {
          commit('SET_FILTERS', response.data.data)
        }
      } catch (error) {
        console.error('获取筛选选项失败:', error)
      }
    },
    
    // 获取角色列表
    async fetchCharacters({ commit }, params = {}) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get('/api/characters', { params })
        if (response.data.success) {
          commit('SET_CHARACTERS', response.data.data)
        }
      } catch (error) {
        console.error('获取角色列表失败:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 获取角色详情
    async fetchCharacterDetail({ commit }, id) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get(`/api/characters/${id}`)
        if (response.data.success) {
          commit('SET_CURRENT_CHARACTER', response.data.data)
        }
      } catch (error) {
        console.error('获取角色详情失败:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 获取动作列表
    async fetchActions({ commit }, params = {}) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get('/api/actions', { params })
        if (response.data.success) {
          commit('SET_ACTIONS', response.data.data)
        }
      } catch (error) {
        console.error('获取动作列表失败:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 获取声骸列表
    async fetchEchoes({ commit }, params = {}) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get('/api/echoes', { params })
        if (response.data.success) {
          commit('SET_ECHOES', response.data.data)
        }
      } catch (error) {
        console.error('获取声骸列表失败:', error)
      } finally {
        commit('SET_LOADING', false)
      }
    }
  }
})
