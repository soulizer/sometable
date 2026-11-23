<template>
  <details class="error-details">
    <summary class="error-details__summary">
      {{ $t('clientHandler.errorDetails') }}
    </summary>
    <dl class="error-details__list">
      <template v-for="(value, key) in formattedDetails" :key="key">
        <dt class="error-details__term">{{ label(key) }}</dt>
        <dd class="error-details__value">
          <pre class="error-details__pre">{{ value }}</pre>
        </dd>
      </template>
    </dl>
    <button
      type="button"
      class="error-details__copy"
      :disabled="copying"
      @click="copyDetails"
    >
      {{ copying ? $t('clientHandler.copyDetailsDone') : $t('clientHandler.copyDetails') }}
    </button>
  </details>
</template>

<script>
const DETAIL_KEYS = ['code', 'status', 'method', 'url', 'detail']

const LABEL_KEYS = {
  code: 'errorCode',
  status: 'httpStatus',
  method: 'method',
  url: 'request',
  detail: 'serverResponse',
}

export default {
  name: 'ErrorDetails',
  props: {
    details: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      copying: false,
    }
  },
  computed: {
    formattedDetails() {
      const result = {}
      for (const key of DETAIL_KEYS) {
        const value = this.details[key]
        if (value === null || value === undefined || value === '') {
          continue
        }
        result[key] =
          typeof value === 'string' ? value : this.stringify(value)
      }
      return result
    },
  },
  methods: {
    label(key) {
      return this.$t(`clientHandler.${LABEL_KEYS[key] || key}`)
    },
    stringify(value) {
      try {
        return JSON.stringify(value, null, 2)
      } catch {
        return String(value)
      }
    },
    async copyDetails() {
      const lines = Object.entries(this.formattedDetails).map(
        ([key, value]) => `${this.label(key)}: ${value}`
      )
      const text = lines.join('\n')
      try {
        await navigator.clipboard.writeText(text)
      } catch {
        const textarea = document.createElement('textarea')
        textarea.value = text
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      }
      this.copying = true
      setTimeout(() => {
        this.copying = false
      }, 2000)
    },
  },
}
</script>
