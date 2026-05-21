import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { TenantSelector } from './TenantSelector'
import { TENANTS, Tenant } from '../types'

describe('TenantSelector', () => {
  const defaultProps = {
    value: TENANTS[0] as Tenant,
    onChange: vi.fn(),
    disabled: false,
  }

  it('renders all 3 tenant options', () => {
    render(<TenantSelector {...defaultProps} />)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(3)
    TENANTS.forEach((tenant) => {
      expect(screen.getByRole('option', { name: tenant })).toBeInTheDocument()
    })
  })

  it('calls onChange with the new tenant when selection changes', async () => {
    const onChange = vi.fn()
    render(<TenantSelector {...defaultProps} onChange={onChange} />)
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, TENANTS[1])
    expect(onChange).toHaveBeenCalledWith(TENANTS[1])
  })

  it('is disabled when disabled={true} is passed', () => {
    render(<TenantSelector {...defaultProps} disabled={true} />)
    const select = screen.getByRole('combobox')
    expect(select).toBeDisabled()
  })
})
