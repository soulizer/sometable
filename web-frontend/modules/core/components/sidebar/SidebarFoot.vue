<template>
  <div class="sidebar__section sidebar__section--bottom">
    <div class="sidebar__foot sidebar__foot--no-logo">
      <div class="sidebar__foot-links">
        <div v-if="exportJobs.length > 0" class="sidebar__foot-action">
          <a
            ref="exportJobsLink"
            class="sidebar__foot-link sidebar__foot-link--with-badge"
            role="button"
            tabindex="0"
            :title="$t('globalExports.title')"
            @click="$refs.exportJobsContext?.toggle($refs.exportJobsLink)"
            @keydown.enter.prevent="
              $refs.exportJobsContext?.toggle($refs.exportJobsLink)
            "
            @keydown.space.prevent="
              $refs.exportJobsContext?.toggle($refs.exportJobsLink)
            "
          >
            <i class="sidebar__foot-link-icon iconoir-download"></i>
            <span
              v-if="unfinishedExportCount > 0"
              class="sidebar__foot-link-badge"
              >{{ unfinishedExportCount }}</span
            >
          </a>
          <Context ref="exportJobsContext" overflow-scroll>
            <div class="context__menu-title">
              {{ $t('globalExports.title') }}
            </div>
            <ul class="context__menu">
              <li
                v-for="exportJob in exportJobs"
                :key="'export-job-' + exportJob.id"
                class="context__menu-item"
              >
                <DownloadLink
                  v-if="exportJob.state === 'finished' && exportJob.url"
                  class="context__menu-item-link"
                  :url="exportJob.url"
                  :filename="exportJob.exported_file_name"
                  loading-class="button--loading"
                  @click="$refs.exportJobsContext?.hide()"
                >
                  <i class="context__menu-item-icon iconoir-download"></i>
                  {{ exportWorkspaceName(exportJob) }}
                </DownloadLink>
                <span v-else class="context__menu-item-link">
                  <i class="context__menu-item-icon iconoir-clock"></i>
                  {{ exportWorkspaceName(exportJob) }} ·
                  {{ exportProgressLabel(exportJob) }}
                </span>
              </li>
            </ul>
          </Context>
        </div>
        <a
          class="sidebar__foot-link"
          :class="{
            'sidebar__foot-link--loading': undoLoading,
          }"
          @click="undo(false)"
        >
          <i class="sidebar__foot-link-icon iconoir-undo"></i>
        </a>
        <a
          class="sidebar__foot-link"
          :class="{
            'sidebar__foot-link--loading': redoLoading,
          }"
          @click="redo(false)"
        >
          <i class="sidebar__foot-link-icon iconoir-redo"></i>
        </a>
        <template v-if="collapsed">
          <div class="sidebar__foot-separator"></div>
          <a class="sidebar__foot-link" @click="$emit('set-col1-width', 240)">
            <i class="sidebar__foot-link-icon baserow-icon-sidebar"></i>
          </a>
        </template>
      </div>
      <div
        v-if="!collapsed && width > 224"
        class="sidebar__foot-links sidebar__foot-links--end"
      >
        <div class="sidebar__foot-separator"></div>
        <a class="sidebar__foot-link" @click="$emit('set-col1-width', 52)">
          <i class="sidebar__foot-link-icon baserow-icon-sidebar"></i>
        </a>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import undoRedo from '@baserow/modules/core/mixins/undoRedo'

export default {
  name: 'SidebarFoot',
  components: {},
  mixins: [undoRedo],
  props: {
    collapsed: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    width: {
      type: Number,
      required: true,
    },
  },
  emits: ['set-col1-width'],
  computed: {
    ...mapGetters({
      allJobs: 'job/getAll',
    }),
    exportJobs() {
      return this.allJobs
        .filter((job) => job.type === 'export_applications')
        .slice()
        .reverse()
        .slice(0, 6)
    },
    unfinishedExportCount() {
      return this.exportJobs.filter((job) =>
        ['pending', 'started'].includes(job.state)
      ).length
    },
  },
  methods: {
    exportWorkspaceName(job) {
      const workspace = this.$store.getters['workspace/get'](job.workspace_id)
      return workspace ? workspace.name : this.$t('globalExports.workspace')
    },
    exportProgressLabel(job) {
      if (job.state === 'finished') {
        return this.$t('globalExports.ready')
      }
      if (job.state === 'failed') {
        return this.$t('globalExports.failed')
      }
      if (job.state === 'cancelled') {
        return this.$t('globalExports.cancelled')
      }
      return this.$t('globalExports.progress', {
        progress: job.progress_percentage || 0,
      })
    },
  },
}
</script>
