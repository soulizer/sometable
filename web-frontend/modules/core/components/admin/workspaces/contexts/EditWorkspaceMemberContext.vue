<template>
  <Context ref="context" overflow-scroll max-height-if-outside-viewport>
    <template v-if="Object.keys(member).length > 0">
      <div class="context__menu-title">{{ member.email }}</div>
      <ul class="context__menu">
        <li v-if="!isSelf && !isAdmin" class="context__menu-item">
          <a
            class="context__menu-item-link"
            :class="{ 'context__menu-item-link--loading': loading }"
            @click.prevent="
              $emit('update-role', { member, permissions: 'ADMIN' })
            "
          >
            <i class="context__menu-item-icon iconoir-user-crown"></i>
            {{ $t('adminWorkspaceMembers.makeAdmin') }}
          </a>
        </li>
        <li v-if="!isSelf && isAdmin" class="context__menu-item">
          <a
            class="context__menu-item-link"
            :class="{ 'context__menu-item-link--loading': loading }"
            @click.prevent="
              $emit('update-role', { member, permissions: 'MEMBER' })
            "
          >
            <i class="context__menu-item-icon iconoir-user"></i>
            {{ $t('adminWorkspaceMembers.makeMember') }}
          </a>
        </li>
        <li
          v-if="!isSelf"
          class="context__menu-item context__menu-item--with-separator"
        >
          <a
            class="context__menu-item-link context__menu-item-link--delete"
            @click.prevent="$emit('delete-member', member)"
          >
            <i class="context__menu-item-icon iconoir-bin"></i>
            {{ $t('adminWorkspaceMembers.removeMember') }}
          </a>
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'EditWorkspaceMemberContext',
  mixins: [context],
  props: {
    member: {
      type: Object,
      required: true,
    },
    userId: {
      type: Number,
      default: null,
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update-role', 'delete-member'],
  computed: {
    isSelf() {
      return this.userId !== null && this.member.user_id === this.userId
    },
    isAdmin() {
      return (
        this.member.role_uid === 'ADMIN' || this.member.permissions === 'ADMIN'
      )
    },
  },
}
</script>
