import { useEffect, useState } from 'react'
import { api, money, pct } from '../api'
import { Help } from '../components/Help'

export function ManagersPage() {
  const [items, setItems] = useState<any[]>([])
  const [active, setActive] = useState<any | null>(null)

  useEffect(() => {
    api.managers().then((r) => setItems(r.items)).catch(console.error)
  }, [])

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Менеджеры</h1>
        <p className="muted">Текущая форма, конверсия и загрузка — без ярлыка «лучший навсегда».</p>
      </div>
      <div className="kpi-grid">
        {items.map((m) => (
          <button key={m.manager} type="button" className="card kpi" onClick={() => setActive(m)} style={{ textAlign: 'left' }}>
            <div className="label">{m.manager}</div>
            <div className="value" style={{ fontSize: '1.2rem' }}>
              {money(m.form.recent_metric)} <span className="muted" style={{ fontSize: '0.85rem' }}>/ переговор</span>
            </div>
            <div className="muted" style={{ marginTop: 8, fontSize: '0.85rem' }}>
              Форма: {m.form.direction === 'up' ? '↑' : m.form.direction === 'down' ? '↓' : '→'}{' '}
              {m.form.change_pct == null ? 'н/д' : `${m.form.change_pct > 0 ? '+' : ''}${String(m.form.change_pct).replace('.', ',')}%`}
              {m.form.low_sample ? ' · мало данных' : ''}
            </div>
            <div className="muted" style={{ fontSize: '0.85rem' }}>
              Загрузка {m.load} из {m.capacity}
            </div>
          </button>
        ))}
      </div>

      {active && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>{active.manager}</h3>
          <p>{active.form.comment}</p>
          <div className="kpi-grid">
            <div>
              <div className="muted label-with-help">
                Продажи <Help tip="Число успешных сделок в истории." metricName="Продажи" />
              </div>
              <strong>{active.sales}</strong>
            </div>
            <div>
              <div className="muted label-with-help">
                Конверсия <Help tip="Фактическая доля продаж. Для решений используется сглаженная оценка." metricName="Конверсия" />
              </div>
              <strong>{pct(active.conversion)}</strong>
            </div>
            <div>
              <div className="muted">Средний чек</div>
              <strong>{money(active.avg_check)}</strong>
            </div>
            <div>
              <div className="muted label-with-help">
                Средняя валовая маржа
                <Help tip="Валовая маржа показывает ожидаемую валовую прибыль по сделке. В демо — на синтетических данных." metricName="Средняя валовая маржа" />
              </div>
              <strong>{money(active.avg_gm)}</strong>
            </div>
            <div>
              <div className="muted">Средняя скидка</div>
              <strong>{pct(active.avg_discount)}</strong>
            </div>
            <div>
              <div className="muted">Исторических переговоров</div>
              <strong>{active.talks}</strong>
            </div>
            <div>
              <div className="muted label-with-help">
                Свободная загрузка
                <Help tip="Показывает, сколько переговоров менеджер ещё может принять в текущем сценарии." metricName="Свободная загрузка" />
              </div>
              <strong>{Math.max(0, active.capacity - active.load)}</strong>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
