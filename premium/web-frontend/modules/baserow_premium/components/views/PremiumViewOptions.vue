<template>
  <div>
    <div class="view-sharing__option">
      <SwitchInput
        small
        :value="!view.show_logo"
        @input="update('show_logo', !$event)"
      >
        <span>{{ $t('shareLinkOptions.baserowLogo.label') }}</span>
      </SwitchInput>
    </div>
    <div v-if="hasValidExporter" class="view-sharing__option">
      <SwitchInput
        small
        :value="view.allow_public_export"
        @input="update('allow_public_export', $event)"
      >
        <i class="switch__icon iconoir-share-ios"></i>
        <span>{{ $t('shareLinkOptions.allowPublicExportLabel') }}</span>
      </SwitchInput>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import ViewPremiumService from '@baserow_premium/services/view'
import { notifyIf } from '@baserow/modules/core/utils/error'
import viewTypeHasExporterTypes from '@baserow/modules/database/utils/viewTypeHasExporterTypes'

export default {
  name: 'PremiumViewOptions',
  emits: ['update-view'],

  props: {
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      additionalUserData: 'auth/getAdditionalUserData',
    }),
    workspace() {
      return this.$store.getters['application/get'](this.view.table.database_id)
        .workspace
    },
    hasValidExporter() {
      return viewTypeHasExporterTypes(this.view.type, this.$registry)
    },
  },
  methods: {
    async update(key, value) {
      try {
        // We are being optimistic that the request will succeed.
        this.$emit('update-view', { ...this.view, [key]: value })
        await ViewPremiumService(this.$client).update(this.view.id, {
          [key]: value,
        })
      } catch (error) {
        // In case it didn't we will roll back the change.
        this.$emit('update-view', { ...this.view, [key]: !value })
        notifyIf(error, 'view')
      }
    },
  },
}
</script>
