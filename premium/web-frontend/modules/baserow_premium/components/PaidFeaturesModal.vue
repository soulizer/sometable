<template>
  <span />
</template>

<script>
export default {
  name: 'PaidFeaturesModal',
  props: {
    workspace: {
      type: [Object, null],
      required: false,
      default: null,
    },
    initialSelectedType: {
      type: String,
      required: false,
      default: null,
    },
  },
  methods: {
    show() {},
    hide() {},
    toggle() {},
  },
}
</script>
