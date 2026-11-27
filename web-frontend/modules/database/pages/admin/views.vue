<template>
  <ViewsAdminTable></ViewsAdminTable>
</template>

<script>
import '@baserow/modules/core/assets/scss/admin.scss'
import '@baserow/modules/core/assets/scss/grid.scss'
import { useHead } from '#imports'
import ViewsAdminTable from '@baserow/modules/database/components/admin/views/ViewsAdminTable'

definePageMeta({
  layout: 'app',
  middleware: 'staff',
})

export default {
  components: { ViewsAdminTable },
  setup() {
    const { $i18n } = useNuxtApp()
    useHead({ title: $i18n.t('viewsAdmin.title') })
  },
}
</script>
