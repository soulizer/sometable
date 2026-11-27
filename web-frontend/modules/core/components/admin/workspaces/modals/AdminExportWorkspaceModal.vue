<template>
  <Modal ref="modal">
    <h2 class="box__title">
      {{ $t('exportWorkspaceModal.title') }} {{ workspace.name }}
    </h2>
    <p>{{ $t('exportWorkspaceModal.description') }}</p>
    <Error :error="error"></Error>
    <div>
      <FormGroup
        small-label
        :label="$t('exportWorkspaceForm.exportSettingsLabel')"
      >
        <Checkbox v-model="onlyStructure" :disabled="jobIsRunning">
          {{ $t('exportWorkspaceForm.onlyStructureLabel') }}
          <HelpIcon
            class="margin-left-1"
            :tooltip="$t('exportWorkspaceForm.onlyStructureDescription')"
            @mousedown.stop
            @click.stop
          />
        </Checkbox>
      </FormGroup>
      <div
        class="export-workspace__button-section"
        :class="{
          'export-workspace__button-section--with-progress':
            jobIsRunning || jobIsFinished,
        }"
      >
        <div
          v-if="jobIsRunning || jobIsFinished"
          class="export-workspace__progress"
        >
          <ProgressBar
            :value="job.progress_percentage"
            :status="jobHumanReadableState"
          />
        </div>
        <Button
          size="large"
          :loading="loading || jobIsRunning"
          :disabled="loading || jobIsRunning"
          @click="submit"
        >
          {{ $t('exportWorkspaceModal.export') }}
        </Button>
      </div>
      <div v-if="jobIsFinished && job.url" class="export-workspace__export">
        <div class="export-workspace__info">
          <div class="export-workspace__name">{{ workspace.name }}</div>
        </div>
        <div class="export-workspace__actions">
          <DownloadLink
            :url="job.url"
            :filename="job.exported_file_name"
            :loading-class="'button--loading'"
          >
            {{ $t('exportWorkspaceModal.download') }}
          </DownloadLink>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import job from '@baserow/modules/core/mixins/job'
import WorkspacesAdminService from '@baserow/modules/core/services/admin/workspaces'
import { ExportApplicationsJobType } from '@baserow/modules/core/jobTypes'
import {
  EXPORT_SERIALIZED_EXPORTING,
  EXPORT_SERIALIZED_EXPORTING_TABLE,
  EXPORT_WORKSPACE_CREATE_ARCHIVE,
} from '@baserow/modules/core/constants'

export default {
  name: 'AdminExportWorkspaceModal',
  mixins: [modal, error, job],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      onlyStructure: false,
      loading: false,
    }
  },
  methods: {
    show(...args) {
      this.onlyStructure = false
      this.job =
        this.$store.getters['job/getUnfinishedJobs'].find(
          (job) =>
            job.type === ExportApplicationsJobType.getType() &&
            job.workspace_id === this.workspace.id
        ) || null
      this.hideError()
      return modal.methods.show.call(this, ...args)
    },
    async submit() {
      if (this.loading || this.jobIsRunning) return
      this.loading = true
      this.hideError()
      try {
        const { data: createdJob } = await WorkspacesAdminService(
          this.$client
        ).exportAsync(this.workspace.id, {
          application_ids: [],
          only_structure: this.onlyStructure,
        })
        await this.createAndMonitorJob(createdJob)
      } catch (e) {
        this.handleError(e)
      } finally {
        this.loading = false
      }
    },
    getCustomHumanReadableJobState(jobState) {
      if (jobState.startsWith(EXPORT_SERIALIZED_EXPORTING_TABLE)) {
        return this.$t('exportWorkspaceModal.exportingTableState', {
          table: jobState.replace(EXPORT_SERIALIZED_EXPORTING_TABLE, ''),
        })
      }
      if (jobState === EXPORT_WORKSPACE_CREATE_ARCHIVE) {
        return this.$t('exportWorkspaceModal.exportingCreateArchiveState')
      }
      if (jobState === EXPORT_SERIALIZED_EXPORTING) {
        return this.$t('exportWorkspaceModal.exportingState')
      }
      return ''
    },
    onJobFailed() {
      this.showError(
        this.$t('clientHandler.notCompletedTitle'),
        this.job.human_readable_error
      )
    },
  },
}
</script>
