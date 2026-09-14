import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, money, pctAlready, type Dashboard } from '../api'
import { Help } from '../components/Help'
import { KpiCard } from '../components/KpiCard'

export function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [seed, setSeed] = useState(42)
  const [scenario, setScenario] = useState('normal')
  const [scenarios, setScenarios] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const nav = useNavigate()

  const load = async () => {
    setError('')
    const [d, s] = await Promise.all([api.dashboard(), api.settings()])
    setData(d)
    setSeed(s.settings.demo_seed)
    setScenarios(s.scenarios)
  }

  useEffect(() => {
    load().catch((e) => setError(String(e.message || e)))
  }, [])

  const generate = async () => {
    setLoading(true)
    try {
      await api.generate(seed, scenario)
      await load()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (!data) {
    return <div className="loading-inline">{error || 'Загрузка…'}</div>
  }

  const k = data.kpi
  const comparison = (data.charts.gm_comparison || []).map((row: { name: string; value: number }) => ({
    ...row,
    name: row.name
      .replace('Ручной baseline', 'Простой вариант')
      .replace('Оптимизированный', 'Оптимизация')
      .replace('Жадный алгоритм', 'Жадный'),
  }))

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Распределение заявок</h1>
        <p className="muted" style={{ margin: 0, maxWidth: 820 }}>
          {data.core_idea}
        </p>
      </div>

      <div className="banner">
        <strong>Демонстрационные данные для прототипа.</strong> {data.disclaimer}
      </div>

      <div className="toolbar">
        <label className="field">
          <span className="field-label-row">
            Сценарий
            <Help tip="Набор демо-ситуаций: просадка формы, малая выборка, перегруз сильного менеджера и другие." metricName="Сценарий" />
          </span>
          <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
            {Object.entries(scenarios).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label-row">
            Код воспроизводимости
            <Help tip="Число для повторяемой генерации демо-дня. Одинаковый код даёт одинаковые данные." metricName="Код воспроизводимости" />
          </span>
          <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
        </label>
        <button className="btn" type="button" onClick={generate} disabled={loading}>
          {loading ? 'Генерация…' : 'Сгенерировать новый день'}
        </button>
        <button className="btn secondary" type="button" onClick={() => api.recalculate().then(load)}>Пересчитать</button>
        <button className="btn ghost" type="button" onClick={() => nav('/result')}>Результат дня</button>
      </div>

      <div className="muted" style={{ fontSize: '0.85rem' }}>
        Режим: {data.mode === 'demo' ? 'Демонстрация' : 'Анализ'} · Сценарий: {data.scenario_label} · Дата: {data.as_of}
      </div>

      <div className="kpi-grid">
        <KpiCard label="Все заявки" value={String(k.total_applications)} tip="Все поступившие заявки за день (обычно 70)." onClick={() => nav('/recommendations')} />
        <KpiCard label="Рекомендуется обработать" value={String(k.recommended)} tip="Заявки, которые вошли в дневную доступную загрузку команды." onClick={() => nav('/recommendations?selected=true')} />
        <KpiCard label="Не вошли в загрузку" value={String(k.queued)} tip="Заявки вне доступной загрузки: ниже приоритет или места заняты более выгодными заявками." onClick={() => nav('/recommendations?selected=false')} />
        <KpiCard
          label="Ожидаемая валовая маржа"
          value={money(k.expected_gm)}
          tip="Суммарная прогнозируемая валовая маржа по рекомендованным назначениям. Это прогноз, а не гарантированная прибыль."
        />
        <KpiCard
          label="Средняя маржа на переговор"
          value={money(k.avg_gm_per_talk)}
          tip="Ожидаемая валовая маржа, делённая на число рекомендованных переговоров."
        />
        <KpiCard
          label="Против простого варианта"
          value={`+${pctAlready(k.lift_vs_manual_pct)}`}
          tip="Сравнение с простым правилом «лучший менеджер по региону и продукту». Только на демонстрационных данных."
          onClick={() => nav('/simulation')}
        />
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 style={{ marginTop: 0 }} className="label-with-help">
            <span>Ожидаемая валовая маржа: подходы</span>
            <Help tip="Почему «каждой заявке лучший менеджер» не всегда лучше: доступная загрузка ограничена, нужен общий оптимум по всей группе заявок." metricName="Сравнение подходов" />
          </h3>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={comparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" interval={0} />
                <YAxis />
                <Tooltip formatter={(v) => money(Number(v))} />
                <Bar dataKey="value" fill="var(--color-primary)" radius={[6, 6, 0, 0]} name="Валовая маржа" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Распределение нагрузки</h3>
          <div style={{ width: '100%', height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={data.charts.load}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="manager" tickFormatter={(v) => String(v).replace('Менеджер ', 'М')} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="load" name="Назначено" fill="var(--color-primary)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="capacity" name="Доступная загрузка" fill="#d1d5db" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Ожидаемая валовая маржа по регионам</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={data.charts.by_region}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v) => money(Number(v))} />
                <Bar dataKey="expected_gm" fill="#4b5563" radius={[6, 6, 0, 0]} name="Валовая маржа" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Ожидаемая валовая маржа по продуктам</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={data.charts.by_product}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(v) => money(Number(v))} />
                <Bar dataKey="expected_gm" fill="#6b7280" radius={[6, 6, 0, 0]} name="Валовая маржа" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }} className="label-with-help">
          <span>Текущая форма менеджеров</span>
          <Help tip="Показывает, как свежие результаты менеджера отличаются от его обычного исторического уровня. Более новые данные имеют больший вес." metricName="Текущая форма менеджера" />
        </h3>
        <div style={{ width: '100%', height: 280 }}>
          <ResponsiveContainer>
            <BarChart data={data.charts.form_series}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="manager" tickFormatter={(v) => String(v).replace('Менеджер ', 'М')} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="previous" name="Предыдущий период" fill="#d1d5db" />
              <Bar dataKey="recent" name="Текущие 30 дней" fill="var(--color-primary)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
