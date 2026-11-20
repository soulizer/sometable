<template>
  <div class="dashboard-sharing__option">
    <SwitchInput
      small
      :value="!dashboard.show_logo"
      @input="update('show_logo', !$event)"
    >
      <span>{{ $t('premiumDashboardShareOptions.hideLogo') }}</span>
    </SwitchInput>
  </div>
</template>

<script setup>
import { useNuxtApp } from '#app'
import PremiumDashboardService from '@baserow_premium/services/dashboard'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  dashboard: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update-dashboard'])

const { $client } = useNuxtApp()

const update = async (key, value) => {
  try {
    // Optimistically apply the change, the request is expected to succeed.
    emit('update-dashboard', { [key]: value })
    await PremiumDashboardService($client).update(props.dashboard.id, {
      [key]: value,
    })
  } catch (error) {
    // Roll the change back if it didn't.
    emit('update-dashboard', { [key]: !value })
    notifyIf(error, 'application')
  }
}

</script>
