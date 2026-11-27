import baseService from '@baserow/modules/core/crudTable/baseService'

export const ADMIN_WORKSPACE_OPTIONS_URL = '/admin/workspaces/options/'

export const ADMIN_WORKSPACE_MEMBERS_URL = (workspaceId) =>
  `/admin/workspaces/${workspaceId}/members/`

export const fetchWorkspaceOptions = (client, page, search) =>
  baseService(client, ADMIN_WORKSPACE_OPTIONS_URL).fetch(
    ADMIN_WORKSPACE_OPTIONS_URL,
    page,
    search,
    [],
    {}
  )

export default (client) => {
  return Object.assign(baseService(client, '/admin/workspaces/'), {
    update(workspaceId, values) {
      return client.patch(`/admin/workspaces/${workspaceId}/`, values)
    },
    delete(workspaceId) {
      return client.delete(`/admin/workspaces/${workspaceId}/`)
    },
    listMembers(workspaceId, page, search, sorts, filters = {}) {
      const url = ADMIN_WORKSPACE_MEMBERS_URL(workspaceId)
      return baseService(client, url).fetch(
        url,
        page,
        search,
        sorts,
        filters,
        {}
      )
    },
    updateMember(workspaceId, memberId, values) {
      return client.patch(
        `${ADMIN_WORKSPACE_MEMBERS_URL(workspaceId)}${memberId}/`,
        values
      )
    },
    deleteMember(workspaceId, memberId) {
      return client.delete(
        `${ADMIN_WORKSPACE_MEMBERS_URL(workspaceId)}${memberId}/`
      )
    },
    exportAsync(workspaceId, values = {}) {
      return client.post(
        `/admin/workspaces/${workspaceId}/export/async/`,
        values
      )
    },
  })
}
