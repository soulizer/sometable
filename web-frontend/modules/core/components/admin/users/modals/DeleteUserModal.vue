<template>
  <Modal ref="modal">
    <h2 class="box__title">{{ $t('deleteUserModal.title', user) }}</h2>
    <Error :error="error"></Error>
    <div>
      <i18n-t scope="global" keypath="deleteUserModal.confirmation" tag="p">
        <template #name>
          <strong class="user-admin-delete__strong">{{ user.username }}</strong>
        </template>
      </i18n-t>
      <p>
        {{ $t('deleteUserModal.comment1') }}
      </p>
      <p>
        {{ $t('deleteUserModal.comment2') }}
      </p>
      <FormGroup
        :label="$t('deleteUserModal.confirmLabel')"
        :helper-text="$t('deleteUserModal.confirmHelp')"
        class="margin-bottom-2"
      >
        <FormInput
          v-model="confirmation"
          :placeholder="user.username"
          size="large"
        />
      </FormGroup>
      <div class="actions">
        <div class="align-right">
          <Button
            type="danger"
            size="large"
            full-width
            :disabled="loading || confirmation !== user.username"
            :loading="loading"
            @click.prevent="deleteUser()"
          >
            {{ $t('deleteUserModal.delete', user) }}</Button
          >
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import UserAdminService from '@baserow/modules/core/services/admin/users'

export default {
  name: 'DeleteUserModal',
  mixins: [modal, error],
  props: {
    user: {
      type: Object,
      required: true,
    },
  },
  emits: ['delete-user'],
  data() {
    return {
      loading: false,
      confirmation: '',
    }
  },
  methods: {
    show() {
      this.confirmation = ''
      return modal.methods.show.call(this)
    },
    async deleteUser() {
      this.hideError()
      this.loading = true

      try {
        await UserAdminService(this.$client).delete(this.user.id)
        this.$emit('delete-user', this.user.id)
        this.hide()
      } catch (error) {
        this.handleError(error, 'application')
      }

      this.loading = false
    },
  },
}
</script>
