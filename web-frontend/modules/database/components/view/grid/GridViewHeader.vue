<template>
  <ul class="header__filter header__filter--full-width">
    <li v-if="canDeduplicate" class="header__filter-item">
      <a class="header__filter-link" @click="$refs.deduplicateModal?.show()">
        <i class="header__filter-icon iconoir-filter-alt"></i>
        {{ $t('deduplicateRowsModal.title') }}
      </a>
      <DeduplicateRowsModal
        ref="deduplicateModal"
        :fields="fields"
        @deduplicated="onDeduplicated"
      ></DeduplicateRowsModal>
    </li>
    <li class="header__filter-item">
      <GridViewHide
        :database="database"
        :view="view"
        :fields="fieldsAllowedToBeHidden"
        :read-only="readOnly"
        :store-prefix="storePrefix"
      ></GridViewHide>
    </li>
    <li class="header__filter-item">
      <GridViewRowHeight
        :database="database"
        :view="view"
        :store-prefix="storePrefix"
        :read-only="readOnly"
      ></GridViewRowHeight>
    </li>
    <template v-if="presenceEnabled">
      <li
        class="header__filter-item header__filter-item--right header__filter-item--stretch"
      >
        <PresenceBar :space-name="activePresenceSpace" />
      </li>
      <li
        v-if="hasPresenceUsers"
        class="header__filter-item header__filter-item--stretch header__filter-item--no-margin-left"
      >
        <div class="presence-bar__divider" />
      </li>
    </template>
    <li
      :class="[
        'header__filter-item',
        {
          'header__filter-item--right': !presenceEnabled,
          'header__filter-item--only-margin-right': presenceEnabled,
        },
      ]"
    >
      <ViewSearch
        :view="view"
        :fields="fields"
        :store-prefix="storePrefix"
        @refresh="$emit('refresh', $event)"
      ></ViewSearch>
    </li>
  </ul>
</template>

<script>
import DeduplicateRowsModal from '@baserow/modules/database/components/view/grid/DeduplicateRowsModal'
import GridViewRowHeight from '@baserow/modules/database/components/view/grid/GridViewRowHeight'
import GridViewHide from '@baserow/modules/database/components/view/grid/GridViewHide'
import PresenceBar from '@baserow/modules/core/components/presence/PresenceBar'
import ViewSearch from '@baserow/modules/database/components/view/ViewSearch'
import {
  isUserPresenceEnabled,
  tablePresenceSpaceName,
} from '@baserow/modules/database/utils/presence'

export default {
  name: 'GridViewHeader',
  components: {
    DeduplicateRowsModal,
    GridViewRowHeight,
    GridViewHide,
    PresenceBar,
    ViewSearch,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  emits: ['refresh'],
  computed: {
    presenceEnabled() {
      return isUserPresenceEnabled(this)
    },
    activePresenceSpace() {
      const table = this.$store.state.table.selected
      if (!table || !table.id) return ''
      return tablePresenceSpaceName(table.id)
    },
    hasPresenceUsers() {
      if (!this.activePresenceSpace) return false
      const currentUserId = this.$store.getters['auth/getUserId']
      const users = this.$store.getters['presence/getUniqueUsersBySpace'](
        this.activePresenceSpace
      )
      return users.some((u) => u.user_id !== currentUserId)
    },
    fieldsAllowedToBeHidden() {
      return this.fields.filter((field) => !field.primary)
    },
    canDeduplicate() {
      if (this.readOnly || !this.database || !this.database.workspace) {
        return false
      }
      const table = this.$store.state.table.selected
      if (!table || table.data_sync) return false
      return this.$hasPermission(
        'database.table.delete_row',
        table,
        this.database.workspace.id
      )
    },
  },
  methods: {
    onDeduplicated(result) {
      this.$emit('refresh')
      if (result?.deleted_count) {
        this.$store.dispatch('toast/success', {
          title: this.$t('deduplicateRowsModal.doneTitle'),
          message: this.$t('deduplicateRowsModal.doneMessage', {
            count: result.deleted_count,
          }),
        })
      }
    },
  },
}
</script>
