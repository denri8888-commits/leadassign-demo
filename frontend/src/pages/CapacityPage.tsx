import { useEffect, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, money } from '../api'
import { Help } from '../components/Help'

export function CapacityPage() {
  const [data, setData] = useState<any | null>(null)

  useEffect(() => {
    api.capacity().then(setData).catch(console.error)
  }, [])

  if (!data) return <div className="loading-inline">Загрузка…</div>
  const h = data.hiring_economics

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Анализ загрузки</h1>
        <p className="muted">Этап 2 / стратегическая аналитика. Не смешивается с обязательным дневным распределением.</p>
      </div>
      <div className="banner">{data.diminishing_returns_note}</div>
      <div className="card">
        <h3 style={{ marginTop: 0 }} className="label-with-help">
          <span>Ожидаемая валовая маржа при разной мощности</span>
          <Help tip="По горизонтали — число переговоров, по вертикали — ожидаемая валовая маржа. Лучшие заявки выбираются первыми." metricName="Сценарии загрузки" />
        </h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={data.chart.points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip formatter={(v) => money(Number(v))} />
              <Line type="monotone" dataKey="y" stroke="var(--color-primary)" strokeWidth={3} dot name="Валовая маржа" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th className="num">Переговоров</th>
              <th className="num">Обработано</th>
              <th className="num">Ожидаемая валовая маржа</th>
              <th className="num">Прирост к предыдущему</th>
              <th className="num">Доп. маржа к 50</th>
            </tr>
          </thead>
          <tbody>
            {data.scenarios.map((r: any) => (
              <tr key={r.capacity}>
                <td className="num">{r.capacity}</td>
                <td className="num">{r.processed}</td>
                <td className="num">{money(r.expected_gm)}</td>
                <td className="num">{money(r.delta_gm)}</td>
                <td className="num">{money(r.extra_vs_50)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Экономика дополнительного менеджера</h3>
        <p className="muted">{h.stage}</p>
        <div className="kpi-grid">
          <div><div className="muted">Доп. маржа в день (50→70)</div><strong>{money(h.daily_gm_uplift_50_to_70)}</strong></div>
          <div><div className="muted">Оценка в месяц</div><strong>{money(h.monthly_gm_uplift_estimate)}</strong></div>
          <div><div className="muted">Стоимость доп. менеджера</div><strong>{money(h.extra_manager_monthly_cost)}</strong></div>
          <div><div className="muted">Ориентир результата</div><strong>{money(h.net_monthly_estimate)}</strong></div>
          <div><div className="muted">Срок окупаемости, дни</div><strong>{h.payback_days_estimate ?? 'н/д'}</strong></div>
        </div>
        <p style={{ marginTop: 12 }}>{h.disclaimer}</p>
        <p>
          <strong>При текущих предположениях увеличение доступной загрузки может быть экономически оправдано.</strong>{' '}
          Решение — за руководителем.
        </p>
      </div>
    </div>
  )
}
