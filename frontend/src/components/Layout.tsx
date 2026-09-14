import { NavLink, Outlet } from 'react-router-dom'

const links = [
  ['/', 'Распределение заявок'],
  ['/recommendations', 'Рекомендации'],
  ['/managers', 'Менеджеры'],
  ['/matrix', 'Регионы и товары'],
  ['/capacity', 'Анализ загрузки'],
  ['/simulation', 'Проверка эффекта'],
  ['/result', 'Результат дня'],
  ['/settings', 'Настройки модели'],
  ['/import', 'Импорт данных'],
  ['/assumptions', 'Допущения и развитие'],
]

export function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          Lead<span>Assign</span>
        </div>
        <div className="muted" style={{ fontSize: '0.8rem', marginBottom: 12 }}>
          Ожидаемая валовая маржа при ограниченной мощности команды
        </div>
        <div
          className="banner"
          style={{ padding: '8px 10px', fontSize: '0.78rem', marginBottom: 14 }}
          title="Эти значения созданы для демонстрации принципа работы системы. Для реального применения решение подключается к данным компании."
        >
          <strong>ДЕМО-РЕЖИМ</strong>
          <div>Синтетические данные</div>
        </div>
        <nav>
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
