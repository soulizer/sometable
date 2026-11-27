<template>
  <div class="layout__col-2-scroll">
    <div class="admin-health">
      <h1>
        {{ $t('health.title') }}
      </h1>
      <div class="admin-health__group">
        <div class="admin-health__description">
          {{ $t('health.description') }}
        </div>
        <div>
          <template v-if="loading">
            <div
              v-for="index in 8"
              :key="`skeleton-${index}`"
              class="skeleton admin-health__check-item"
              aria-hidden="true"
            >
              <div class="admin-health__check-item-label">
                <div class="admin-health__check-item-name">
                  <SkeletonBlock width="160px"></SkeletonBlock>
                </div>
              </div>
              <div class="admin-health__icon">
                <SkeletonBlock
                  width="18px"
                  height="18px"
                  shape="circle"
                ></SkeletonBlock>
              </div>
            </div>
          </template>
          <div
            v-for="(status, checkName) in healthChecks"
            :key="checkName"
            class="admin-health__check-item"
          >
            <div class="admin-health__check-item-label">
              <div class="admin-health__check-item-name">
                {{ healthCheckName(checkName) }}
              </div>
            </div>
            <div
              class="admin-health__icon"
              :class="status !== 'working' ? 'warning' : ''"
            >
              <i
                :class="
                  status === 'working'
                    ? 'iconoir-check admin-health__icon--success'
                    : 'iconoir-cancel admin-health__icon--fail'
                "
              ></i>
              <div
                v-if="status !== 'working'"
                class="admin-health__check-item-description"
              >
                {{ healthCheckStatus(status) }}
              </div>
            </div>
          </div>
          <div class="admin-health__check-item">
            <div class="admin-health__check-item-label">
              <div class="admin-health__check-item-name">
                {{ $t('health.celeryQueueSize') }}
              </div>
            </div>
            <span v-skeleton="{ loading, width: '24px' }">{{
              celeryQueueSize
            }}</span>
          </div>
          <div class="admin-health__check-item">
            <div class="admin-health__check-item-label">
              <div class="admin-health__check-item-name">
                {{ $t('health.celeryExportQueueSize') }}
              </div>
            </div>
            <span v-skeleton="{ loading, width: '24px' }">{{
              celeryExportQueueSize
            }}</span>
          </div>
        </div>
      </div>
      <div class="admin-health__group">
        <EmailTester></EmailTester>
      </div>
      <div class="admin-health__group">
        <h2>{{ $t('health.errorTesterTitle') }}</h2>
        <Button @click="error()">{{ $t('health.throwError') }}</Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import '@baserow/modules/core/assets/scss/admin.scss'
import { computed } from 'vue'
import { useHead } from '#imports'
import { usePageAsyncData } from '@baserow/modules/core/composables/usePageAsyncData'
import HealthService from '@baserow/modules/core/services/health'
import EmailTester from '@baserow/modules/core/components/health/EmailTester.vue'

// Page meta
definePageMeta({
  layout: 'app',
  middleware: 'staff',
})

// Access Baserow client from Nuxt app
const { $client, $i18n } = useNuxtApp()

useHead({ title: $i18n.t('health.title') })

const { data, loading } = await usePageAsyncData('health', async () => {
  const res = await HealthService($client).getAll()
  return res.data
})

const healthChecks = computed(() => data.value?.checks ?? [])
const celeryQueueSize = computed(() => data.value?.celery_queue_size ?? 0)
const celeryExportQueueSize = computed(
  () => data.value?.celery_export_queue_size ?? 0
)

// Methods
const healthCheckLabels = {
  DatabaseBackend: 'databaseBackend',
  'Cache backend: default': 'cacheBackendDefault',
  'Cache backend: generated-models': 'cacheBackendGeneratedModels',
  MigrationsHealthCheck: 'migrations',
  RedisHealthCheck: 'redis',
  CeleryPingHealthCheck: 'celeryPing',
  DiskUsage: 'diskUsage',
  MemoryUsage: 'memoryUsage',
  S3Boto3StorageHealthCheck: 'objectStorage',
  DebugModeHealthCheck: 'debugMode',
  DefaultFileStorageHealthCheck: 'defaultFileStorage',
  ChatRunsHealthCheck: 'chatRuns',
}

function healthCheckName(checkName) {
  const key = healthCheckLabels[checkName]
  return key
    ? $i18n.t(`health.checks.${key}`)
    : camelCaseToSpaceSeparated(checkName)
}

function healthCheckStatus(status) {
  return status === 'working' ? $i18n.t('health.working') : status
}

function camelCaseToSpaceSeparated(str) {
  if (!str) return 'unknown'
  return str.toString().replace(/([A-Z])/g, ' $1')
}

function error() {
  setTimeout(() => {
    throw new Error('Health check error')
  }, 1)
}
</script>
