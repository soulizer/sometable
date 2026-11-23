<template>
  <NuxtLoadingIndicator :throttle="500" :hide-delay="0" />
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useHead } from '#imports'
import { useStore } from 'vuex'
import head from '@baserow/modules/core/head'

const store = useStore()

// Instance level favicon. The keys match the defaults in `core/head.js`, so
// unhead replaces them. A builder application can still override them with its
// own favicon on public pages.
const faviconLinks = computed(() => {
  const file = store.getters['settings/get']?.favicon
  if (!file?.url) {
    return []
  }
  return head.link
    .filter((link) => link.rel === 'icon')
    .map((link) => ({
      key: link.key,
      rel: 'icon',
      type: file.mime_type || 'image/png',
      href: file.url,
    }))
})

useHead(computed(() => ({ link: faviconLinks.value })))
</script>
