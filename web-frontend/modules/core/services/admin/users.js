import baseService from '@baserow/modules/core/crudTable/baseService'

export default (client) => {
  return Object.assign(baseService(client, '/admin/users/'), {
    create(values) {
      return client.post('/admin/users/', values)
    },
    update(userId, values) {
      return client.patch(`/admin/users/${userId}/`, values)
    },
    delete(userId) {
      return client.delete(`/admin/users/${userId}/`)
    },
    bulkUpdate(userIds, values) {
      return Promise.allSettled(
        userIds.map((userId) => client.patch(`/admin/users/${userId}/`, values))
      )
    },
    bulkDelete(userIds) {
      return Promise.allSettled(
        userIds.map((userId) => client.delete(`/admin/users/${userId}/`))
      )
    },
    disableTwoFactorAuth(userId) {
      return client.delete(`/admin/users/${userId}/two-factor-auth/`)
    },
    impersonate(userId) {
      return client.post(`/admin/users/impersonate/`, {
        user: userId,
      })
    },
  })
}
