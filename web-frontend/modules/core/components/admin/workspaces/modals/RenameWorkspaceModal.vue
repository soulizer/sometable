<template>
  <Modal ref="modal">
    <h2 class="box__title">{{ $t('renameWorkspaceModal.title') }}</h2>
    <FormGroup :label="$t('renameWorkspaceModal.name')" required>
      <FormInput
        v-model="name"
        size="large"
        :error="error"
        @keyup.enter.prevent="submit"
      />
    </FormGroup>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="actions">
      <div class="align-right">
        <Button @click="hide">{{ $t('action.cancel') }}</Button>
        <Button
          type="primary"
          :loading="loading"
          :disabled="!name.trim() || loading"
          @click="submit"
        >
          {{ $t('action.save') }}
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import WorkspacesAdminService from '@baserow/modules/core/services/admin/workspaces'

export default {
  name: 'RenameWorkspaceModal',
  mixins: [modal, error],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  emits: ['updated'],
  data() {
    return {
      name: '',
      loading: false,
    }
  },
  methods: {
    show() {
      this.name = this.workspace.name || ''
      this.hideError()
      return modal.methods.show.call(this)
    },
    async submit() {
      const name = this.name.trim()
      if (!name || this.loading) return
      this.loading = true
      this.hideError()
      try {
        const { data } = await WorkspacesAdminService(this.$client).update(
          this.workspace.id,
          { name }
        )
        this.$emit('updated', data)
        this.hide()
      } catch (e) {
        this.handleError(e, 'settings')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
