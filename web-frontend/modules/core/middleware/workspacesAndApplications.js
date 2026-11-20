import { fetchWorkspacesAndApplications } from '@baserow/modules/core/utils/workspace'

/**
 * This middleware will make sure that all the workspaces and applications belonging to
 * the user are fetched and added to the store.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const nuxtApp = useNuxtApp()
  const store = nuxtApp.$store
  const event = import.meta.server ? useRequestEvent() : null

  // If nuxt generate, pass this middleware
  if (import.meta.server && !event) return

  // A workspace is only selected when the route explicitly points to one. Pages can
  // opt out or change the param by doing:
  // `definePageMeta({ useRouteWorkspaceParam: 'none' })`.
  let workspaceId = null
  const workspaceIdParam = to.meta.useRouteWorkspaceParam ?? 'workspaceId'
  if (to.params[workspaceIdParam]) {
    const routeWorkspaceId = parseInt(to.params[workspaceIdParam], 10)
    if (!isNaN(routeWorkspaceId)) {
      workspaceId = routeWorkspaceId
    }
  }

  if (store.getters['auth/isAuthenticated']) {
    await fetchWorkspacesAndApplications(nuxtApp, workspaceId)
  }
})
