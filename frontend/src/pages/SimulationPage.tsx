import { useState } from 'react'
import { api, money } from '../api'
import { Help } from '../components/Help'

export function SimulationPage() {
  const [days, setDays] = useState(14)
  const [autoShare, setAutoShare] = useState(0.5)
  const [data, setData] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)

  const run = async () => {
    setLoading(true)
    try {
      setData(await api.simulation(days, autoShare))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Проверка эффекта</h1>
        <p className="muted">Простой симулятор на демо-данных. Без заявлений о статистической значимости без расчёта.</p>
      </div>
      <div className="toolbar">
        <label className="field">
          <span className="field-label-row">
            Тестовых дней
            <Help tip="Сколько синтетических дней прогнать для сравнения." metricName="Тестовых дней" />
          </span>
          <input type="number" min={1} max={60} value={days} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
        <label className="field">
          <span className="field-label-row">
            Доля дней с авто-распределением
            <Help tip="Остальные дни имитируют «ручной» режим для смешанного сценария." metricName="Доля авто-распределения" />
          </span>
          <input type="number" min={0} max={1} step={0.1} value={autoShare} onChange={(e) => setAutoShare(Number(e.target.value))} />
        </label>
        <button className="btn" type="button" onClick={run} disabled={loading}>
          {loading ? 'Считаем…' : 'Сравнить с простым вариантом'}
        </button>
      </div>
      {data && (
        <>
          <div className="banner">{data.note}</div>
          <div className="kpi-grid">
            <div className="card"><div className="label">Валовая маржа (простой вариант)</div><div className="value" style={{ fontSize: '1.3rem' }}>{money(data.gm_manual_total)}</div></div>
            <div className="card"><div className="label">Валовая маржа (оптимизация)</div><div className="value" style={{ fontSize: '1.3rem' }}>{money(data.gm_optimized_total)}</div></div>
            <div className="card"><div className="label">Разница</div><div className="value" style={{ fontSize: '1.3rem' }}>{money(data.difference_opt_vs_manual)}</div></div>
            <div className="card"><div className="label">Среднее изменение / день</div><div className="value" style={{ fontSize: '1.3rem' }}>{money(data.avg_daily_change)}</div></div>
          </div>
          <div className="card table-wrap">
            <table>
              <thead>
                <tr>
                  <th>День</th>
                  <th>Режим</th>
                  <th className="num">Оптимизация</th>
                  <th className="num">Простой вариант</th>
                  <th className="num">Случайный</th>
                </tr>
              </thead>
              <tbody>
                {data.daily.map((d: any) => (
                  <tr key={d.day}>
                    <td>{d.day}</td>
                    <td>{d.mode === 'auto' ? 'авто' : 'ручной'}</td>
                    <td className="num">{money(d.optimized_gm)}</td>
                    <td className="num">{money(d.manual_gm)}</td>
                    <td className="num">{money(d.random_gm)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
