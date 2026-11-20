import { getAirtableJobErrorMessage } from '@baserow/modules/database/utils/airtableErrors'

const fakeT = (key) => key

describe('getAirtableJobErrorMessage', () => {
  test('maps the requires authentication error code', () => {
    const job = { error_code: 'AirtableBaseRequiresAuthentication' }
    expect(getAirtableJobErrorMessage(fakeT, job)).toStrictEqual({
      title: 'importFromAirtable.errorRequiresAuthenticationTitle',
      message: 'importFromAirtable.errorRequiresAuthenticationDescription',
    })
  })

  test('maps the base not public error code', () => {
    const job = { error_code: 'AirtableBaseNotPublic' }
    expect(getAirtableJobErrorMessage(fakeT, job)).toStrictEqual({
      title: 'importFromAirtable.errorBaseNotPublicTitle',
      message: 'importFromAirtable.errorBaseNotPublicDescription',
    })
  })

  test('falls back to the human readable error for unmapped error codes', () => {
    const job = {
      error_code: 'SoftTimeLimitExceeded',
      human_readable_error: 'The job took too long.',
    }
    expect(getAirtableJobErrorMessage(fakeT, job)).toStrictEqual({
      title: 'importFromAirtable.importError',
      message: 'The job took too long.',
    })
  })
})
