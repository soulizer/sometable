<template>
  <Modal
    ref="modal"
    :content-scrollable="true"
    :close-button="false"
    :box-padding="false"
    :content-padding="false"
    @show="onShow"
  >
    <template #content>
      <div
        class="workspace-search workspace-search--expanded"
        :class="{ 'workspace-search--keyboard-nav': isKeyboardNavigating }"
      >
        <div class="workspace-search__header">
          <div class="workspace-search__search">
            <i
              class="workspace-search__icon iconoir-search"
              :class="{ 'workspace-search__icon--active': focusInput }"
            ></i>
            <input
              ref="searchInput"
              v-model="searchTerm"
              class="workspace-search__input"
              :placeholder="$t('commandPalette.placeholder')"
              @keydown.stop="handleKeydown"
              @focusin="focusInput = true"
              @focusout="focusInput = false"
            />
            <a
              v-show="searchTerm.length > 0"
              class="workspace-search__close"
              @click="searchTerm = ''"
              ><i class="iconoir-cancel"
            /></a>
          </div>
        </div>

        <div class="workspace-search__content" @mousemove="onMouseMove">
          <div v-if="items.length" class="workspace-search__results">
            <div ref="resultsList" class="workspace-search__results-list">
              <div
                v-for="(item, index) in items"
                :key="item.key"
                class="workspace-search__result-item"
                :class="{
                  'workspace-search__result-item--active':
                    activeIndex === index,
                }"
                @click="selectItem(item)"
                @mouseenter="handleMouseEnter(index)"
              >
                <div class="workspace-search__result-icon">
                  <i :class="item.icon"></i>
                </div>
                <div class="workspace-search__result-main">
                  <div class="workspace-search__result-title">
                    {{ item.title }}
                  </div>
                  <div
                    v-if="item.subtitle"
                    class="workspace-search__result-subtitle"
                  >
                    {{ item.subtitle }}
                  </div>
                </div>
                <div
                  v-if="activeIndex === index"
                  class="workspace-search__result-enter"
                >
                  <kbd class="workspace-search__keys"> ↵ </kbd>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="workspace-search__empty">
            <div class="workspace-search__empty-icon">
              <i class="iconoir-search"></i>
            </div>
            <div class="workspace-search__empty-title">
              {{ $t('workspaceSearch.noResults') }}
            </div>
            <div class="workspace-search__empty-subtitle">
              {{ $t('workspaceSearch.noResultsSubtitle', { searchTerm }) }}
            </div>
          </div>
        </div>

        <div class="workspace-search__footer">
          <div class="workspace-search__shortcuts">
            <div class="workspace-search__shortcuts-left">
              <div class="workspace-search__shortcut">
                <kbd class="workspace-search__keys"
                  ><i class="iconoir-arrow-up"></i
                ></kbd>
                <kbd class="workspace-search__keys"
                  ><i class="iconoir-arrow-down"></i
                ></kbd>
                {{ $t('workspaceSearch.navigate') }}
              </div>
            </div>
            <div class="workspace-search__shortcuts-right">
              <div class="workspace-search__shortcut">
                <kbd class="workspace-search__keys">esc</kbd>
                {{ $t('workspaceSearch.close') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'
import modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'GlobalCommandPalette',
  mixins: [modal],
  data() {
    return {
      searchTerm: '',
      activeIndex: 0,
      focusInput: false,
      isKeyboardNavigating: false,
    }
  },
  computed: {
    ...mapGetters({
      workspaces: 'workspace/getAllSorted',
      isStaff: 'auth/isStaff',
    }),
    actions() {
      const actions = [
        {
          key: 'action-all-workspaces',
          title: this.$t('allWorkspaces.title'),
          icon: 'iconoir-home',
          route: { name: 'all-workspaces' },
        },
      ]
      if (this.isStaff) {
        actions.push(
          {
            key: 'action-admin-dashboard',
            title: this.$t('adminDashboard.title'),
            icon: 'iconoir-dashboard',
            route: { name: 'admin-dashboard' },
          },
          {
            key: 'action-admin-users',
            title: this.$t('adminType.users'),
            icon: 'iconoir-user',
            route: { name: 'admin-users' },
          },
          {
            key: 'action-admin-workspaces',
            title: this.$t('adminWorkspaces.title'),
            icon: 'iconoir-group',
            route: { name: 'admin-workspaces' },
          },
          {
            key: 'action-admin-templates',
            title: this.$t('adminType.templates'),
            icon: 'iconoir-layout',
            route: { name: 'admin-templates' },
          },
          {
            key: 'action-admin-ai',
            title: this.$t('adminType.aiProviders'),
            icon: 'iconoir-sparks',
            route: { name: 'admin-ai-providers' },
          },
          {
            key: 'action-admin-backups',
            title: this.$t('adminBackups.title'),
            icon: 'iconoir-database',
            route: { name: 'admin-backups' },
          },
          {
            key: 'action-admin-health',
            title: this.$t('health.title'),
            icon: 'iconoir-heart',
            route: { name: 'admin-health' },
          },
          {
            key: 'action-admin-settings',
            title: this.$t('settings.settingsTitle'),
            icon: 'iconoir-settings',
            route: { name: 'admin-settings' },
          }
        )
      }
      return actions
    },
    items() {
      const query = this.searchTerm.trim().toLowerCase()
      const matches = (value) => value.toLowerCase().includes(query)
      const actionItems = this.actions.filter((action) => matches(action.title))
      const workspaceItems = this.workspaces
        .filter((workspace) => matches(workspace.name))
        .map((workspace) => ({
          key: 'workspace-' + workspace.id,
          title: workspace.name,
          subtitle: this.$t('commandPalette.workspaces'),
          icon: 'iconoir-home-simple',
          route: {
            name: 'workspace',
            params: { workspaceId: workspace.id },
          },
        }))
      return [...actionItems, ...workspaceItems]
    },
  },
  watch: {
    searchTerm() {
      this.activeIndex = 0
    },
  },
  methods: {
    onShow() {
      this.searchTerm = ''
      this.activeIndex = 0
      this.$nextTick(() => this.$refs.searchInput?.focus())
    },
    onMouseMove(event) {
      if (event && (event.movementX !== 0 || event.movementY !== 0)) {
        this.isKeyboardNavigating = false
      }
    },
    handleMouseEnter(index) {
      if (!this.isKeyboardNavigating) {
        this.activeIndex = index
      }
    },
    handleKeydown(event) {
      this.isKeyboardNavigating = true
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        this.activeIndex = Math.min(
          this.activeIndex + 1,
          Math.max(0, this.items.length - 1)
        )
        this.scrollToActiveItem()
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        this.activeIndex = Math.max(0, this.activeIndex - 1)
        this.scrollToActiveItem()
      } else if (event.key === 'Enter') {
        event.preventDefault()
        if (this.items[this.activeIndex]) {
          this.selectItem(this.items[this.activeIndex])
        }
      } else if (event.key === 'Escape') {
        event.preventDefault()
        this.hide()
      }
    },
    scrollToActiveItem() {
      this.$nextTick(() => {
        this.$refs.resultsList?.children[this.activeIndex]?.scrollIntoView({
          block: 'nearest',
        })
      })
    },
    selectItem(item) {
      if (!item.route) return
      this.hide()
      this.$router.push(item.route)
    },
  },
}
</script>
