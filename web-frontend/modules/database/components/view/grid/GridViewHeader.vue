<template>
  <ul class="header__filter header__filter--full-width">
    <li v-if="isSelectionActive" class="header__filter-item">
      <span class="header__filter-link header__filter-link--disabled">
        <i class="iconoir-check-square header__filter-icon"></i>
        <span class="header__filter-name header__filter-name--forced">
          {{ $t('gridView.selectedRows', { count: selectionCount }) }}
        </span>
      </span>
      <a
        v-if="canDeleteSelected"
        class="header__filter-link"
        :aria-label="$t('gridView.deleteRows')"
        @click="askDeleteSelectedRows"
      >
        <i class="iconoir-bin header__filter-icon"></i>
        <span class="header__filter-name">{{ $t('gridView.deleteRows') }}</span>
      </a>
      <a
        class="header__filter-link"
        :aria-label="$t('gridView.clearSelection')"
        @click="clearSelection"
      >
        <i class="iconoir-cancel header__filter-icon"></i>
        <span class="header__filter-name">{{
          $t('gridView.clearSelection')
        }}</span>
      </a>
    </li>
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
  <ConfirmModal
    ref="deleteRowsConfirmModal"
    :title="$t('gridView.deleteSelectedRowsTitle')"
    :message="
      $t('gridView.deleteSelectedRowsMessage', { count: selectionCount })
    "
    :confirm-label="$t('gridView.deleteRows')"
    danger
    @confirm="confirmDeleteSelectedRows"
  />
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import DeduplicateRowsModal from '@baserow/modules/database/components/view/grid/DeduplicateRowsModal'
import GridViewRowHeight from '@baserow/modules/database/components/view/grid/GridViewRowHeight'
import GridViewHide from '@baserow/modules/database/components/view/grid/GridViewHide'
import PresenceBar from '@baserow/modules/core/components/presence/PresenceBar'
import ConfirmModal from '@baserow/modules/core/components/modals/ConfirmModal'
import ViewSearch from '@baserow/modules/database/components/view/ViewSearch'
import {
  isUserPresenceEnabled,
  tablePresenceSpaceName,
} from '@baserow/modules/database/utils/presence'
import { GRID_VIEW_MULTI_SELECT_CHECKBOX } from '@baserow/modules/database/constants'

export default {
  name: 'GridViewHeader',
  components: {
    DeduplicateRowsModal,
    GridViewRowHeight,
    GridViewHide,
    PresenceBar,
    ViewSearch,
    ConfirmModal,
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
    gridStore() {
      return this.storePrefix + 'view/grid'
    },
    table() {
      return this.$store.state.table.selected
    },
    selectionType() {
      return this.$store.getters[`${this.gridStore}/getSelectionType`]
    },
    selectionCount() {
      // This toolbar is for checkbox row selection only. A single cell click
      // also activates the area multi-select, but that must not turn into a
      // row-selection toolbar at the top of the grid.
      if (this.selectionType !== GRID_VIEW_MULTI_SELECT_CHECKBOX) {
        return 0
      }
      return this.$store.getters[
        `${this.gridStore}/getCheckboxSelectedRowsIds`
      ].length
    },
    isSelectionActive() {
      return (
        this.selectionType === GRID_VIEW_MULTI_SELECT_CHECKBOX &&
        this.selectionCount > 0
      )
    },
    canDeleteSelected() {
      if (
        this.readOnly ||
        !this.table ||
        !this.database?.workspace ||
        (this.table.data_sync && !this.table.data_sync.two_way_sync)
      ) {
        return false
      }
      return (
        this.$hasPermission(
          'database.table.delete_row',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.view.delete_row',
          this.view,
          this.database.workspace.id
        )
      )
    },
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
    askDeleteSelectedRows() {
      this.$refs.deleteRowsConfirmModal?.show()
    },
    async confirmDeleteSelectedRows() {
      this.$refs.deleteRowsConfirmModal?.hide()
      const count = this.selectionCount
      try {
        await this.$store.dispatch(`${this.gridStore}/deleteSelectedRows`, {
          table: this.table,
          view: this.view,
          fields: this.fields,
          getScrollTop: () => 0,
        })
        if (count > 0) {
          this.$store.dispatch('toast/success', {
            title: this.$t('gridView.rowsDeletedTitle'),
            message: this.$t('gridView.rowsDeletedMessage', { count }),
          })
        }
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    clearSelection() {
      this.$store.dispatch(`${this.gridStore}/clearAndDisableMultiSelect`, {
        view: this.view,
      })
    },
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
