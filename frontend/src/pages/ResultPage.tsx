import { useEffect, useState } from 'react'
import { api, money } from '../api'

export function ResultPage() {
  const [data, setData] = useState<any | null>(null)

  useEffect(() => {
    api.result().then(setData).catch(console.error)
  }, [])

  if (!data) return <div className="loading-inline">Загрузка…</div>

  const steps = [
    [`${data.total_applications} заявок`, 'Входящий поток'],
    [`${data.assigned} назначено`, 'Вошли в доступную загрузку'],
    [`${data.queued} осталось в очереди`, 'Вне текущей загрузки'],
    [money(data.expected_gm), 'ожидаемой валовой маржи'],
    [`+${money(data.lift_abs)}`, 'против простого варианта для сравнения'],
  ]

  return (
    <div className="stack" style={{ maxWidth: 720, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', padding: '24px 0' }}>
        <div className="brand" style={{ fontSize: '1.6rem', marginBottom: 8 }}>Lead<span>Assign</span></div>
        <h1 className="page-title">{data.title}</h1>
        <p className="muted">{data.core_idea}</p>
      </div>
      <div className="card" style={{ textAlign: 'center' }}>
        {steps.map(([value, label], i) => (
          <div key={label} style={{ padding: '18px 8px' }}>
            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: i === steps.length - 1 ? 'var(--color-primary)' : 'var(--color-text)' }}>{value}</div>
            <div className="muted">{label}</div>
            {i < steps.length - 1 && <div style={{ marginTop: 12, color: 'var(--color-primary)', fontSize: 22 }}>↓</div>}
          </div>
        ))}
      </div>
      <div className="banner" style={{ textAlign: 'center' }}>{data.disclaimer}</div>
    </div>
  )
}
