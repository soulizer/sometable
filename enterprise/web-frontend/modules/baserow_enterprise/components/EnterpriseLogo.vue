<template>
  <div v-if="getLogoUrl()" class="logo">
    <img :src="getLogoUrl()" v-bind="$attrs" />
  </div>
</template>

<script>
export default {
  name: 'EnterpriseLogo',
  methods: {
    getLogoUrl() {
      const settings = this.$store.getters['settings/get']
      // No default brand icon: only show a logo when one has been configured.
      return settings.co_branding_logo ? settings.co_branding_logo.url : null
    },
  },
}
</script>
