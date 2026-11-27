export default (client) => {
  return {
    get(config = {}) {
      return client.get('/settings/', config)
    },
    update(values) {
      return client.patch('/settings/update/', values)
    },
    restoreBackup(id, confirm) {
      return client.post('/settings/backups/restore/', { id, confirm })
    },
    getBackupRestoreStatus(token) {
      return client.get(`/settings/backups/restore/${token}/status/`)
    },
  }
}
