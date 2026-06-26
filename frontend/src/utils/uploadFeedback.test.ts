import { describe, expect, it } from 'vitest'

import { parseUploadFeedback } from '@/utils/uploadFeedback'

describe('parseUploadFeedback', () => {
  it('classifies duplicate light curves as warnings', () => {
    const [item] = parseUploadFeedback('This light curve is a duplicate and was not added!')
    expect(item.kind).toBe('warning')
    expect(item.title).toBe('Duplicate light curve')
  })

  it('classifies successful light curve imports', () => {
    const [item] = parseUploadFeedback('New light curve, added to new System Vega: 18.62 38.78')
    expect(item.kind).toBe('success')
    expect(item.title).toBe('Light curve imported')
  })

  it('splits multi-file upload feedback', () => {
    const items = parseUploadFeedback(
      'New light curve, added to new System A; This light curve is a duplicate and was not added!',
    )
    expect(items).toHaveLength(2)
    expect(items[0]?.kind).toBe('success')
    expect(items[1]?.kind).toBe('warning')
  })
})
