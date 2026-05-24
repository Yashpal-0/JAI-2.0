import { TENANTS, Tenant } from '../types'

interface Props {
  value: Tenant
  onChange: (tenant: Tenant) => void
  disabled: boolean
}

export function TenantSelector({ value, onChange, disabled }: Props) {
  return (
    <label className="tenant-label">
      <span>Tenant:</span>
      <select
        className="tenant-select"
        value={value}
        onChange={(e) => {
          const val = e.target.value
          if (TENANTS.includes(val as Tenant)) onChange(val as Tenant)
        }}
        disabled={disabled}
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
