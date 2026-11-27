<template>
  <Context ref="context" overflow-scroll max-height-if-outside-viewport>
    <template v-if="Object.keys(workspace).length > 0">
      <div class="context__menu-title">
        {{ workspace.name }} ({{ workspace.id }})
      </div>
      <ul class="context__menu">
        <li class="context__menu-item">
          <a class="context__menu-item-link" @click.prevent="showRenameModal">
            <i class="context__menu-item-icon iconoir-edit-pencil"></i>
            {{ $t('editWorkspaceContext.rename') }}
          </a>
        </li>
        <li class="context__menu-item">
          <a class="context__menu-item-link" @click.prevent="showMembersModal">
            <i class="context__menu-item-icon iconoir-group"></i>
            {{ $t('editWorkspaceContext.members') }}
          </a>
        </li>
        <li class="context__menu-item">
          <a class="context__menu-item-link" @click.prevent="showExportModal">
            <i class="context__menu-item-icon iconoir-download"></i>
            {{ $t('editWorkspaceContext.export') }}
          </a>
        </li>
        <li class="context__menu-item context__menu-item--with-separator">
          <a
            class="context__menu-item-link context__menu-item-link--delete"
            @click.prevent="showDeleteModal"
          >
            <i class="context__menu-item-icon iconoir-bin"></i>
            {{ $t('editWorkspaceContext.delete') }}
          </a>
        </li>
      </ul>
      <RenameWorkspaceModal
        ref="renameWorkspaceModal"
        :workspace="workspace"
        @updated="$emit('workspace-updated', $event)"
      ></RenameWorkspaceModal>
      <DeleteWorkspaceModal
        ref="deleteWorkspaceModal"
        :workspace="workspace"
        @workspace-deleted="$emit('workspace-deleted', $event)"
      ></DeleteWorkspaceModal>
      <WorkspaceMembersModal
        ref="workspaceMembersModal"
        :workspace="workspace"
      ></WorkspaceMembersModal>
      <AdminExportWorkspaceModal
        ref="adminExportWorkspaceModal"
        :workspace="workspace"
      ></AdminExportWorkspaceModal>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import AdminExportWorkspaceModal from '@baserow/modules/core/components/admin/workspaces/modals/AdminExportWorkspaceModal'
import DeleteWorkspaceModal from '@baserow/modules/core/components/admin/workspaces/modals/DeleteWorkspaceModal'
import RenameWorkspaceModal from '@baserow/modules/core/components/admin/workspaces/modals/RenameWorkspaceModal'
import WorkspaceMembersModal from '@baserow/modules/core/components/admin/workspaces/modals/WorkspaceMembersModal'

export default {
  name: 'EditWorkspaceContext',
  components: {
    AdminExportWorkspaceModal,
    DeleteWorkspaceModal,
    RenameWorkspaceModal,
    WorkspaceMembersModal,
  },
  mixins: [context],
  props: {
    workspace: {
      required: true,
      type: Object,
    },
  },
  emits: ['workspace-deleted', 'workspace-updated'],
  methods: {
    showRenameModal() {
      this.hide()
      this.$refs.renameWorkspaceModal?.show()
    },
    showDeleteModal() {
      this.hide()
      this.$refs.deleteWorkspaceModal?.show()
    },
    showMembersModal() {
      this.hide()
      this.$refs.workspaceMembersModal?.show()
    },
    showExportModal() {
      this.hide()
      this.$refs.adminExportWorkspaceModal?.show()
    },
  },
}
</script>
