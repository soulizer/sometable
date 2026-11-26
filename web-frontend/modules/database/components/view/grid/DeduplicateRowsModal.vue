<template>
  <Modal ref="modal" :close-button="!deleting" @hidden="reset">
    <h2 class="box__title">{{ $t('deduplicateRowsModal.title') }}</h2>
    <Error :error="error"></Error>

    <p class="deduplicate__description">
      {{ $t('deduplicateRowsModal.description') }}
    </p>

    <div class="deduplicate__section">
      <h3 class="deduplicate__section-title">
        {{ $t('deduplicateRowsModal.stepFields') }}
      </h3>
      <div class="deduplicate__fields">
        <label
          v-for="field in selectableFields"
          :key="field.id"
          class="deduplicate__field"
        >
          <Checkbox
            :model-value="selectedFieldIds.includes(field.id)"
            @update:model-value="toggleField(field.id, $event)"
          />
          <span>{{ field.name }}</span>
        </label>
      </div>
      <Button
        type="secondary"
        size="small"
        :loading="loading"
        :disabled="!selectedFieldIds.length"
        @click="preview"
      >
        {{ $t('deduplicateRowsModal.preview') }}
      </Button>
    </div>

    <div v-if="previewed" class="deduplicate__section">
      <h3 class="deduplicate__section-title">
        {{ $t('deduplicateRowsModal.stepPreview') }}
      </h3>
      <p v-if="!groups.length" class="deduplicate__empty">
        {{ $t('deduplicateRowsModal.noDuplicates') }}
      </p>
      <div v-for="group in groups" :key="group.key" class="deduplicate__group">
        <div class="deduplicate__group-header">
          <strong>{{ group.values.join(' / ') || '—' }}</strong>
          <span>
            {{ $t('deduplicateRowsModal.rowCount', { count: group.row_count }) }}
          </span>
        </div>
        <div v-if="rule === 'manual'" class="deduplicate__group-rows">
          <label
            v-for="row in group.rows"
            :key="row.id"
            class="deduplicate__row"
          >
            <Radio
              :value="row.id"
              :model-value="keepMap[group.key]"
              @input="keepMap[group.key] = $event"
            />
            <span>#{{ row.id }} — {{ row.values.join(' / ') }}</span>
          </label>
        </div>
      </div>
    </div>

    <div v-if="previewed && groups.length" class="deduplicate__section">
      <h3 class="deduplicate__section-title">
        {{ $t('deduplicateRowsModal.stepRule') }}
      </h3>
      <RadioGroup v-model="rule" :options="ruleOptions" />
      <div class="deduplicate__options">
        <label>
          <Checkbox v-model="backup" />
          <span>{{ $t('deduplicateRowsModal.backupBefore') }}</span>
        </label>
      </div>
    </div>

    <Alert v-if="confirming" type="warning" class="margin-top-2">
      {{ $t('deduplicateRowsModal.warning', { count: deleteCount }) }}
    </Alert>

    <div class="actions deduplicate__actions">
      <div class="align-right">
        <Button :disabled="deleting" @click="onCancel">
          {{ $t('action.cancel') }}
        </Button>
        <Button
          v-if="previewed && groups.length && !confirming"
          type="danger"
          :disabled="!canProceed"
          @click="confirming = true"
        >
          {{ $t('deduplicateRowsModal.continue') }}
        </Button>
        <Button
          v-if="confirming"
          type="danger"
          :loading="deleting"
          @click="remove"
        >
          {{ $t('deduplicateRowsModal.confirmDelete', { count: deleteCount }) }}
        </Button>
      </div>
    </div>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import RowAdminService from '@baserow/modules/database/services/row'

export default {
  name: 'DeduplicateRowsModal',
  mixins: [modal, error],
  props: {
    fields: {
      type: Array,
      required: true,
    },
  },
  emits: ['deduplicated'],
  data() {
    return {
      selectedFieldIds: [],
      groups: [],
      totalGroups: 0,
      previewed: false,
      loading: false,
      deleting: false,
      confirming: false,
      rule: 'oldest',
      backup: false,
      keepMap: {},
    }
  },
  computed: {
    ...mapGetters({
      table: 'table/getSelected',
    }),
    selectableFields() {
      return this.fields.filter(
        (field) =>
          !field.read_only &&
          !['link_row', 'multiple_collaborators'].includes(field.type)
      )
    },
    ruleOptions() {
      return [
        { value: 'oldest', label: this.$t('deduplicateRowsModal.ruleOldest') },
        { value: 'newest', label: this.$t('deduplicateRowsModal.ruleNewest') },
        { value: 'manual', label: this.$t('deduplicateRowsModal.ruleManual') },
      ]
    },
    deleteCount() {
      return this.groups.reduce(
        (count, group) => count + group.row_count - 1,
        0
      )
    },
    canProceed() {
      if (this.rule !== 'manual') return true
      return this.groups.every((group) => Boolean(this.keepMap[group.key]))
    },
  },
  methods: {
    onCancel() {
      if (this.confirming && !this.deleting) {
        this.confirming = false
        return
      }
      this.hide()
    },
    reset() {
      this.selectedFieldIds = []
      this.groups = []
      this.previewed = false
      this.confirming = false
      this.backup = false
      this.rule = 'oldest'
      this.keepMap = {}
      this.hideError()
    },
    toggleField(id, checked) {
      if (checked && !this.selectedFieldIds.includes(id)) {
        this.selectedFieldIds.push(id)
      } else if (!checked) {
        this.selectedFieldIds = this.selectedFieldIds.filter((item) => item !== id)
      }
      this.previewed = false
    },
    async preview() {
      this.loading = true
      this.hideError()
      try {
        const { data } = await RowAdminService(this.$client).deduplicatePreview(
          this.table.id,
          { field_ids: this.selectedFieldIds, limit: 50 }
        )
        this.groups = data.groups
        this.totalGroups = data.total_groups
        this.previewed = true
        this.keepMap = {}
        for (const group of this.groups) {
          this.keepMap[group.key] = group.rows[0]?.id
        }
      } catch (error) {
        this.handleError(error, 'table')
      } finally {
        this.loading = false
      }
    },
    async remove() {
      this.deleting = true
      this.hideError()
      try {
        const { data } = await RowAdminService(this.$client).deduplicate(
          this.table.id,
          {
            field_ids: this.selectedFieldIds,
            rule: this.rule,
            keep_row_ids: this.keepMap,
            backup: this.backup,
          }
        )
        this.$emit('deduplicated', data)
        this.hide()
      } catch (error) {
        this.handleError(error, 'table')
      } finally {
        this.deleting = false
      }
    },
  },
}
</script>
