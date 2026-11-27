<template>
  <div class="layout__col-2-scroll">
    <div class="admin-settings">
      <h1>{{ $t('adminBackups.title') }}</h1>

      <div class="admin-settings__group">
        <h2 class="admin-settings__group-title">
          {{ $t('adminBackups.scheduleTitle') }}
        </h2>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('adminBackups.scopeLabel') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('adminBackups.scopeDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <RadioGroup
              v-model="form.scope"
              :options="scopeOptions"
            ></RadioGroup>
          </div>
        </div>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('adminBackups.frequencyLabel') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('adminBackups.frequencyDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <RadioGroup
              v-model="form.frequency"
              :options="frequencyOptions"
            ></RadioGroup>
          </div>
        </div>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('adminBackups.hourLabel') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <FormInput
              v-model="form.hour"
              type="number"
              size="large"
              min="0"
              max="23"
            />
          </div>
        </div>
        <div v-if="form.frequency === 'weekly'" class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('adminBackups.dowLabel') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <Dropdown v-model="form.day_of_week" size="large">
              <DropdownItem
                v-for="(day, index) in days"
                :key="index"
                :name="day"
                :value="String(index)"
                >{{ day }}</DropdownItem
              >
            </Dropdown>
          </div>
        </div>
        <div v-if="form.frequency === 'monthly'" class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('adminBackups.domLabel') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <FormInput
              v-model="form.day_of_month"
              type="number"
              size="large"
              min="1"
              max="31"
            />
          </div>
        </div>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('adminBackups.keepLabel') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('adminBackups.keepDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <FormInput v-model="form.keep" type="number" size="large" min="1" />
          </div>
        </div>
        <div class="admin-settings__item">
          <div class="admin-settings__label"></div>
          <div class="admin-settings__control">
            <Button type="primary" :loading="saving" @click="save">
              {{ $t('adminBackups.save') }}
            </Button>
          </div>
        </div>
      </div>

      <StorageSettings
        namespace="backupStorageSettings"
        endpoint-base="/settings/backup-storage/"
        :media-extras="false"
      />

      <div class="admin-settings__group">
        <h2 class="admin-settings__group-title">
          {{ $t('adminBackups.listTitle') }}
        </h2>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__description">
              {{ $t('adminBackups.listDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <Button :loading="running" @click="runNow">
              {{ $t('adminBackups.runNow') }}
            </Button>
          </div>
        </div>
        <Alert v-if="message" :type="messageType" class="margin-bottom-2">
          {{ message }}
        </Alert>
        <table class="admin-backups__table">
          <thead>
            <tr>
              <th>{{ $t('adminBackups.tableTime') }}</th>
              <th>{{ $t('adminBackups.tableScope') }}</th>
              <th>{{ $t('adminBackups.tableSize') }}</th>
              <th>{{ $t('adminBackups.tableContent') }}</th>
              <th>{{ $t('adminBackups.tableRemote') }}</th>
              <th>{{ $t('adminBackups.tableActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingBackups">
              <td colspan="6">
                <div class="admin-backups__loading">
                  {{ $t('adminBackups.loading') }}
                </div>
              </td>
            </tr>
            <template v-else>
              <tr v-for="item in backups" :key="item.id">
                <td>{{ formatTime(item.created_at) }}</td>
                <td>{{ scopeLabel(item.scope) }}</td>
                <td>{{ sizeLabel(item) }}</td>
                <td>{{ contentLabel(item) }}</td>
                <td>
                  {{
                    item.remote
                      ? $t('adminBackups.remoteYes')
                      : $t('adminBackups.remoteNo')
                  }}
                </td>
                <td>
                  <Button
                    type="secondary"
                    size="small"
                    :loading="restoringId === item.id"
                    @click="askRestore(item)"
                  >
                    {{ $t('adminBackups.restore') }}
                  </Button>
                </td>
              </tr>
              <tr v-if="!backups.length">
                <td colspan="6">{{ $t('adminBackups.empty') }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <Modal ref="restoreModal">
        <h2 class="box__title">{{ $t('adminBackups.restoreTitle') }}</h2>
        <Alert type="warning" class="margin-bottom-2">
          {{ $t('adminBackups.restoreDescription') }}
        </Alert>
        <div v-if="restoringId !== null" class="margin-bottom-2">
          <ProgressBar :value="restoreProgress" :status="restoreStatusLabel" />
        </div>
        <Alert v-if="restoreError" type="error" class="margin-bottom-2">
          {{ restoreError }}
        </Alert>
        <FormGroup
          :label="$t('adminBackups.restoreConfirmLabel')"
          :helper-text="$t('adminBackups.restoreConfirmHelp')"
          class="margin-bottom-2"
        >
          <FormInput
            v-model="restoreConfirm"
            :placeholder="pendingRestore ? pendingRestore.id : ''"
            size="large"
          />
        </FormGroup>
        <div class="actions">
          <div class="align-right">
            <Button
              :disabled="restoringId !== null"
              @click="$refs.restoreModal?.hide()"
            >
              {{ $t('adminBackups.cancel') }}
            </Button>
            <Button
              type="danger"
              :loading="restoringId !== null"
              :disabled="
                restoringId !== null ||
                !pendingRestore ||
                restoreConfirm !== pendingRestore.id
              "
              @click="restore"
            >
              {{ $t('adminBackups.restoreConfirm') }}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import StorageSettings from '@baserow/modules/core/components/settings/StorageSettings.vue'
import SettingsService from '@baserow/modules/core/services/settings'
import { useHead } from '#imports'
import { useNuxtApp } from '#app'
import { useI18n } from 'vue-i18n'

const RESTORE_POLL_INTERVAL = 2000

definePageMeta({
  layout: 'app',
  middleware: 'staff',
})

const { $client } = useNuxtApp()
const { t } = useI18n()

const settings = ref({})
const backups = ref([])
const loadingBackups = ref(true)
const saving = ref(false)
const running = ref(false)
const restoringId = ref(null)
const restoreModal = ref(null)
const message = ref('')
const messageType = ref('success')
const pendingRestore = ref(null)
const restoreConfirm = ref('')
const restoreProgress = ref(0)
const restoreStatus = ref('')
const restoreError = ref('')
const savedScope = ref('all')
let restorePollTimer = null

const form = reactive({
  scope: 'all',
  frequency: 'daily',
  hour: 3,
  day_of_week: '0',
  day_of_month: '1',
  keep: 7,
})

useHead({ title: t('adminBackups.title') })

const scopeLabels = computed(() => ({
  all: t('adminBackups.scopeAll'),
  database: t('adminBackups.scopeDatabase'),
  object_storage: t('adminBackups.scopeObjectStorage'),
}))

const scopeOptions = computed(() =>
  Object.entries(scopeLabels.value).map(([value, label]) => ({ value, label }))
)

const restoreStatusLabel = computed(() => {
  if (restoreStatus.value === 'pending') {
    return t('adminBackups.restoreQueued')
  }
  if (restoreStatus.value === 'running') {
    return t('adminBackups.restoreRunning')
  }
  return ''
})

const frequencyOptions = computed(() => [
  { value: 'disabled', label: t('adminBackups.frequencyDisabled') },
  { value: 'daily', label: t('adminBackups.frequencyDaily') },
  { value: 'weekly', label: t('adminBackups.frequencyWeekly') },
  { value: 'monthly', label: t('adminBackups.frequencyMonthly') },
])

const days = computed(() =>
  t('adminBackups.days')
    .split(',')
    .map((name) => name.trim())
)

function scopeLabel(scope) {
  return scopeLabels.value[scope] || scope
}

function formatTime(value) {
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function sizeLabel(item) {
  let total = 0
  if (item.database) total += item.database.bytes || 0
  if (item.media) total += item.media.bytes || 0
  if (item.object_storage) total += item.object_storage.bytes || 0
  if (!total && item.remote) total = item.remote.bytes || 0
  if (total < 1024) return `${total} B`
  if (total < 1024 * 1024) return `${(total / 1024).toFixed(1)} KB`
  if (total < 1024 * 1024 * 1024) {
    return `${(total / 1024 / 1024).toFixed(1)} MB`
  }
  return `${(total / 1024 / 1024 / 1024).toFixed(2)} GB`
}

function contentLabel(item) {
  const parts = []
  if (item.database) parts.push(t('adminBackups.contentDatabase'))
  if (item.media) parts.push(t('adminBackups.contentMedia'))
  if (item.object_storage)
    parts.push(
      `${t('adminBackups.contentObjectStorage')} (${item.object_storage.count})`
    )
  return parts.join(' / ') || '-'
}

function showMessage(text, type = 'success') {
  message.value = text
  messageType.value = type
}

async function load() {
  loadingBackups.value = true
  try {
    const { data } = await $client.get('/settings/backups/')
    backups.value = data
  } catch (error) {
    showMessage(
      error?.response?.data?.error || t('adminBackups.loadError'),
      'error'
    )
  } finally {
    loadingBackups.value = false
  }
}

async function loadSettings() {
  const { data } = await $client.get('/settings/')
  settings.value = data
  form.scope = data.backup_scope
  form.frequency = data.backup_frequency
  form.hour = Number(data.backup_hour)
  form.day_of_week = String(data.backup_dow)
  form.day_of_month = String(data.backup_dom)
  form.keep = Number(data.backup_keep)
  savedScope.value = data.backup_scope
}

async function save() {
  saving.value = true
  try {
    await $client.patch('/settings/update/', {
      backup_scope: form.scope,
      backup_frequency: form.frequency,
      backup_hour: form.hour,
      backup_dow: form.day_of_week,
      backup_dom: form.day_of_month,
      backup_keep: form.keep,
    })
    savedScope.value = form.scope
    showMessage(t('adminBackups.saved'))
  } catch (error) {
    showMessage(
      error?.response?.data?.error || t('adminBackups.saveError'),
      'error'
    )
  } finally {
    saving.value = false
  }
}

async function runNow() {
  running.value = true
  try {
    await $client.post('/settings/backups/', { scope: savedScope.value })
    showMessage(t('adminBackups.runQueued'))
    setTimeout(load, 4000)
  } catch (error) {
    showMessage(
      error?.response?.data?.error || t('adminBackups.runError'),
      'error'
    )
  } finally {
    running.value = false
  }
}

function askRestore(item) {
  pendingRestore.value = item
  restoreConfirm.value = ''
  restoreProgress.value = 0
  restoreStatus.value = ''
  restoreError.value = ''
  restoreModal.value.show()
}

function stopRestorePolling() {
  if (restorePollTimer !== null) {
    clearTimeout(restorePollTimer)
    restorePollTimer = null
  }
}

function finishRestore(success, detail = '') {
  stopRestorePolling()
  pendingRestore.value = null
  restoringId.value = null
  restoreStatus.value = ''
  restoreError.value = success ? '' : detail || t('adminBackups.restoreError')
  if (success) {
    restoreModal.value?.hide()
    showMessage(t('adminBackups.restoreOk'))
    load()
  } else {
    showMessage(restoreError.value, 'error')
  }
}

async function pollRestoreStatus(token) {
  try {
    const { data } =
      await SettingsService($client).getBackupRestoreStatus(token)
    restoreProgress.value = Number(data.progress) || 0
    restoreStatus.value = data.status
    if (data.status === 'success') {
      finishRestore(true)
    } else if (data.status === 'failed') {
      finishRestore(false, data.message || t('adminBackups.restoreError'))
    } else {
      restorePollTimer = setTimeout(
        () => pollRestoreStatus(token),
        RESTORE_POLL_INTERVAL
      )
    }
  } catch (error) {
    finishRestore(
      false,
      error?.response?.data?.message ||
        error?.response?.data?.error ||
        t('adminBackups.restoreError')
    )
  }
}

async function restore() {
  if (!pendingRestore.value) return
  if (restoreConfirm.value !== pendingRestore.value.id) return
  restoringId.value = pendingRestore.value.id
  restoreError.value = ''
  restoreProgress.value = 0
  restoreStatus.value = 'pending'
  try {
    const { data } = await SettingsService($client).restoreBackup(
      pendingRestore.value.id,
      restoreConfirm.value
    )
    await pollRestoreStatus(data.token)
  } catch (error) {
    finishRestore(
      false,
      error?.response?.data?.error || t('adminBackups.restoreError')
    )
  }
}

onMounted(async () => {
  await Promise.all([loadSettings(), load()])
})

onUnmounted(stopRestorePolling)
</script>
