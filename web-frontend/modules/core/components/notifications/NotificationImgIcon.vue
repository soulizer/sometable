<template>
  <img :src="icon" loading="lazy" alt="" />
</template>

<script>
export default {
  props: {
    icon: {
      type: String,
      required: true,
    },
  },
}
</script>
