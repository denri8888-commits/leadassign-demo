import { useEffect, useState } from 'react'
import { api } from '../api'
import { Help } from '../components/Help'

const LABEL: Record<string, string> = {
  team_capacity: 'Сколько переговоров команда может провести за день',
  recency_half_life_days: 'Через сколько дней старые сделки «весят» вдвое меньше',
  recency_lambda: 'Технический коэффициент свежести (обычно не трогаем)',
  prior_strength: 'Сила сглаживания на маленькой выборке',
  min_observations: 'Минимум наблюдений для узкой оценки',
  extra_manager_monthly_cost: 'Стоимость доп. менеджера в месяц, BYN',
  working_days_per_month: 'Рабочих дней в месяце',
  form_short_days: 'Короткое окно формы, дней',
  form_long_days: 'Длинная база формы, дней',
  form_dip_threshold: 'Порог заметной просадки формы (доля)',
  assignment_mode: 'Как назначать заявки',
}

export function SettingsPage() {
  const [settings, setSettings] = useState<any | null>(null)
  const [helpers, setHelpers] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.settings().then((r) => {
      setSettings(r.settings)
      setHelpers(r.helpers)
    })
  }, [])

  if (!settings) return <div className="loading-inline">Загрузка…</div>

  const setNum = (key: string, value: number) => setSettings({ ...settings, [key]: value })
  const setCap = (manager: string, value: number) =>
    setSettings({ ...settings, manager_capacities: { ...settings.manager_capacities, [manager]: value } })

  const save = async () => {
    setSaving(true)
    try {
      const payload = { ...settings }
      // период полураспада — понятный параметр; λ пересчитаем на сервере
      if (payload.recency_half_life_days != null) {
        delete payload.recency_lambda
      }
      const r = await api.updateSettings(payload) as { settings?: any }
      setSettings(r.settings || payload)
      setSaved('Настройки применены, распределение пересчитано.')
    } finally {
      setSaving(false)
    }
  }

  const field = (key: string, tip: string, control: React.ReactNode) => (
    <label className="field" key={key}>
      <span className="field-label-row">
        {LABEL[key] || key}
        <Help tip={tip} metricName={LABEL[key] || key} />
      </span>
      {control}
    </label>
  )

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Настройки модели</h1>
        <p className="muted">Каждая настройка влияет на оценку или дневную загрузку. Без «магии».</p>
      </div>
      {saved && <div className="banner">{saved}</div>}
      <div className="card stack">
        {field(
          'team_capacity',
          helpers.team_capacity || 'Максимум переговоров команды за день.',
          <input type="number" value={settings.team_capacity} onChange={(e) => setNum('team_capacity', Number(e.target.value))} />,
        )}
        {field(
          'recency_half_life_days',
          helpers.recency_half_life_days || 'Через сколько дней вес старой сделки становится примерно вдвое меньше. Обычно 23–30 дней.',
          <input type="number" step="1" value={settings.recency_half_life_days} onChange={(e) => setNum('recency_half_life_days', Number(e.target.value))} />,
        )}
        {field(
          'prior_strength',
          helpers.prior_strength || 'Не даёт считать 2 продажи из 2 переговоров как 100% вероятность.',
          <input type="number" step="0.5" value={settings.prior_strength} onChange={(e) => setNum('prior_strength', Number(e.target.value))} />,
        )}
        {field(
          'min_observations',
          helpers.min_observations || 'Ниже этого числа система чаще опирается на более общий уровень данных.',
          <input type="number" value={settings.min_observations} onChange={(e) => setNum('min_observations', Number(e.target.value))} />,
        )}
        {field(
          'form_short_days',
          helpers.form_short_days || 'Короткое окно для проверки текущей формы менеджера.',
          <input type="number" value={settings.form_short_days} onChange={(e) => setNum('form_short_days', Number(e.target.value))} />,
        )}
        {field(
          'form_long_days',
          helpers.form_long_days || 'Длинная база для сравнения формы (около полугода).',
          <input type="number" value={settings.form_long_days} onChange={(e) => setNum('form_long_days', Number(e.target.value))} />,
        )}
        {field(
          'form_dip_threshold',
          helpers.form_dip_threshold || 'Например 0.15 = просадка на 15% и больше считается заметной.',
          <input type="number" step="0.01" value={settings.form_dip_threshold} onChange={(e) => setNum('form_dip_threshold', Number(e.target.value))} />,
        )}
        {field(
          'extra_manager_monthly_cost',
          helpers.extra_manager_monthly_cost || 'Демо-параметр. В реальной компании подставьте свои цифры.',
          <input type="number" value={settings.extra_manager_monthly_cost} onChange={(e) => setNum('extra_manager_monthly_cost', Number(e.target.value))} />,
        )}
        {field(
          'working_days_per_month',
          helpers.working_days_per_month || 'Нужен для перевода дневного эффекта в месячный.',
          <input type="number" value={settings.working_days_per_month} onChange={(e) => setNum('working_days_per_month', Number(e.target.value))} />,
        )}
        {field(
          'assignment_mode',
          helpers.assignment_mode || 'Оптимальный — совместный выбор заявок и менеджеров. Простой — понятный запасной вариант.',
          <select value={settings.assignment_mode} onChange={(e) => setSettings({ ...settings, assignment_mode: e.target.value })}>
            <option value="optimal">Оптимальный</option>
            <option value="greedy">Простой (жадный)</option>
          </select>,
        )}
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }} className="label-with-help">
          <span>Дневная загрузка менеджеров</span>
          <Help tip={helpers.manager_capacities || 'Сколько переговоров может провести каждый менеджер. Числа не обязаны быть одинаковыми.'} metricName="Загрузка менеджеров" />
        </h3>
        <div className="kpi-grid">
          {Object.entries(settings.manager_capacities || {}).map(([m, c]) => (
            <label key={m} className="field">{m}
              <input type="number" value={c as number} onChange={(e) => setCap(m, Number(e.target.value))} />
            </label>
          ))}
        </div>
      </div>
      <button className="btn" type="button" onClick={save} disabled={saving}>
        {saving ? 'Считаю…' : 'Пересчитать распределение'}
      </button>
    </div>
  )
}
