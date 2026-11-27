<template>
  <div>
    <Toasts />

    <div ref="app" class="layout">
      <div class="layout__col-1" :style="{ width: col1Width + 'px' }">
        <SidebarAllWorkspaces
          v-if="sidebarType === SIDEBAR_TYPES.ALL_WORKSPACES"
          :workspaces="workspaces"
          :selected-workspace="selectedWorkspace"
          :collapsed="isCollapsed"
          :width="col1Width"
          @set-col1-width="col1Width = $event"
        />
        <Sidebar
          v-else
          :workspaces="workspaces"
          :selected-workspace="selectedWorkspace"
          :applications="applications"
          :collapsed="isCollapsed"
          :width="col1Width"
          :right-sidebar-open="col3Visible"
          @set-col1-width="col1Width = $event"
          @open-workspace-search="openWorkspaceSearch"
        />
      </div>

      <div
        class="layout__col-2"
        :style="{
          left: col1Width + 'px',
          right: col3Shown ? col3Width + 'px' : 0,
        }"
      >
        <slot />
      </div>

      <div
        v-if="col3Shown"
        class="layout__col-3"
        :style="{ width: col3Width + 'px', right: 0 }"
      >
        <RightSidebar :workspace="selectedWorkspace" />
      </div>

      <HorizontalResize
        class="layout__resize"
        :width="col1Width"
        :style="{ left: col1Width - 2 + 'px' }"
        :min="52"
        :max="300"
        @move="resizeCol1"
      />

      <HorizontalResize
        v-if="col3Shown"
        class="layout__resize"
        :width="col3Width"
        :style="{ right: col3Width - 3 + 'px' }"
        :min="300"
        :max="500"
        :right="true"
        @move="resizeCol3"
      />

      <component
        :is="component"
        v-for="(component, index) in appLayoutComponents"
        :key="index"
      />
    </div>

    <WorkspaceSearchModal ref="workspaceSearchModal" />
    <GlobalCommandPalette ref="globalCommandPalette" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'

import Toasts from '@baserow/modules/core/components/toasts/Toasts.vue'
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar.vue'
import SidebarAllWorkspaces from '@baserow/modules/core/components/sidebar/SidebarAllWorkspaces.vue'
import RightSidebar from '@baserow/modules/core/components/sidebar/RightSidebar.vue'
import HorizontalResize from '@baserow/modules/core/components/HorizontalResize.vue'
import WorkspaceSearchModal from '@baserow/modules/core/components/workspace/WorkspaceSearchModal.vue'
import GlobalCommandPalette from '@baserow/modules/core/components/GlobalCommandPalette.vue'
import {
  CORE_ACTION_SCOPES,
  getSidebarActionScopes,
} from '@baserow/modules/core/utils/undoRedoConstants'
import {
  isOsSpecificModifierPressed,
  keyboardShortcutsToPriorityEventBus,
} from '@baserow/modules/core/utils/events'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { SIDEBAR_TYPES } from '@baserow/modules/core/utils/constants'
import { provideWorkspaceSidebarVisible } from '@baserow/modules/core/composables/useWorkspaceSidebar'

const store = useStore()
const { $registry, $priorityBus, $realtime, $bus } = useNuxtApp()

const col1Width = ref(240)
const col3Width = ref(400)
const layoutWidthRestored = ref(false)
const col3Visible = ref(false)
const narrowViewport = ref(false)
let widthBeforeNarrow = 240
const app = ref()

const workspaceSearchModal = ref(null)
const globalCommandPalette = ref(null)

const workspaces = computed(() => store.getters['workspace/getAll'])
const selectedWorkspace = computed(() => store.getters['workspace/getSelected'])
const applications = computed(() => store.getters['application/getAll'])

const isCollapsed = computed(() => col1Width.value < 170)

const route = useRoute()
const router = useRouter()

// Pages can render an alternative sidebar via
// `definePageMeta({ sidebarType: SIDEBAR_TYPES.ALL_WORKSPACES })`.
const sidebarType = computed(
  () => route.meta.sidebarType ?? SIDEBAR_TYPES.WORKSPACE
)

provideWorkspaceSidebarVisible(
  computed(
    () => sidebarType.value === SIDEBAR_TYPES.WORKSPACE && !isCollapsed.value
  )
)

// The sidebar decides which workspace and application level actions the user
// can undo, so the corresponding scopes follow it and the store selections here
// rather than in every page. The selections stay in the store when navigating
// to a page that doesn't select anything (settings, the homepage), so the
// scopes are re-derived from them whenever the sidebar changes.
const selectedApplication = computed(
  () => store.getters['application/getSelected']
)
watch(
  () => [
    sidebarType.value,
    selectedWorkspace.value?.id ?? null,
    selectedApplication.value?.id ?? null,
  ],
  ([type, workspaceId, applicationId]) => {
    store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      getSidebarActionScopes({ sidebarType: type, workspaceId, applicationId })
    )
  },
  { immediate: true }
)

// The all workspaces sidebar shows no selected application, and application
// types redirect away on delete while their application is still selected, so
// the selection of a previously opened application must not linger.
watch(sidebarType, (type) => {
  if (type === SIDEBAR_TYPES.ALL_WORKSPACES) {
    store.dispatch('application/unselect')
  }
})

// The right sidebar contains workspace specific components, like the assistant, so
// it must not render on pages without a workspace context. The open state is kept,
// so it shows again when navigating back to a workspace page.
const col3Shown = computed(
  () => col3Visible.value && sidebarType.value === 'workspace'
)

// Preserve authentication logic
if (route.query.token) {
  const newQuery = { ...route.query }
  delete newQuery.token
  router.replace({ query: newQuery })
}

function openWorkspaceSearch() {
  // The all workspaces page has its own inline search and handles Ctrl+K.
  if (route.name === 'all-workspaces') {
    return
  }
  if (route.path.startsWith('/admin')) {
    globalCommandPalette.value?.show()
    return
  }
  if (selectedWorkspace.value?.id && workspaceSearchModal.value) {
    workspaceSearchModal.value.show()
  } else {
    globalCommandPalette.value?.show()
  }
}

function resizeCol1(v) {
  col1Width.value = v
}
function resizeCol3(v) {
  col3Width.value = v
}

// On narrow screens the fixed sidebar would leave too little room for the
// content tables. Collapse it automatically without overwriting the saved
// desktop width, and restore the preference when the viewport grows again.
function applyResponsiveSidebar() {
  const shouldNarrow = window.innerWidth <= 768
  if (shouldNarrow && !narrowViewport.value) {
    widthBeforeNarrow = col1Width.value
    narrowViewport.value = true
    col3Visible.value = false
    col1Width.value = 52
  } else if (!shouldNarrow && narrowViewport.value) {
    narrowViewport.value = false
    col1Width.value = widthBeforeNarrow
  }
}

function toggleRightSidebar(value = !col3Visible.value) {
  col3Visible.value = value
  localStorage.setItem('baserow.rightSidebarOpen', col3Visible.value)
}

function keyDown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    openWorkspaceSearch()
    return
  }

  if (isOsSpecificModifierPressed(event) && event.key.toLowerCase() === 'z') {
    const el = document.activeElement
    const avoid =
      ['input', 'textarea', 'select'].includes(el.tagName.toLowerCase()) ||
      el.isContentEditable

    if (!avoid) {
      const actionName = event.shiftKey ? 'undoRedo/redo' : 'undoRedo/undo'
      store.dispatch(actionName, { showLoadingToast: true }).catch(notifyIf)
      event.preventDefault()
    }
  }

  keyboardShortcutsToPriorityEventBus(event, $priorityBus)
}

watch([col1Width, col3Width], ([left, right]) => {
  if (!layoutWidthRestored.value || narrowViewport.value) {
    return
  }
  localStorage.setItem('baserow.leftSidebarWidth', String(left))
  localStorage.setItem('baserow.rightSidebarWidth', String(right))
})

onMounted(() => {
  const storedLeft = Number(localStorage.getItem('baserow.leftSidebarWidth'))
  const storedRight = Number(localStorage.getItem('baserow.rightSidebarWidth'))
  if (storedLeft >= 52 && storedLeft <= 600) {
    col1Width.value = storedLeft
  }
  if (storedRight >= 240 && storedRight <= 900) {
    col3Width.value = storedRight
  }
  const storedRightSidebar = localStorage.getItem('baserow.rightSidebarOpen')
  if (storedRightSidebar !== null) {
    col3Visible.value = storedRightSidebar === 'true'
  }
  layoutWidthRestored.value = true
  applyResponsiveSidebar()
  window.addEventListener('resize', applyResponsiveSidebar)

  $realtime.connect()

  const handler = (e) => keyDown(e)
  document.body.addEventListener('keydown', handler)
  //nuxtApp.$el = { keydownEvent: handler }
  app.value.keydownEvent = handler

  store.dispatch('undoRedo/updateCurrentScopeSet', CORE_ACTION_SCOPES.root())

  store.dispatch('job/initializePoller')

  $bus.$on('toggle-right-sidebar', toggleRightSidebar)
})

onBeforeUnmount(() => {
  $realtime.disconnect()

  if (app.value?.keydownEvent) {
    document.body.removeEventListener('keydown', app.value?.keydownEvent)
  }
  window.removeEventListener('resize', applyResponsiveSidebar)

  store.dispatch(
    'undoRedo/updateCurrentScopeSet',
    CORE_ACTION_SCOPES.root(false)
  )

  $bus.$off('toggle-right-sidebar', toggleRightSidebar)
})

const appLayoutComponents = computed(() => {
  return Object.values($registry.getAll('plugin'))
    .map((plugin) => plugin.getAppLayoutComponent())
    .filter((component) => component !== null)
})
</script>
