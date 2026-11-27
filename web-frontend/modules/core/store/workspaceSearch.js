import WorkspaceSearchService from '@baserow/modules/core/services/workspaceSearch'

export const state = () => ({
  searchTerm: '',
  results: [],
  loading: false,
  globalResults: [],
  globalLoading: false,
  globalRequestId: 0,
})

export const mutations = {
  SET_SEARCH_TERM(state, term) {
    state.searchTerm = term
  },

  SET_RESULTS(state, results) {
    state.results = results
  },

  SET_LOADING(state, loading) {
    state.loading = loading
  },

  CLEAR_RESULTS(state) {
    state.results = []
  },

  SET_GLOBAL_REQUEST_ID(state, requestId) {
    state.globalRequestId = requestId
  },

  SET_GLOBAL_RESULTS(state, { results, requestId }) {
    if (requestId !== null && requestId !== state.globalRequestId) {
      return
    }
    state.globalResults = results
  },

  SET_GLOBAL_LOADING(state, loading) {
    state.globalLoading = loading
  },

  CLEAR_GLOBAL_RESULTS(state) {
    state.globalResults = []
    state.globalLoading = false
  },
}

export const actions = {
  async search(
    { commit, state },
    {
      workspaceId,
      searchTerm,
      types = null,
      limit = 20,
      offset = 0,
      append = false,
    }
  ) {
    commit('SET_LOADING', true)
    commit('SET_SEARCH_TERM', searchTerm)

    try {
      const params = {
        query: searchTerm,
        limit,
        offset,
      }

      if (types && types.length > 0) {
        params.types = types
      }

      const { data } = await WorkspaceSearchService(this.$client).search(
        workspaceId,
        params
      )

      if (append) {
        const existing = Array.isArray(state.results) ? state.results : []
        const incoming = Array.isArray(data.results) ? data.results : []
        commit('SET_RESULTS', existing.concat(incoming))
      } else {
        commit('SET_RESULTS', Array.isArray(data.results) ? data.results : [])
      }

      return data
    } catch (error) {
      commit('SET_RESULTS', [])
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  clearSearch({ commit }) {
    commit('SET_SEARCH_TERM', '')
    commit('CLEAR_RESULTS')
  },

  async searchGlobal(
    { commit, state },
    { searchTerm, limit = 20, offset = 0, signal = null, requestId = null }
  ) {
    if (requestId !== null) {
      commit('SET_GLOBAL_REQUEST_ID', requestId)
    }
    commit('SET_GLOBAL_LOADING', true)

    try {
      const { data } = await WorkspaceSearchService(this.$client).searchGlobal(
        { query: searchTerm, limit, offset },
        signal
      )
      const results = Array.isArray(data.results) ? data.results : []
      commit('SET_GLOBAL_RESULTS', { results, requestId })
      return data
    } catch (error) {
      if (requestId === null || requestId === state.globalRequestId) {
        commit('CLEAR_GLOBAL_RESULTS')
      }
      throw error
    } finally {
      if (requestId === null || requestId === state.globalRequestId) {
        commit('SET_GLOBAL_LOADING', false)
      }
    }
  },

  clearGlobalSearch({ commit, state }) {
    commit('SET_GLOBAL_REQUEST_ID', state.globalRequestId + 1)
    commit('CLEAR_GLOBAL_RESULTS')
  },
}

export const getters = {
  hasResults: (state) =>
    Array.isArray(state.results) && state.results.length > 0,

  totalResultCount: (state) => {
    return Array.isArray(state.results) ? state.results.length : 0
  },

  isLoading: (state) => state.loading,

  getResultsByType: (state) => (type) => {
    if (!Array.isArray(state.results)) return []
    return state.results.filter((r) => r.type === type)
  },

  getAllResults: (state) => {
    return Array.isArray(state.results) ? state.results : []
  },

  globalResults: (state) => {
    return Array.isArray(state.globalResults) ? state.globalResults : []
  },

  isGlobalLoading: (state) => state.globalLoading,
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
