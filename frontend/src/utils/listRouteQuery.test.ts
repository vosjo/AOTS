import { describe, expect, it } from 'vitest'
import {
  buildListRouteQuery,
  mergeListRouteQuery,
  parseRouteFilterValue,
  readListStateFromQuery,
} from '@/utils/listRouteQuery'

describe('listRouteQuery', () => {
  it('parses scalar and array filter values from route query', () => {
    expect(parseRouteFilterValue('abc', false)).toBe('abc')
    expect(parseRouteFilterValue('ON,FI', true)).toEqual(['ON', 'FI'])
    expect(parseRouteFilterValue(['a', 'b'], true)).toEqual(['a', 'b'])
  })

  it('reads list state with defaults', () => {
    const state = readListStateFromQuery(
      { page: '3', page_size: '50', system: 'V*' },
      { system: '', name: '' },
    )
    expect(state.page).toBe(3)
    expect(state.pageSize).toBe(50)
    expect(state.filters).toEqual({ system: 'V*', name: '' })
  })

  it('builds query only for non-default values', () => {
    expect(
      buildListRouteQuery({
        page: 1,
        pageSize: 20,
        filters: { system: '', name: 'test' },
      }),
    ).toEqual({ name: 'test' })
  })

  it('merges list query without dropping unrelated params', () => {
    expect(
      mergeListRouteQuery(
        { tab: 'overview', page: '2' },
        { page: '3', name: 'x' },
        ['page', 'page_size', 'name'],
      ),
    ).toEqual({ tab: 'overview', page: '3', name: 'x' })
  })
})
