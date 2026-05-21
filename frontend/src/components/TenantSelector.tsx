import { TENANTS, Tenant } from '../types'

interface Props {
  value: Tenant
  onChange: (tenant: Tenant) => void
  disabled: boolean
}

export function TenantSelector({ value, onChange, disabled }: Props) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
      <span>Tenant:</span>
      <select
        value={value}
        onChange={(e) => {
          const val = e.target.value
          if (TENANTS.includes(val as Tenant)) onChange(val as Tenant)
        }}
        disabled={disabled}
        style={{
          padding: '0.25rem 0.5rem',
          borderRadius: '4px',
          border: '1px solid #ccc',
          background: '#fff',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        {TENANTS.map((tenant) => (
          <option key={tenant} value={tenant}>
            {tenant}
          </option>
        ))}
      </select>
    </label>
  )
}
