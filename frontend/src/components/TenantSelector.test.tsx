import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TenantSelector } from './TenantSelector'
import { TENANTS, Tenant } from '../types'

describe('TenantSelector', () => {
  let defaultProps: { value: Tenant; onChange: ReturnType<typeof vi.fn>; disabled: boolean }

  beforeEach(() => {
    defaultProps = {
      value: TENANTS[0] as Tenant,
      onChange: vi.fn(),
      disabled: false,
    }
  })

  it('renders all tenant options', () => {
    render(<TenantSelector {...defaultProps} />)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(TENANTS.length)
    TENANTS.forEach((tenant) => {
      expect(screen.getByRole('option', { name: tenant })).toBeInTheDocument()
    })
  })

  it('calls onChange with the selected tenant', async () => {
    const onChange = vi.fn()
    render(<TenantSelector {...defaultProps} onChange={onChange} />)
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, TENANTS[0])
    expect(onChange).toHaveBeenCalledWith(TENANTS[0])
  })

  it('is disabled when disabled={true} is passed', () => {
    render(<TenantSelector {...defaultProps} disabled={true} />)
    const select = screen.getByRole('combobox')
    expect(select).toBeDisabled()
  })
})
