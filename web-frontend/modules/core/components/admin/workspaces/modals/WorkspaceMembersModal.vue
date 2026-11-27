<template>
  <Modal ref="modal" wide>
    <div class="workspace-members-modal">
      <h2 class="box__title">
        {{ $t('adminWorkspaceMembers.title', { workspace: workspace.name }) }}
      </h2>
      <CrudTable
        ref="crudTable"
        :columns="columns"
        :service="service"
        row-id-key="id"
        @row-context="onRowContext"
      >
        <template #menus>
          <EditWorkspaceMemberContext
            ref="editMemberContext"
            :member="editMember"
            :user-id="userId"
            :loading="loading"
            @update-role="updateRole"
            @delete-member="deleteMember"
          ></EditWorkspaceMemberContext>
        </template>
      </CrudTable>
    </div>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import WorkspacesAdminService, {
  ADMIN_WORKSPACE_MEMBERS_URL,
} from '@baserow/modules/core/services/admin/workspaces'
import WorkspaceMemberRoleField from '@baserow/modules/core/components/admin/workspaces/fields/WorkspaceMemberRoleField'
import EditWorkspaceMemberContext from '@baserow/modules/core/components/admin/workspaces/contexts/EditWorkspaceMemberContext'

export default {
  name: 'WorkspaceMembersModal',
  components: {
    CrudTable,
    EditWorkspaceMemberContext,
  },
  mixins: [modal],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    this.columns = [
      new CrudTableColumn(
        'email',
        () => this.$t('adminWorkspaceMembers.email'),
        SimpleField,
        true
      ),
      new CrudTableColumn(
        'permissions',
        () => this.$t('adminWorkspaceMembers.role'),
        WorkspaceMemberRoleField,
        true
      ),
      new CrudTableColumn(
        'created_on',
        () => this.$t('adminWorkspaceMembers.joined'),
        LocalDateField,
        true
      ),
      new CrudTableColumn('more', '', MoreField, false, false, true),
    ]
    return {
      editMember: {},
      loading: false,
    }
  },
  computed: {
    ...mapGetters({ userId: 'auth/getUserId' }),
    service() {
      const service = WorkspacesAdminService(this.$client)
      return {
        ...service,
        options: {
          ...service.options,
          baseUrl: (params) => ADMIN_WORKSPACE_MEMBERS_URL(params.workspaceId),
          urlParams: { workspaceId: this.workspace.id },
        },
      }
    },
  },
  methods: {
    onRowContext({ row, event, target }) {
      event.preventDefault()
      if (target === undefined) {
        target = { left: event.clientX, top: event.clientY }
      }

      const action = row.id === this.editMember.id ? 'toggle' : 'show'
      this.editMember = row
      this.$refs.editMemberContext[action](target, 'bottom', 'left', 4)
    },
    async updateRole({ member, permissions }) {
      if (this.loading) return
      this.loading = true
      try {
        const { data } = await WorkspacesAdminService(
          this.$client
        ).updateMember(this.workspace.id, member.id, { permissions })
        this.$refs.crudTable.updateRow(data)
        this.$refs.editMemberContext?.hide?.()
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        this.loading = false
      }
    },
    async deleteMember(member) {
      if (this.loading) return
      this.loading = true
      try {
        await WorkspacesAdminService(this.$client).deleteMember(
          this.workspace.id,
          member.id
        )
        this.$refs.crudTable.deleteRow(member.id)
        this.$refs.editMemberContext?.hide?.()
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
