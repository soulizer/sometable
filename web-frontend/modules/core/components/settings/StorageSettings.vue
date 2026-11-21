<template>
  <div class="admin-settings__group storage-settings">
    <h2 class="admin-settings__group-title">
      {{ $t('storageSettings.title') }}
    </h2>

    <Alert type="warning" class="margin-bottom-2">
      {{ $t('storageSettings.switchWarning') }}
    </Alert>

    <div class="admin-settings__item">
      <div class="admin-settings__label">
        <div class="admin-settings__name">
          {{ $t('storageSettings.typeLabel') }}
        </div>
        <div class="admin-settings__description">
          {{ $t('storageSettings.typeDescription') }}
        </div>
      </div>
      <div class="admin-settings__control">
        <SwitchInput
          :value="form.type === 's3'"
          @input="form.type = $event ? 's3' : 'local'"
        >
          {{ $t('storageSettings.useObjectStorage') }}
        </SwitchInput>
      </div>
    </div>

    <template v-if="form.type === 's3'">
      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.endpointLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.endpointDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.endpoint_url" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.bucketLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.bucketDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.bucket_name" size="large" required></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.regionLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.regionDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.region_name" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.locationLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.locationDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.location" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.accessKeyLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.accessKeyDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.access_key_id" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.secretKeyLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.secretKeyDescription') }}
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

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.customDomainLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.customDomainDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <FormInput v-model="form.custom_domain" size="large"></FormInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.querystringAuthLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.querystringAuthDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <SwitchInput v-model="form.querystring_auth">
            {{ $t('storageSettings.enabled') }}
          </SwitchInput>
        </div>
      </div>

      <div class="admin-settings__item">
        <div class="admin-settings__label">
          <div class="admin-settings__name">
            {{ $t('storageSettings.addressingStyleLabel') }}
          </div>
          <div class="admin-settings__description">
            {{ $t('storageSettings.addressingStyleDescription') }}
          </div>
        </div>
        <div class="admin-settings__control">
          <SwitchInput
            :value="form.addressing_style === 'path'"
            @input="
              form.addressing_style = $event ? 'path' : 'virtual'
            "
          >
            {{ $t('storageSettings.pathStyle') }}
          </SwitchInput>
        </div>
      </div>
    </template>

    <div class="admin-settings__item">
      <div class="admin-settings__label">
        <div class="admin-settings__name">
          {{ $t('storageSettings.currentStatus') }}
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
        {{ $t('storageSettings.testConnection') }}
      </Button>
      <Button
        type="primary"
        :loading="saving"
        :disabled="testing"
        @click="save"
      >
        {{ $t('storageSettings.save') }}
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
    return t('storageSettings.localStatus', { path: localPath.value })
  }
  return t('storageSettings.objectStatus', {
    bucket: form.bucket_name || '-',
    location: form.location || '-',
  })
})

const sourceText = computed(() => {
  return t(`storageSettings.source_${source.value}`)
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
    const { data } = await $client.get('/settings/storage/')
    applyConfig(data)
  } catch {
    showMessage(t('storageSettings.loadError'), 'error')
  }
}

function validate() {
  if (form.type !== 's3') return true
  if (!form.bucket_name.trim()) {
    showMessage(t('storageSettings.bucketRequired'), 'error')
    return false
  }
  if (
    !hasCredentials.value &&
    (!form.access_key_id.trim() || !form.secret_access_key)
  ) {
    showMessage(t('storageSettings.credentialsRequired'), 'error')
    return false
  }
  return true
}

async function save() {
  if (!validate()) return
  saving.value = true
  message.value = ''
  try {
    const { data } = await $client.put('/settings/storage/', { ...form })
    applyConfig(data)
    showMessage(t('storageSettings.saved'))
  } catch (error) {
    showMessage(
      error?.response?.data?.error || t('storageSettings.saveError'),
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
    await $client.post('/settings/storage/test/', { ...form })
    showMessage(t('storageSettings.testSucceeded'))
  } catch (error) {
    showMessage(
      error?.response?.data?.error || t('storageSettings.testFailed'),
      'error'
    )
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>
