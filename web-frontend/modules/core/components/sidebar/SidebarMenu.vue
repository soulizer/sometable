<template>
  <div class="sidebar__section" ph-autocapture="sidebar" data-highlight="menu">
    <ul class="tree">
      <SidebarSearch
        :selected-workspace="selectedWorkspace"
        @open-workspace-search="openWorkspaceSearch"
      />
      <nuxt-link
        v-slot="{ href, navigate, isExactActive, prefetch, shouldPrefetch }"
        custom
        prefetch-on="interaction"
        :to="{
          name: 'workspace',
          params: {
            workspaceId: selectedWorkspace.id,
          },
        }"
      >
        <li
          class="tree__item"
          :class="{
            active: isExactActive,
          }"
        >
          <div class="tree__action sidebar__action">
            <a
              :href="href"
              class="tree__link"
              @click="navigate"
              @pointerenter="shouldPrefetch('interaction') && prefetch()"
              @focus="shouldPrefetch('interaction') && prefetch()"
            >
              <i class="tree__icon iconoir-clock"></i>
              <span class="tree__link-text">
                <span class="sidebar__item-name">{{
                  $t('sidebar.recents')
                }}</span>
              </span>
            </a>
          </div>
        </li>
      </nuxt-link>

      <li class="tree__item">
        <div class="tree__action tree__action--has-counter">
          <a
            class="tree__link"
            role="button"
            tabindex="0"
            @click="$refs.notificationPanel?.toggle($event.currentTarget)"
            @keydown.enter.prevent="
              $refs.notificationPanel?.toggle($event.currentTarget)
            "
            @keydown.space.prevent="
              $refs.notificationPanel?.toggle($event.currentTarget)
            "
          >
            <i class="tree__icon tree__icon--type iconoir-bell"></i>
            <span class="tree__link-text">{{
              $t('sidebar.notifications')
            }}</span>
          </a>
          <BadgeCounter
            v-show="unreadNotificationCount"
            class="tree__counter"
            :count="unreadNotificationCount"
            :limit="10"
          >
          </BadgeCounter>
        </div>
        <NotificationPanel ref="notificationPanel" />
      </li>

      <li v-if="exportJobs.length > 0" class="tree__item">
        <div class="tree__action tree__action--has-counter">
          <a
            ref="exportJobsLink"
            class="tree__link"
            role="button"
            tabindex="0"
            @click="$refs.exportJobsContext?.toggle($refs.exportJobsLink)"
            @keydown.enter.prevent="
              $refs.exportJobsContext?.toggle($refs.exportJobsLink)
            "
            @keydown.space.prevent="
              $refs.exportJobsContext?.toggle($refs.exportJobsLink)
            "
          >
            <i class="tree__icon tree__icon--type iconoir-download"></i>
            <span class="tree__link-text">
              {{ $t('globalExports.title') }}
            </span>
          </a>
          <BadgeCounter
            v-show="unfinishedExportCount > 0"
            class="tree__counter"
            :count="unfinishedExportCount"
            :limit="10"
          >
          </BadgeCounter>
        </div>
        <Context ref="exportJobsContext" overflow-scroll>
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
      </li>

      <nuxt-link
        v-if="
          $hasPermission(
            'workspace.list_workspace_users',
            selectedWorkspace,
            selectedWorkspace.id
          )
        "
        v-slot="{ href, navigate, prefetch, shouldPrefetch }"
        custom
        prefetch-on="interaction"
        :to="{
          name: 'settings-members',
          params: {
            workspaceId: selectedWorkspace.id,
          },
        }"
      >
        <li
          class="tree__item"
          :class="{
            active: isManagementPage,
          }"
          data-highlight="members"
        >
          <div class="tree__action sidebar__action">
            <a
              :href="href"
              class="tree__link"
              @click="navigate"
              @pointerenter="shouldPrefetch('interaction') && prefetch()"
              @focus="shouldPrefetch('interaction') && prefetch()"
            >
              <i class="tree__icon baserow-icon-team"></i>
              <span class="tree__link-text">
                <span class="sidebar__item-name">{{
                  $t('sidebar.members')
                }}</span>
              </span>
              <span v-if="membersCount" class="sidebar__item-count">
                {{ membersCount }}</span
              >
            </a>
          </div>
        </li>
      </nuxt-link>

      <li
        v-if="
          $hasPermission(
            'workspace.create_invitation',
            selectedWorkspace,
            selectedWorkspace.id
          )
        "
        class="tree__item"
      >
        <div class="tree__action sidebar__action">
          <a class="tree__link" @click="$refs.inviteModal?.show()">
            <i class="tree__icon iconoir-add-user"></i>
            <span class="tree__link-text">
              <span class="sidebar__item-name">{{
                $t('sidebar.inviteOthers')
              }}</span>
            </span>
          </a>
        </div>

        <InviteModal ref="inviteModal" :workspace="selectedWorkspace" />
      </li>
      <component
        :is="component"
        v-for="(component, index) in sidebarWorkspaceComponents"
        :key="'sidebarWorkspaceComponents' + index"
        :workspace="selectedWorkspace"
        :right-sidebar-open="rightSidebarOpen"
      ></component>
      <li class="tree__item">
        <div class="tree__action sidebar__action">
          <a class="tree__link" @click="$refs.trashModal?.show()">
            <i class="tree__icon iconoir-bin"></i>
            <span class="tree__link-text">
              <span class="sidebar__item-name">{{ $t('sidebar.trash') }}</span>
            </span>
          </a>
          <TrashModal
            ref="trashModal"
            :initial-workspace="selectedWorkspace"
          ></TrashModal>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import {
  canListIdentities,
  getWorkspaceMembersCount,
} from '@baserow/modules/core/utils/workspace'

import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import NotificationPanel from '@baserow/modules/core/components/NotificationPanel'
import InviteModal from '@baserow/modules/core/components/invitation/InviteModal'
import BadgeCounter from '@baserow/modules/core/components/BadgeCounter'
import SidebarSearch from '@baserow/modules/core/components/sidebar/SidebarSearch'

export default {
  name: 'SidebarMenu',
  components: {
    TrashModal,
    NotificationPanel,
    InviteModal,
    BadgeCounter,
    SidebarSearch,
  },
  props: {
    selectedWorkspace: {
      type: Object,
      required: true,
    },
    rightSidebarOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['open-workspace-search'],
  computed: {
    membersCount() {
      return getWorkspaceMembersCount(
        this.selectedWorkspace,
        canListIdentities(this, this.selectedWorkspace)
      )
    },
    isManagementPage() {
      return [
        'settings-members',
        'settings-teams',
        'settings-identities',
      ].includes(this.$route.name)
    },
    sidebarWorkspaceComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .flatMap((plugin) =>
          plugin.getSidebarWorkspaceComponents(this.selectedWorkspace)
        )
        .filter((component) => component !== null)
    },
    ...mapGetters({
      unreadNotificationCount: 'notification/getUnreadCount',
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
    openWorkspaceSearch() {
      this.$emit('open-workspace-search')
    },
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
