import { useState } from 'react'
import { api } from '../api'
import { Help } from '../components/Help'

export function ImportPage() {
  const [kind, setKind] = useState('history')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<any | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const onPreview = async () => {
    if (!file) return
    setError('')
    try {
      const p = await api.importPreview(file, kind)
      setPreview(p)
      const m: Record<string, string> = {}
      Object.entries(p.suggested_mapping || {}).forEach(([k, v]) => {
        if (v) m[k] = String(v)
      })
      setMapping(m)
    } catch (e: any) {
      setError(e.message || 'Не удалось прочитать файл')
    }
  }

  const onApply = async () => {
    if (!file) return
    setError('')
    try {
      const r = await api.importApply(file, kind, mapping)
      setMessage(`Загружено строк: ${r.rows}. Режим: ${r.mode === 'analysis' ? 'Анализ' : r.mode}. Аналитика пересчитана.`)
    } catch (e: any) {
      setError(e.message || 'Ошибка импорта')
    }
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Импорт данных</h1>
        <p className="muted">Режим «Анализ»: CSV/Excel без CRM. Демонстрация — отдельный режим на синтетике.</p>
      </div>
      <div className="toolbar">
        <label className="field">
          <span className="field-label-row">
            Тип файла
            <Help tip="История — прошлые переговоры и сделки. Заявки — входящий поток дня." metricName="Тип файла" />
          </span>
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="history">История</option>
            <option value="applications">Заявки</option>
          </select>
        </label>
        <label className="field">
          <span className="field-label-row">Файл</span>
          <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </label>
        <button className="btn secondary" type="button" onClick={onPreview} disabled={!file}>Показать колонки</button>
        <button className="btn" type="button" onClick={onApply} disabled={!file || !preview}>Построить аналитику</button>
      </div>
      {message && <div className="banner">{message}</div>}
      {error && <div className="banner" style={{ borderColor: '#fecaca', background: '#fef2f2' }}>{error}</div>}
      {preview && (
        <>
          <div className="card">
            <h3 style={{ marginTop: 0 }} className="label-with-help">
              <span>Сопоставление колонок</span>
              <Help tip={preview.helpers?.mapping || 'Сопоставьте колонки файла с полями системы.'} metricName="Сопоставление" />
            </h3>
            <div className="kpi-grid">
              {Object.keys(preview.suggested_mapping).map((field) => (
                <label key={field} className="field">{field}
                  <select
                    value={mapping[field] || ''}
                    onChange={(e) => setMapping({ ...mapping, [field]: e.target.value })}
                  >
                    <option value="">—</option>
                    {preview.columns.map((c: string) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
              ))}
            </div>
          </div>
          <div className="card table-wrap">
            <h3 style={{ marginTop: 0 }} className="label-with-help">
              <span>Превью</span>
              <Help tip={preview.helpers?.preview || 'Первые строки файла после чтения.'} metricName="Превью" />
            </h3>
            <table>
              <thead>
                <tr>{preview.columns.map((c: string) => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {preview.preview_rows.map((row: any, idx: number) => (
                  <tr key={idx}>
                    {preview.columns.map((c: string) => <td key={c}>{row[c]}</td>)}
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
