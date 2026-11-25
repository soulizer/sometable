<template>
  <div>
    <CrudTable
      ref="crudTable"
      :columns="columns"
      :service="service"
      row-id-key="id"
      :default-search="defaultSearch"
      @row-context="onRowContext"
    >
      <template #title>
        {{ $t('usersAdminTable.allUsers') }}
      </template>
      <template #primary-action>
        <Button
          type="primary"
          size="large"
          icon="iconoir-plus"
          @click="$refs.createUserModal?.show()"
        >
          {{ $t('usersAdminTable.createUser') }}
        </Button>
      </template>
      <template #menus="slotProps">
      <EditUserContext
        ref="editUserContext"
        :user="editUser"
        @delete-user="slotProps.deleteRow"
        @update="slotProps.updateRow"
      >
        </EditUserContext>
      </template>
    </CrudTable>
    <CreateUserModal
      ref="createUserModal"
      @created="onUserCreated"
    ></CreateUserModal>
  </div>
</template>

<script>
import UserAdminService from '@baserow/modules/core/services/admin/users'
import UsernameField from '@baserow/modules/core/components/admin/users/fields/UsernameField'
import UserWorkspacesField from '@baserow/modules/core/components/admin/users/fields/UserWorkspacesField'
import CrudTable from '@baserow/modules/core/components/crudTable/CrudTable'
import SimpleField from '@baserow/modules/core/components/crudTable/fields/SimpleField'
import LocalDateField from '@baserow/modules/core/components/crudTable/fields/LocalDateField'
import ActiveField from '@baserow/modules/core/components/admin/users/fields/ActiveField'
import TwoFactorAuthField from '@baserow/modules/core/components/crudTable/fields/TwoFactorAuthField'
import MoreField from '@baserow/modules/core/components/crudTable/fields/MoreField'
import EditUserContext from '@baserow/modules/core/components/admin/users/contexts/EditUserContext'
import CreateUserModal from '@baserow/modules/core/components/admin/users/modals/CreateUserModal'
import BooleanIconField from '@baserow/modules/core/components/crudTable/fields/BooleanIconField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export default {
  name: 'UsersAdminTable',
  components: {
    CrudTable,
    EditUserContext,
    CreateUserModal,
  },
  data() {
    this.service = UserAdminService(this.$client)
    return {
      editUser: {},
    }
  },
  computed: {
    defaultSearch() {
      const { search } = this.$route.query
      return search ? String(search) : null
    },
    membersPagePlugins() {
      return Object.values(this.$registry.getAll('membersPagePlugins'))
    },
    columns() {
      let columns = [
        new CrudTableColumn(
          'username',
          () => this.$t('usersAdminTable.username'),
          UsernameField,
          true,
          true
        ),
        new CrudTableColumn(
          'name',
          () => this.$t('usersAdminTable.name'),
          SimpleField,
          true
        ),
        new CrudTableColumn(
          'workspaces',
          () => this.$t('usersAdminTable.workspaces'),
          UserWorkspacesField
        ),
        new CrudTableColumn(
          'last_login',
          () => this.$t('usersAdminTable.lastLogin'),
          LocalDateField,
          true
        ),
        new CrudTableColumn(
          'date_joined',
          () => this.$t('usersAdminTable.dateJoined'),
          LocalDateField,
          true
        ),
        new CrudTableColumn(
          'is_active',
          () => this.$t('user.active'),
          ActiveField,
          true
        ),
        new CrudTableColumn(
          'two_factor_auth',
          () => this.$t('usersAdminTable.twoFactorAuth'),
          TwoFactorAuthField
        ),
        new CrudTableColumn(
          'email_verified',
          () => this.$t('usersAdminTable.emailVerified'),
          BooleanIconField,
          false,
          false,
          false,
          {
            icon: 'iconoir-check',
            title: this.$t('usersAdminTable.emailVerified'),
          }
        ),
        new CrudTableColumn('more', '', MoreField, false, false, true),
      ]
      for (const plugin of this.membersPagePlugins) {
        if (!plugin.isDeactivated()) {
          columns = plugin.mutateAdminUsersTableColumns(columns, {
            client: this.$client,
          })
        }
      }
      return columns
    },
  },
  methods: {
    onUserCreated() {
      this.$refs.crudTable?.refresh()
    },
    onRowContext({ row, event, target }) {
      event.preventDefault()
      if (target === undefined) {
        target = {
          left: event.clientX,
          top: event.clientY,
        }
      }

      const action = row.id === this.editUser.id ? 'toggle' : 'show'
      this.editUser = row
      this.$refs.editUserContext[action](target, 'bottom', 'left', 4)
    },
  },
}
</script>
