export default (client) => {
  return {
    get(config = {}) {
      return client.get('/settings/', config)
    },
    update(values) {
      return client.patch('/settings/update/', values)
    },
  }
}
