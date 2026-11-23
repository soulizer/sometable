<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <component
      :is="component"
      v-for="(component, index) in impersonateComponent"
      :key="index"
    ></component>
    <a
      ref="userContextAnchor"
      class="sidebar__workspaces-selector"
      @click="openUserContext"
    >
      <Avatar :initials="$filters.nameAbbreviation(name)"></Avatar>
      <span
        v-show="!collapsed"
        class="sidebar__workspaces-selector-selected-workspace"
        >{{ name }}</span
      >
      <span
        v-show="!collapsed"
        v-if="unreadNotificationsInAnyWorkspace"
        class="sidebar__unread-notifications-icon"
      ></span>
      <i
        v-show="!collapsed"
        class="sidebar__workspaces-selector-icon baserow-icon-up-down-arrows"
      ></i>
    </a>
    <SidebarUserContext
      ref="userContext"
      :workspaces="workspaces"
      :selected-workspace="selectedWorkspace"
    ></SidebarUserContext>

    <SidebarAllWorkspacesMenu v-show="!collapsed"></SidebarAllWorkspacesMenu>

    <SidebarFoot
      :collapsed="collapsed"
      :width="width"
      @set-col1-width="$emit('set-col1-width', $event)"
    ></SidebarFoot>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import SidebarUserContext from '@baserow/modules/core/components/sidebar/SidebarUserContext'
import SidebarAllWorkspacesMenu from '@baserow/modules/core/components/sidebar/SidebarAllWorkspacesMenu'
import SidebarFoot from '@baserow/modules/core/components/sidebar/SidebarFoot'

export default {
  name: 'SidebarAllWorkspaces',
  components: {
    SidebarUserContext,
    SidebarAllWorkspacesMenu,
    SidebarFoot,
  },
  props: {
    workspaces: {
      type: Array,
      required: true,
    },
    selectedWorkspace: {
      type: Object,
      required: true,
    },
    collapsed: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    width: {
      type: Number,
      required: false,
      default: 240,
    },
  },
  emits: ['set-col1-width'],
  computed: {
    impersonateComponent() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getImpersonateComponent())
        .filter((component) => component !== null)
    },
    ...mapGetters({
      name: 'auth/getName',
      unreadNotificationsInAnyWorkspace: 'notification/anyWorkspaceWithUnread',
    }),
  },
  methods: {
    /**
     * The click can land while the sidebar is (re)mounting, for example during
     * a route change, in which case the child refs are not available yet.
     */
    openUserContext() {
      const context = this.$refs.userContext
      const anchor = this.$refs.userContextAnchor
      if (!context || !anchor) {
        return
      }
      context.toggle(anchor, 'bottom', 'left', 4, 16)
    },
  },
}
</script>
