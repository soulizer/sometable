<template>
  <nuxt-link
    v-if="hasPermission"
    v-slot="{ href, navigate, isExactActive, prefetch, shouldPrefetch }"
    custom
    prefetch-on="interaction"
    :to="{
      name: 'workspace-audit-log',
      params: {
        workspaceId: workspace.id,
      },
    }"
  >
    <li
      class="tree__item"
      :class="{
        'tree__item--loading': loading,
        active: isExactActive,
      }"
    >
      <div class="tree__action">
        <a
          :href="href"
          class="tree__link"
          @click="navigate"
          @pointerenter="shouldPrefetch('interaction') && prefetch()"
          @focus="shouldPrefetch('interaction') && prefetch()"
        >
          <i class="tree__icon baserow-icon-history"></i>
          <span class="tree__link-text">{{
            $t('auditLogSidebarWorkspace.title')
          }}</span>
        </a>
      </div>
    </li>
  </nuxt-link>
</template>

<script>

export default {
  name: 'AuditLogSidebarWorkspace',

  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  computed: {
    hasPermission() {
      return this.$hasPermission(
        'workspace.list_audit_log_entries',
        this.workspace,
        this.workspace.id
      )
    },
  },
}
</script>
