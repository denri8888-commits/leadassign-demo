import { useEffect, useMemo, useState } from 'react'
import { api, money } from '../api'
import { Help } from '../components/Help'

export function MatrixPage() {
  const [items, setItems] = useState<any[]>([])
  const [region, setRegion] = useState('Гродно')
  const [metric, setMetric] = useState<'expected_gm' | 'confidence' | 'n_observations'>('expected_gm')

  useEffect(() => {
    api.matrix().then((r) => setItems(r.items)).catch(console.error)
  }, [])

  const regions = useMemo(() => [...new Set(items.map((i) => i.region))], [items])
  const products = useMemo(() => [...new Set(items.map((i) => i.product))], [items])
  const managers = useMemo(() => [...new Set(items.map((i) => i.manager))], [items])

  const filtered = items.filter((i) => i.region === region)
  const values = filtered.map((i) => i[metric])
  const min = Math.min(...values, 0)
  const max = Math.max(...values, 1)

  const color = (v: number) => {
    const t = max === min ? 0.5 : (v - min) / (max - min)
    const light = 96 - t * 28
    return `hsl(350 70% ${light}%)`
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Регионы и товары</h1>
        <p className="muted">Матрица менеджер × регион × продукт. Цвет отражает выбранный показатель без агрессивной шкалы.</p>
      </div>
      <div className="toolbar">
        <label className="field">
          <span className="field-label-row">Регион</span>
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            {regions.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <label className="field">
          <span className="field-label-row">
            Показатель
            <Help tip="Ожидаемая валовая маржа — основной показатель; уверенность и число наблюдений помогают увидеть малую выборку." metricName="Показатель матрицы" />
          </span>
          <select value={metric} onChange={(e) => setMetric(e.target.value as any)}>
            <option value="expected_gm">Ожидаемая валовая маржа</option>
            <option value="confidence">Уверенность оценки</option>
            <option value="n_observations">Исторических переговоров</option>
          </select>
        </label>
      </div>
      <div className="card table-wrap">
        {filtered.length === 0 ? (
          <div className="empty-state">Нет данных для выбранного региона.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Менеджер</th>
                {products.map((p) => <th key={p} className="center">{region} / {p}</th>)}
              </tr>
            </thead>
            <tbody>
              {managers.map((m) => (
                <tr key={m}>
                  <td>{m}</td>
                  {products.map((p) => {
                    const row = filtered.find((i) => i.manager === m && i.product === p)
                    const v = row ? row[metric] : 0
                    const label =
                      metric === 'expected_gm'
                        ? money(v)
                        : metric === 'confidence'
                          ? String(v.toFixed(2)).replace('.', ',')
                          : String(Math.round(v))
                    return (
                      <td key={p}>
                        <div className="heat-cell" style={{ background: color(v) }} title={`Наблюдений: ${row?.n_observations ?? 0}`}>
                          {label}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
