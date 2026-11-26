import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import {
  downloadViaXhr,
  getDownloadHref,
  triggerDownload,
} from '@baserow/modules/core/utils/download'

const url = 'https://files.example.com/template-revisions/abc.zip'
const filename = 'sales-pipeline.zip'

describe('download', () => {
  test('getDownloadHref adds the filename to a normal URL', () => {
    expect(getDownloadHref(url, filename)).toBe(`${url}?dl=${filename}`)
  })

  test('getDownloadHref leaves a signed S3 URL untouched', () => {
    const signed =
      'https://s3.bitiful.net/bucket/dms/export_files/test.csv' +
      '?X-Amz-Algorithm=AWS4-HMAC-SHA256' +
      '&X-Amz-Credential=key%2F20261126%2Fcn-east-1%2Fs3%2Faws4_request' +
      '&X-Amz-Date=20261126T000000Z' +
      '&X-Amz-Expires=604800' +
      '&X-Amz-SignedHeaders=host' +
      '&X-Amz-Signature=abc123'
    expect(getDownloadHref(signed, filename)).toBe(signed)
  })

  let clicked = []

  beforeEach(() => {
    clicked = []
    // Records the clicked anchors, without navigating.
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(
      function () {
        clicked.push(this)
      }
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  test('downloadViaXhr throws on a failed response without saving it', async () => {
    const blob = vi.fn()
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 403, blob }))
    )

    await expect(downloadViaXhr(url, filename)).rejects.toThrow('403')

    expect(blob).not.toHaveBeenCalled()
    expect(clicked).toHaveLength(0)
  })

  test.each([
    ['unknown', null, '_blank'],
    ['active', true, '_blank'],
    // The click no longer counts, so a new tab would be blocked.
    ['expired', false, ''],
  ])(
    'triggerDownload with the user activation %s',
    async (_, isActive, target) => {
      if (isActive !== null) {
        vi.stubGlobal(
          'navigator',
          Object.create(navigator, { userActivation: { value: { isActive } } })
        )
      }

      await triggerDownload(url, filename)

      expect(clicked.map((anchor) => anchor.target)).toStrictEqual([target])
    }
  )
})
