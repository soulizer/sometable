<template>
  <div class="logo">
    <img :src="getLogoUrl()" v-bind="$attrs" />
  </div>
</template>

<script>
import baserowLogo from '@baserow/modules/core/static/img/logo.svg?url'

export default {
  name: 'EnterpriseLogo',
  methods: {
    getLogoUrl(parent) {
      const settings = this.$store.getters['settings/get']
      if (settings.co_branding_logo) {
        return settings.co_branding_logo.url
      }
      return baserowLogo
    },
  },
}
</script>
