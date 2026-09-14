import { Help } from './Help'

type Props = {
  label: string
  value: string
  tip: string
  onClick?: () => void
}

export function KpiCard({ label, value, tip, onClick }: Props) {
  return (
    <button type="button" className="card kpi" onClick={onClick} style={{ textAlign: 'left', width: '100%' }}>
      <div className="label">
        <span>{label}</span>
        <Help tip={tip} metricName={label} />
      </div>
      <div className="value">{value}</div>
    </button>
  )
}
