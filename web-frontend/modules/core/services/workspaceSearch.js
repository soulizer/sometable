export default (client) => {
  return {
    /**
     * Performs a workspace search across all searchable content types in a workspace.
     */
    search(workspaceId, params) {
      return client.get(`/search/workspace/${workspaceId}/`, { params })
    },

    /**
     * Searches across every workspace the authenticated user can access.
     */
    searchGlobal(params, signal = null) {
      const config = { params }
      if (signal) {
        config.signal = signal
      }
      return client.get('/search/', config)
    },
  }
}
