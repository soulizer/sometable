<template>
  <div class="admin-settings__group storage-settings">
    <h2 class="admin-settings__group-title">
      {{ tr('title') }}
    </h2>

    <Alert type="warning" class="margin-bottom-2">
      {{ tr('switchWarning') }}
    </Alert>

    <div class="admin-settings__item">
      <div class="admin-settings__label">
        <div class="admin-settings__name">
          {{ tr('typeLabel') }}
        </div>
        <div class="admin-settings__description">
          {{ tr('typeDescription') }}
        </div>
      </div>
      <div class="admin-settings__control">
        <SwitchInput
          :value="form.type === 's3'"
          @input="form.type = $event ? 's3' : 'local'"
        >
          {{ tr('useObjectStorage') }}
        </SwitchInput>
      </div>
    </div>

    <template v-if="form.type === 's3'">
      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('endpointLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('endpointDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.endpoint_url" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('bucketLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('bucketDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.bucket_name" size="large" required></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('regionLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('regionDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.region_name" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('locationLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('locationDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.location" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('accessKeyLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('accessKeyDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.access_key_id" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('secretKeyLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('secretKeyDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput
            v-model="form.secret_access_key"
            type="password"
            size="large"
          ></FormInput>
        </div>
      </div>

      <div v-if="mediaExtras" class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('customDomainLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('customDomainDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.custom_domain" size="large"></FormInput>
        </div>
      </div>

      <div v-if="mediaExtras" class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('querystringAuthLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('querystringAuthDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <SwitchInput v-model="form.querystring_auth">
            {{ tr('enabled') }}
          </SwitchInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ tr('addressingStyleLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ tr('addressingStyleDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <SwitchInput
            :value="form.addressing_style === 'path'"
            @input="
              form.addressing_style = $event ? 'path' : 'virtual'
            "
          >
            {{ tr('pathStyle') }}
          </SwitchInput>
        </div>
      </div>
    </template>

    <div class="admin-settings__item">
      <div class="admin-settings__label">
        <div class="admin-settings__name">
          {{ tr('currentStatus') }}
        </div>
        <div class="admin-settings__description">{{ sourceText }}</div>
      </div>
      <div class="admin-settings__control storage-settings__status">
        {{ statusText }}
      </div>
    </div>

    <div class="storage-settings__actions">
      <Button
        type="secondary"
        :loading="testing"
        :disabled="saving"
        @click="testConnection"
      >
        {{ tr('testConnection') }}
      </Button>
      <Button
        type="primary"
        :loading="saving"
        :disabled="testing"
        @click="save"
      >
        {{ tr('save') }}
      </Button>
    </div>

    <Alert v-if="message" :type="messageType" class="margin-top-2">
      {{ message }}
    </Alert>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useNuxtApp } from '#app'
import { useI18n } from 'vue-i18n'

const { $client } = useNuxtApp()
const { t } = useI18n()

const props = defineProps({
  endpointBase: { type: String, default: '/settings/storage/' },
  namespace: { type: String, default: 'storageSettings' },
  mediaExtras: { type: Boolean, default: true },
})

const tr = (key, values) => t(`${props.namespace}.${key}`, values)

const form = reactive({
  type: 'local',
  endpoint_url: '',
  bucket_name: '',
  region_name: '',
  location: '',
  access_key_id: '',
  secret_access_key: '',
  custom_domain: '',
  addressing_style: 'path',
  querystring_auth: true,
})

const source = ref('default')
const localPath = ref('')
const hasCredentials = ref(false)
const saving = ref(false)
const testing = ref(false)
const message = ref('')
const messageType = ref('success')

const statusText = computed(() => {
  if (form.type === 'local') {
    return tr('localStatus', { path: localPath.value })
  }
  return tr('objectStatus', {
    bucket: form.bucket_name || '-',
    location: form.location || '-',
  })
})

const sourceText = computed(() => {
  return tr(`source_${source.value}`)
})

function showMessage(text, type = 'success') {
  message.value = text
  messageType.value = type
}

function applyConfig(data) {
  source.value = data.source || 'default'
  localPath.value = data.local_path || ''
  hasCredentials.value = !!data.has_credentials
  Object.assign(form, {
    type: data.type || 'local',
    endpoint_url: data.endpoint_url || '',
    bucket_name: data.bucket_name || '',
    region_name: data.region_name || '',
    location: data.location || '',
    custom_domain: data.custom_domain || '',
    addressing_style: data.addressing_style || 'path',
    querystring_auth: data.querystring_auth !== false,
    // The secret is never sent back to the browser.
    access_key_id: '',
    secret_access_key: '',
  })
}

async function load() {
  try {
    const { data } = await $client.get(props.endpointBase)
    applyConfig(data)
  } catch {
    showMessage(tr('loadError'), 'error')
  }
}

function validate() {
  if (form.type !== 's3') return true
  if (!form.bucket_name.trim()) {
    showMessage(tr('bucketRequired'), 'error')
    return false
  }
  if (
    !hasCredentials.value &&
    (!form.access_key_id.trim() || !form.secret_access_key)
  ) {
    showMessage(tr('credentialsRequired'), 'error')
    return false
  }
  return true
}

async function save() {
  if (!validate()) return
  saving.value = true
  message.value = ''
  try {
    const { data } = await $client.put(props.endpointBase, { ...form })
    applyConfig(data)
    showMessage(tr('saved'))
  } catch (error) {
    showMessage(
      error?.response?.data?.error || tr('saveError'),
      'error'
    )
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  if (!validate()) return
  testing.value = true
  message.value = ''
  try {
    await $client.post(`${props.endpointBase}test/`, { ...form })
    showMessage(tr('testSucceeded'))
  } catch (error) {
    showMessage(
      error?.response?.data?.error || tr('testFailed'),
      'error'
    )
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>
