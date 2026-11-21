import path from 'path'

export const routes = [
  {
    name: 'database-public-kanban-view',
    path: '/public/kanban/:slug',
    file: '@baserow/modules/database/pages/publicView.vue',
  },
  {
    name: 'database-public-calendar-view',
    path: '/public/calendar/:slug',
    file: '@baserow/modules/database/pages/publicView.vue',
  },
  {
    name: 'database-public-timeline-view',
    path: '/public/timeline/:slug',
    file: '@baserow/modules/database/pages/publicView.vue',
  },
]
