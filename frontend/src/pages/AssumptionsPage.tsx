import { useEffect, useState } from 'react'
import { api } from '../api'

export function AssumptionsPage() {
  const [assumptions, setAssumptions] = useState<{ title: string; text: string }[]>([])
  const [roadmap, setRoadmap] = useState<any | null>(null)

  useEffect(() => {
    Promise.all([api.assumptions(), api.roadmap()]).then(([a, r]) => {
      setAssumptions(a.items)
      setRoadmap(r)
    })
  }, [])

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Допущения MVP</h1>
        <p className="muted">Прозрачные рамки прототипа.</p>
      </div>
      <div className="kpi-grid">
        {assumptions.map((a) => (
          <div key={a.title} className="card">
            <h3 style={{ marginTop: 0 }}>{a.title}</h3>
            <p className="muted">{a.text}</p>
          </div>
        ))}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Дополнительные факторы — следующий этап</h2>
        <p>Сначала доказать пользу на доступных данных. Затем добавлять признаки только если они улучшают прогноз и допустимы.</p>
        <ul>
          <li>новый/повторный клиент, источник, бюджет</li>
          <li>длительность переговоров, причина отказа, конкурент</li>
          <li>сезонность, тип клиента</li>
        </ul>
      </div>

      {roadmap && (
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Будущее развитие</h2>
          <ol>
            {roadmap.next_features.map((x: string) => <li key={x}>{x}</li>)}
          </ol>
          <p>{roadmap.note}</p>
          <p className="muted">{roadmap.external_data}</p>
          <p className="muted">{roadmap.demographics}</p>
          <p>
            Если компания фиксирует причину отказа и уход к конкуренту — это можно использовать позже.
            Важно различать гипотезу, реальный признак и подтверждённое влияние.
          </p>
        </div>
      )}
    </div>
  )
}
