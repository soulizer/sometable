<template>
  <Alert v-if="error.visible" type="error">
    <template #title>{{ error.title }}</template>
    <p>{{ error.message }}</p>
    <ErrorDetails v-if="error.details" :details="error.details" />
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>
  </Alert>
</template>

<script>
import ErrorDetails from '@baserow/modules/core/components/ErrorDetails.vue'

/**
 * This component works the best if the parent has the error mixin.
 */
export default {
  name: 'Error',
  components: {
    ErrorDetails,
  },
  props: {
    error: {
      required: true,
      type: Object,
    },
  },
}
</script>
