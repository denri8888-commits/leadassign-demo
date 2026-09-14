import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, money, pct } from '../api'
import { Drawer } from '../components/Drawer'
import { Help, LabelHelp } from '../components/Help'

const REASONS = [
  'уже работает с этим клиентом',
  'знает продукт',
  'свободнее по времени',
  'причина не указана',
  'другое',
]

export function RecommendationsPage() {
  const [params, setParams] = useSearchParams()
  const [items, setItems] = useState<any[] | null>(null)
  const [regions, setRegions] = useState<string[]>([])
  const [products, setProducts] = useState<string[]>([])
  const [selected, setSelected] = useState<any | null>(null)
  const [overrideManager, setOverrideManager] = useState('')
  const [reason, setReason] = useState(REASONS[0])
  const [comment, setComment] = useState('')
  const [showFormula, setShowFormula] = useState(false)

  const filters = useMemo(
    () => ({
      region: params.get('region') || '',
      product: params.get('product') || '',
      manager: params.get('manager') || '',
      selected: params.get('selected') || '',
      confidence: params.get('confidence') || '',
    }),
    [params],
  )

  const load = async () => {
    const q: Record<string, string | boolean | undefined> = {
      region: filters.region || undefined,
      product: filters.product || undefined,
      manager: filters.manager || undefined,
      confidence: filters.confidence || undefined,
      selected: filters.selected === '' ? undefined : filters.selected === 'true',
    }
    const [apps, regs, prods] = await Promise.all([api.applications(q), api.regions(), api.products()])
    setItems(apps.items)
    setRegions(regs.items)
    setProducts(prods.items)
  }

  useEffect(() => {
    setItems(null)
    load().catch(console.error)
  }, [filters.region, filters.product, filters.manager, filters.selected, filters.confidence])

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (!value) next.delete(key)
    else next.set(key, value)
    setParams(next)
  }

  const open = async (id: string) => {
    const detail = await api.application(id)
    setSelected(detail)
    setOverrideManager(detail.recommended_manager || detail.best_available_manager)
    setShowFormula(false)
  }

  const applyOverride = async () => {
    if (!selected) return
    try {
      await api.override(selected.application_id, { manager: overrideManager, reason, comment })
      await load()
      await open(selected.application_id)
    } catch (e: any) {
      alert(e.message || 'Не удалось изменить менеджера')
    }
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Рекомендации</h1>
        <p className="muted">Все заявки дня: кого обработать и кому назначить.</p>
      </div>

      <div className="toolbar">
        <label className="field">
          <span className="field-label-row">Регион</span>
          <select value={filters.region} onChange={(e) => setFilter('region', e.target.value)}>
            <option value="">Все</option>
            {regions.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <label className="field">
          <span className="field-label-row">Продукт</span>
          <select value={filters.product} onChange={(e) => setFilter('product', e.target.value)}>
            <option value="">Все</option>
            {products.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <label className="field">
          <span className="field-label-row">Статус</span>
          <select value={filters.selected} onChange={(e) => setFilter('selected', e.target.value)}>
            <option value="">Все</option>
            <option value="true">Обработать</option>
            <option value="false">Не обрабатывать</option>
          </select>
        </label>
        <label className="field">
          <span className="field-label-row">
            Уверенность оценки
            <Help
              tip="Показывает, насколько надёжна текущая оценка. Если похожих исторических переговоров мало, система снижает уверенность и использует более общий уровень данных."
              metricName="Уверенность оценки"
            />
          </span>
          <select value={filters.confidence} onChange={(e) => setFilter('confidence', e.target.value)}>
            <option value="">Все</option>
            <option value="высокая">высокая</option>
            <option value="средняя">средняя</option>
            <option value="низкая">низкая</option>
          </select>
        </label>
      </div>

      <div className="card table-wrap">
        {items === null && <div className="loading-inline">Загрузка…</div>}
        {items && items.length === 0 && (
          <div className="empty-state">
            <div>По выбранным фильтрам данных нет.</div>
            <div style={{ marginTop: 8 }}>Измените фильтры.</div>
          </div>
        )}
        {items && items.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Заявка</th>
                <th>Регион</th>
                <th>Продукт</th>
                <th>
                  <LabelHelp as="th-inner" tip="Кому назначить, если заявка вошла в доступную загрузку команды.">
                    Рекомендация
                  </LabelHelp>
                </th>
                <th className="num">
                  <LabelHelp
                    as="th-inner"
                    tip="Прогнозируемая валовая маржа от обработки заявки конкретным менеджером с учётом вероятности продажи и исторических результатов. Это ожидаемое значение, а не гарантированная прибыль."
                  >
                    Ожидаемая валовая маржа
                  </LabelHelp>
                </th>
                <th className="num">Вероятность продажи</th>
                <th className="center">
                  <LabelHelp
                    as="th-inner"
                    tip="Показывает, насколько надёжна текущая оценка. Если похожих исторических переговоров мало, система снижает уверенность и использует более общий уровень данных."
                  >
                    Уверенность
                  </LabelHelp>
                </th>
                <th className="num">
                  <LabelHelp
                    as="th-inner"
                    tip="Вспомогательный показатель для сортировки таблицы. Это не ожидаемая валовая маржа и не то, что оптимизатор максимизирует. Оптимизатор смотрит на ожидаемую валовую маржу."
                  >
                    Приоритет
                  </LabelHelp>
                </th>
                <th className="center">Статус</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.application_id} className="clickable" onClick={() => open(r.application_id)}>
                  <td>{r.application_id}</td>
                  <td>{r.region}</td>
                  <td>{r.product}</td>
                  <td>{r.recommended_manager || '—'}</td>
                  <td className="num">{money(r.expected_gm)}</td>
                  <td className="num">{pct(r.p_sale)}</td>
                  <td className="center">
                    <span className={`badge ${r.confidence_label === 'высокая' ? 'ok' : r.confidence_label === 'средняя' ? 'warn' : 'danger'}`}>
                      {r.confidence_label}
                    </span>
                  </td>
                  <td className="num">{r.priority}</td>
                  <td className="center">
                    {r.selected ? <span className="badge ok">обработать</span> : <span className="badge muted">очередь</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Drawer open={!!selected} title={selected ? `Заявка ${selected.application_id}` : ''} onClose={() => setSelected(null)}>
        {selected && (
          <div className="stack">
            <div className="card" style={{ boxShadow: 'none' }}>
              <div><strong>Регион:</strong> {selected.region}</div>
              <div><strong>Продукт:</strong> {selected.product}</div>
              <div><strong>Дата:</strong> {selected.date}</div>
              <div><strong>Источник:</strong> {selected.source}</div>
              <div><strong>Клиент:</strong> {selected.client_type}</div>
              <div><strong>Срочность:</strong> {selected.urgency}</div>
            </div>

            {!selected.selected && (
              <div className="banner">Не вошла в загрузку: {selected.reject_reason}</div>
            )}

            <div>
              <h3>Рекомендация</h3>
              {selected.override && !selected.override.rejected ? (
                <div className="banner" style={{ marginBottom: 12 }}>
                  <div>Автоматическая рекомендация: <strong>{selected.override.original_manager || selected.system_recommended_manager}</strong>
                    {selected.override.original_expected_gm != null ? ` (${money(selected.override.original_expected_gm)})` : ''}
                  </div>
                  <div>Назначено вручную: <strong>{selected.recommended_manager}</strong> ({money(selected.expected_gm)})</div>
                  <div className="muted">Причина: {selected.override.reason}{selected.override.comment ? ` — ${selected.override.comment}` : ''}</div>
                </div>
              ) : (
                <p>
                  {selected.recommended_manager || selected.best_available_manager}: {money(selected.expected_gm)},
                  вероятность {pct(selected.p_sale)}, уверенность {selected.confidence_label}
                </p>
              )}
              <div className="muted" style={{ marginTop: 8 }}>
                Наблюдений: {selected.n_observations ?? '—'}
                {selected.expected_gm_per_sale != null ? ` · Маржа при продаже: ${money(selected.expected_gm_per_sale)}` : ''}
                {selected.free_capacity != null ? ` · Свободная загрузка менеджера: ${selected.free_capacity} из ${selected.manager_capacity}` : ''}
              </div>
              {selected.manager_form && (
                <div className="muted" style={{ marginTop: 6 }}>
                  Форма менеджера: короткое окно {selected.manager_form.short_metric} vs длинная база {selected.manager_form.long_metric}
                  {selected.manager_form.dip_flag ? ' (есть просадка)' : ''}.
                </div>
              )}
              <div className="muted" style={{ marginTop: 6 }}>
                Ожидаемая валовая маржа — экономическая ценность. Приоритет в таблице — только для удобной сортировки.
              </div>
            </div>

            <div>
              <h3>Почему он</h3>
              <ul>
                {selected.explanation.reasons.map((x: string) => <li key={x}>{x}</li>)}
              </ul>
              <p className="muted">{selected.explanation.disclaimer}</p>
            </div>

            <div>
              <h3>Альтернативы</h3>
              <table>
                <thead>
                  <tr>
                    <th>Менеджер</th>
                    <th className="num">Ожидаемая валовая маржа</th>
                    <th className="center">Уверенность</th>
                    <th>Примечание</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.explanation.alternatives.map((a: any) => (
                    <tr key={a.manager}>
                      <td>{a.manager}</td>
                      <td className="num">{money(a.expected_gm)}</td>
                      <td className="center">{a.confidence}</td>
                      <td>{a.note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button className="btn secondary" type="button" onClick={() => setShowFormula((v) => !v)}>
              Как получилась эта цифра?
            </button>
            {showFormula && (
              <div className="card" style={{ boxShadow: 'none' }}>
                {selected.explanation.formula.steps.map((s: any) => (
                  <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 6 }}>
                    <span>{s.label === 'Ожидаемая GM' ? 'Ожидаемая валовая маржа' : s.label === 'Средняя GM' ? 'Средняя валовая маржа' : s.label === 'GM при успешной сделке' ? 'Валовая маржа при успешной сделке' : s.label}</span>
                    <strong>
                      {s.format === 'money' ? money(Number(s.value)) :
                        s.format === 'pct' ? pct(Number(s.value)) :
                          String(s.value)}
                    </strong>
                  </div>
                ))}
                {selected.used_fallback && (
                  <p className="muted">
                    Оценка построена по более общему уровню данных («{selected.fallback_label}»), потому что по узкому сочетанию мало истории.
                  </p>
                )}
              </div>
            )}

            <div className="card" style={{ boxShadow: 'none' }}>
              <h3 style={{ marginTop: 0 }}>Изменить менеджера</h3>
              <p className="muted">Вы изменили рекомендацию системы. Почему? Ручное изменение — источник обратной связи для будущих улучшений.</p>
              <div className="stack">
                <select value={overrideManager} onChange={(e) => setOverrideManager(e.target.value)}>
                  {selected.all_manager_scores.map((s: any) => (
                    <option key={s.manager} value={s.manager}>{s.manager} — {money(s.expected_gm)}</option>
                  ))}
                </select>
                <select value={reason} onChange={(e) => setReason(e.target.value)}>
                  {REASONS.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
                <textarea rows={3} placeholder="Комментарий" value={comment} onChange={(e) => setComment(e.target.value)} />
                <button className="btn" type="button" onClick={applyOverride}>Применить изменение</button>
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}
