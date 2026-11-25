<template>
  <Modal ref="modal" @hidden="$refs.form && $refs.form?.reset()">
    <h2 class="box__title">{{ $t('createUserModal.title') }}</h2>
    <Error :error="error"></Error>
    <CreateUserForm
      ref="form"
      :loading="loading"
      @submitted="createUser"
    ></CreateUserForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import UserAdminService from '@baserow/modules/core/services/admin/users'
import CreateUserForm from '@baserow/modules/core/components/admin/users/forms/CreateUserForm'

export default {
  name: 'CreateUserModal',
  components: { CreateUserForm },
  mixins: [modal, error],
  emits: ['created'],
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async createUser(values) {
      this.loading = true
      this.hideError()
      try {
        const { data: user } = await UserAdminService(this.$client).create(values)
        this.$emit('created', user)
        this.loading = false
        this.hide()
      } catch (error) {
        this.loading = false
        this.handleError(error, 'application')
      }
    },
  },
}
</script>
