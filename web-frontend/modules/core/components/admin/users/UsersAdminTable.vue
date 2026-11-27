<template>
  <div>
    <CrudTable
      ref="crudTable"
      :columns="columns"
      :service="service"
      row-id-key="id"
      :filters="filters"
      :default-search="defaultSearch"
      :selected-user-ids="selectedUserIds"
      @rows-update="onRowsUpdate"
      @selection-change="onSelectionChange"
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
      <template #header-right-side>
        <div v-if="selectedUserIds.length" class="users-admin-bulk">
          <span class="users-admin-bulk__count">
            {{
              $t('usersAdminTable.selectedCount', {
                count: selectedUserIds.length,
              })
            }}
          </span>
          <Button
            type="secondary"
            size="large"
            icon="iconoir-settings"
            :loading="bulkLoading"
            @click="toggleBulkContext"
          >
            {{ $t('usersAdminTable.bulkActions') }}
          </Button>
        </div>
      </template>
      <template #header-filters>
        <div class="data-table__filters">
          <Checkbox
            size="small"
            :checked="allRowsSelected"
            :indeterminate="someRowsSelected && !allRowsSelected"
            :disabled="!tableRows.length || bulkLoading"
            :aria-label="$t('usersAdminTable.selectAllOnPage')"
            @input="toggleSelectAll"
          >
            <span>{{ $t('usersAdminTable.selectAllOnPage') }}</span>
          </Checkbox>
          <button
            v-if="selectedUserIds.length"
            type="button"
            class="users-admin-bulk__clear"
            :disabled="bulkLoading"
            @click="clearSelection"
          >
            {{ $t('usersAdminTable.clearSelection') }}
          </button>
          <Dropdown
            :model-value="statusFilter"
            :show-search="false"
            @update:model-value="statusFilter = $event"
          >
            <template #selectedValue>
              <span class="dropdown__selected-text">{{ statusLabel }}</span>
            </template>
            <template #defaultValue>
              <span class="dropdown__selected-text">{{ statusLabel }}</span>
            </template>
            <DropdownItem :name="$t('usersAdminTable.allStatuses')" value="" />
            <DropdownItem
              :name="$t('usersAdminTable.onlyActive')"
              value="true"
            />
            <DropdownItem
              :name="$t('usersAdminTable.onlyInactive')"
              value="false"
            />
          </Dropdown>
          <Dropdown
            :model-value="roleFilter"
            :show-search="false"
            @update:model-value="roleFilter = $event"
          >
            <template #selectedValue>
              <span class="dropdown__selected-text">{{ roleLabel }}</span>
            </template>
            <template #defaultValue>
              <span class="dropdown__selected-text">{{ roleLabel }}</span>
            </template>
            <DropdownItem :name="$t('usersAdminTable.allRoles')" value="" />
            <DropdownItem
              :name="$t('usersAdminTable.onlyAdmins')"
              value="true"
            />
            <DropdownItem
              :name="$t('usersAdminTable.onlyRegular')"
              value="false"
            />
          </Dropdown>
          <Dropdown
            :model-value="verifiedFilter"
            :show-search="false"
            @update:model-value="verifiedFilter = $event"
          >
            <template #selectedValue>
              <span class="dropdown__selected-text">{{ verifiedLabel }}</span>
            </template>
            <template #defaultValue>
              <span class="dropdown__selected-text">{{ verifiedLabel }}</span>
            </template>
            <DropdownItem :name="$t('usersAdminTable.allEmails')" value="" />
            <DropdownItem
              :name="$t('usersAdminTable.onlyVerified')"
              value="true"
            />
            <DropdownItem
              :name="$t('usersAdminTable.onlyUnverified')"
              value="false"
            />
          </Dropdown>
        </div>
      </template>
      <template #menus="slotProps">
        <EditUserContext
          ref="editUserContext"
          :user="editUser"
          @delete-user="slotProps.deleteRow"
          @update="slotProps.updateRow"
        >
        </EditUserContext>
        <Context
          ref="bulkContext"
          overflow-scroll
          max-height-if-outside-viewport
        >
          <div class="context__menu-title">
            {{ $t('usersAdminTable.bulkActions') }}
          </div>
          <ul class="context__menu">
            <li class="context__menu-item">
              <a
                class="context__menu-item-link"
                :class="{ 'context__menu-item-link--loading': bulkLoading }"
                @click.prevent="bulkUpdate({ is_active: true })"
              >
                <i class="context__menu-item-icon iconoir-check"></i>
                {{ $t('usersAdminTable.bulkActivate') }}
              </a>
            </li>
            <li class="context__menu-item">
              <a
                class="context__menu-item-link"
                :class="{ 'context__menu-item-link--loading': bulkLoading }"
                @click.prevent="bulkUpdate({ is_active: false })"
              >
                <i class="context__menu-item-icon iconoir-cancel"></i>
                {{ $t('usersAdminTable.bulkDeactivate') }}
              </a>
            </li>
            <li class="context__menu-item">
              <a
                class="context__menu-item-link"
                :class="{ 'context__menu-item-link--loading': bulkLoading }"
                @click.prevent="bulkUpdate({ is_staff: true })"
              >
                <i class="context__menu-item-icon iconoir-user-crown"></i>
                {{ $t('usersAdminTable.bulkMakeStaff') }}
              </a>
            </li>
            <li class="context__menu-item">
              <a
                class="context__menu-item-link"
                :class="{ 'context__menu-item-link--loading': bulkLoading }"
                @click.prevent="bulkUpdate({ is_staff: false })"
              >
                <i class="context__menu-item-icon iconoir-user"></i>
                {{ $t('usersAdminTable.bulkRemoveStaff') }}
              </a>
            </li>
            <li class="context__menu-item context__menu-item--with-separator">
              <a
                class="context__menu-item-link context__menu-item-link--delete"
                @click.prevent="showBulkDeleteModal"
              >
                <i class="context__menu-item-icon iconoir-bin"></i>
                {{ $t('usersAdminTable.bulkDelete') }}
              </a>
            </li>
          </ul>
        </Context>
      </template>
    </CrudTable>
    <CreateUserModal
      ref="createUserModal"
      @created="onUserCreated"
    ></CreateUserModal>
    <ConfirmModal
      ref="bulkDeleteModal"
      :title="$t('usersAdminTable.bulkDeleteTitle')"
      :message="bulkDeleteMessage"
      :confirm-label="$t('usersAdminTable.bulkDelete')"
      :loading="bulkLoading"
      danger
      @confirm="bulkDelete"
    ></ConfirmModal>
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
import SelectUserField from '@baserow/modules/core/components/admin/users/fields/SelectUserField'
import EditUserContext from '@baserow/modules/core/components/admin/users/contexts/EditUserContext'
import ConfirmModal from '@baserow/modules/core/components/modals/ConfirmModal'
import CreateUserModal from '@baserow/modules/core/components/admin/users/modals/CreateUserModal'
import BooleanIconField from '@baserow/modules/core/components/crudTable/fields/BooleanIconField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import Dropdown from '@baserow/modules/core/components/Dropdown'
import DropdownItem from '@baserow/modules/core/components/DropdownItem'

export default {
  name: 'UsersAdminTable',
  components: {
    CrudTable,
    EditUserContext,
    ConfirmModal,
    CreateUserModal,
    Dropdown,
    DropdownItem,
  },
  data() {
    this.service = UserAdminService(this.$client)
    return {
      editUser: {},
      statusFilter: '',
      roleFilter: '',
      verifiedFilter: '',
      tableRows: [],
      selectedUserIds: [],
      bulkLoading: false,
    }
  },
  computed: {
    filters() {
      const filters = {}
      if (this.statusFilter) filters.is_active = this.statusFilter
      if (this.roleFilter) filters.is_staff = this.roleFilter
      if (this.verifiedFilter) filters.email_verified = this.verifiedFilter
      return filters
    },
    statusLabel() {
      if (this.statusFilter === 'true')
        return this.$t('usersAdminTable.onlyActive')
      if (this.statusFilter === 'false') {
        return this.$t('usersAdminTable.onlyInactive')
      }
      return this.$t('usersAdminTable.allStatuses')
    },
    roleLabel() {
      if (this.roleFilter === 'true')
        return this.$t('usersAdminTable.onlyAdmins')
      if (this.roleFilter === 'false')
        return this.$t('usersAdminTable.onlyRegular')
      return this.$t('usersAdminTable.allRoles')
    },
    verifiedLabel() {
      if (this.verifiedFilter === 'true') {
        return this.$t('usersAdminTable.onlyVerified')
      }
      if (this.verifiedFilter === 'false') {
        return this.$t('usersAdminTable.onlyUnverified')
      }
      return this.$t('usersAdminTable.allEmails')
    },
    defaultSearch() {
      const { search } = this.$route.query
      return search ? String(search) : null
    },
    allRowsSelected() {
      return (
        this.tableRows.length > 0 &&
        this.tableRows.every((row) => this.selectedUserIds.includes(row.id))
      )
    },
    someRowsSelected() {
      return this.tableRows.some((row) => this.selectedUserIds.includes(row.id))
    },
    bulkDeleteMessage() {
      const count = this.bulkDeleteUserIds.length
      const skipped = this.selectedUserIds.length - count
      let message = this.$t('usersAdminTable.bulkDeleteMessage', { count })
      if (skipped > 0) {
        message += ` ${this.$t('usersAdminTable.bulkSkippedSelf', {
          count: skipped,
        })}`
      }
      return message
    },
    bulkDeleteUserIds() {
      const selfId = this.$store.getters['auth/getUserId']
      return this.selectedUserIds.filter((id) => id !== selfId)
    },
    membersPagePlugins() {
      return Object.values(this.$registry.getAll('membersPagePlugins'))
    },
    columns() {
      let columns = [
        new CrudTableColumn('select', '', SelectUserField, false, true),
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
    toggleBulkContext(event) {
      if (!event?.currentTarget) return
      this.$refs.bulkContext?.toggle(event.currentTarget, 'bottom', 'left', 4)
    },
    hideBulkContext() {
      this.$refs.bulkContext?.hide?.()
    },
    onRowsUpdate(rows) {
      this.tableRows = rows
      const visibleIds = new Set(rows.map((row) => row.id))
      this.selectedUserIds = this.selectedUserIds.filter((id) =>
        visibleIds.has(id)
      )
    },
    onSelectionChange({ id, value }) {
      const index = this.selectedUserIds.indexOf(id)
      if (value && index === -1) {
        this.selectedUserIds.push(id)
      } else if (!value && index !== -1) {
        this.selectedUserIds.splice(index, 1)
      }
    },
    toggleSelectAll(value) {
      this.selectedUserIds = value ? this.tableRows.map((row) => row.id) : []
    },
    clearSelection() {
      this.selectedUserIds = []
      this.hideBulkContext()
    },
    notifyBulkResult(succeeded, failed) {
      const store = this.$store
      if (succeeded > 0 && failed === 0) {
        store.dispatch('toast/success', {
          title: this.$t('usersAdminTable.bulkSuccessTitle'),
          message: this.$t('usersAdminTable.bulkSuccessMessage', {
            count: succeeded,
          }),
        })
      } else if (failed > 0) {
        store.dispatch('toast/error', {
          title: this.$t('usersAdminTable.bulkPartialTitle'),
          message: this.$t('usersAdminTable.bulkPartialMessage', {
            success: succeeded,
            failed,
          }),
        })
      }
    },
    async bulkUpdate(values) {
      if (this.bulkLoading) return

      const selfId = this.$store.getters['auth/getUserId']
      let ids = [...this.selectedUserIds]
      if (
        (values.is_active === false || values.is_staff === false) &&
        ids.includes(selfId)
      ) {
        ids = ids.filter((id) => id !== selfId)
        this.$store.dispatch('toast/warning', {
          title: this.$t('usersAdminTable.bulkSkippedSelfTitle'),
          message: this.$t('usersAdminTable.bulkSkippedSelf', { count: 1 }),
        })
      }
      if (ids.length === 0) return

      this.bulkLoading = true
      this.hideBulkContext()
      const results = await this.service.bulkUpdate(ids, values)
      const succeeded = results.filter(
        (result) => result.status === 'fulfilled'
      ).length
      const failed = results.length - succeeded
      await this.$refs.crudTable?.refresh()
      this.bulkLoading = false
      this.notifyBulkResult(succeeded, failed)
      if (failed === 0) this.clearSelection()
    },
    showBulkDeleteModal() {
      this.hideBulkContext()
      if (this.bulkDeleteUserIds.length === 0) {
        this.$store.dispatch('toast/warning', {
          title: this.$t('usersAdminTable.bulkSkippedSelfTitle'),
          message: this.$t('usersAdminTable.bulkSkippedSelf', { count: 1 }),
        })
        return
      }
      this.$refs.bulkDeleteModal?.show()
    },
    async bulkDelete() {
      if (this.bulkLoading || this.bulkDeleteUserIds.length === 0) return

      const ids = [...this.bulkDeleteUserIds]
      const skipped = this.selectedUserIds.length - ids.length
      this.bulkLoading = true
      this.$refs.bulkDeleteModal?.hide()
      const results = await this.service.bulkDelete(ids)
      const succeeded = results.filter(
        (result) => result.status === 'fulfilled'
      ).length
      const failed = results.length - succeeded
      await this.$refs.crudTable?.refresh()
      this.bulkLoading = false
      this.notifyBulkResult(succeeded, failed)
      if (skipped > 0) {
        this.$store.dispatch('toast/warning', {
          title: this.$t('usersAdminTable.bulkSkippedSelfTitle'),
          message: this.$t('usersAdminTable.bulkSkippedSelf', {
            count: skipped,
          }),
        })
      }
      if (failed === 0) this.clearSelection()
    },
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
