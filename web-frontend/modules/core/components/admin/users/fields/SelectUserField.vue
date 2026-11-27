<template>
  <div class="user-admin-select" @click.stop @contextmenu.stop>
    <Checkbox
      size="small"
      :checked="selected"
      :aria-label="selectionLabel"
      @input="onInput"
    ></Checkbox>
  </div>
</template>

<script>
import Checkbox from '@baserow/modules/core/components/Checkbox'

export default {
  name: 'SelectUserField',
  components: { Checkbox },
  props: {
    row: {
      required: true,
      type: Object,
    },
    selectedUserIds: {
      required: false,
      type: Array,
      default: () => [],
    },
  },
  emits: ['selection-change'],
  computed: {
    selected() {
      return this.selectedUserIds.includes(this.row.id)
    },
    selectionLabel() {
      return this.$t('usersAdminTable.selectUser', {
        username: this.row.username,
      })
    },
  },
  methods: {
    onInput(value) {
      this.$emit('selection-change', { id: this.row.id, value })
    },
  },
}
</script>
