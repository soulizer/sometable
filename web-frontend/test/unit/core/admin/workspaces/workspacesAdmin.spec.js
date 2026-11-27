import { expect, test, vi } from 'vitest'

import WorkspacesAdminService from '@baserow/modules/core/services/admin/workspaces'

test('workspace admin member and export service uses the admin endpoints', async () => {
  const client = {
    get: vi.fn().mockResolvedValue({ data: { results: [] } }),
    patch: vi.fn(),
    delete: vi.fn(),
    post: vi.fn(),
  }
  const service = WorkspacesAdminService(client)

  await service.listMembers(7, 2, 'alice', [], {})

  expect(client.get).toHaveBeenCalledWith('/admin/workspaces/7/members/', {
    params: { page: 2, search: 'alice' },
  })

  service.updateMember(7, 9, { permissions: 'ADMIN' })
  expect(client.patch).toHaveBeenCalledWith('/admin/workspaces/7/members/9/', {
    permissions: 'ADMIN',
  })

  service.deleteMember(7, 9)
  expect(client.delete).toHaveBeenCalledWith('/admin/workspaces/7/members/9/')

  service.exportAsync(7, { only_structure: true, application_ids: [] })
  expect(client.post).toHaveBeenCalledWith(
    '/admin/workspaces/7/export/async/',
    { only_structure: true, application_ids: [] }
  )
})
