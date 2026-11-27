<template>
  <div class="workspace-member-role">
    <i
      v-if="isAdmin"
      v-tooltip="$t('adminWorkspaceMembers.adminRole')"
      class="iconoir-user-crown"
    ></i>
    <span>{{ roleName }}</span>
  </div>
</template>

<script>
export default {
  name: 'WorkspaceMemberRoleField',
  props: {
    row: {
      type: Object,
      required: true,
    },
    column: {
      type: Object,
      required: true,
    },
  },
  computed: {
    roleUid() {
      return this.row.role_uid || this.row.permissions || 'MEMBER'
    },
    isAdmin() {
      return this.roleUid === 'ADMIN'
    },
    roleName() {
      return this.isAdmin
        ? this.$t('adminWorkspaceMembers.adminRole')
        : this.$t('adminWorkspaceMembers.memberRole')
    },
  },
}
</script>
