<template>
  <div v-if="showEntry && hasPermission" class="context__menu-item">
    <div>
      <a
        class="context__menu-item-link"
        @click="
          () => {
            $refs.dateDependencyModal.show()
            $emit('hide-context')
          }
        "
      >
        <i class="context__menu-item-icon baserow-icon-dependency"></i>
        {{ $t('dateDependencyModal.contextMenuItemLabel') }}
      </a>
    </div>
    <DateDependencyModal
      ref="dateDependencyModal"
      :table="table"
      :table-fields="fields"
      :workspace-id="database.workspace.id"
    >
    </DateDependencyModal>
  </div>
</template>

<script>
import EnterpriseFeatures from '@baserow_enterprise/features'
import DateDependencyModal from '@baserow_enterprise/components/dateDependency/DateDependencyModal'

export default {
  name: 'DateDependencyMenuItem',
  emits: ['hide-context'],
  components: { DateDependencyModal },
  props: {
    table: {
      type: Object,
      required: false,
      default: null,
    },
    database: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: false,
      default: null,
    },
    fields: {
      type: [Array, null],
      required: false,
      default: null,
    },
  },
  computed: {
    hasFeature() {
      return this.$hasFeature(
        EnterpriseFeatures.DATE_DEPENDENCY,
        this.database.workspace.id
      )
    },
    hasPermission() {
      return this.$hasPermission(
        'database.table.field_rules.set_field_rules',
        this.table,
        this.database.workspace.id
      )
    },
    showEntry() {
      // Menu entry requested outside a field context (i.e. table sidebar menu,
      // view menu), so we can show it always.
      if (!this.field) {
        return true
      }
      return (
        (this.field.type === 'date' && !this.field.date_include_time) ||
        (this.field.type === 'duration' &&
          this.field.duration_format === 'd h') ||
        (this.field.type === 'link_row' &&
          this.field.link_row_table_id === this.table.id)
      )
    },
  },
}
</script>
