# UI Audit (промежуточный)

| Страница | Элемент | Проблема | Исправление | Проверено |
|----------|---------|----------|-------------|-----------|
| Рекомендации | Helper в th | tooltip через ::after + overflow таблицы → обрезка | Portal tooltip в body | да |
| Рекомендации | Уверенность [?] | helper раздувал ширину колонки | фиксированный `.help-btn` 16×16 + `th-label` | да |
| Все страницы | CSS `::after` tooltips | разные stacking contexts | единый `Help` + portal | да |
| Dashboard / Capacity / … | «GM», «capacity», «baseline» | англ./сокр. в UI | «валовая маржа», «доступная загрузка», «простой вариант» | да |
| Фильтры | разная высота | helpers в label ломали baseline | `field-label-row` + единый `--control-height` | да |
| Таблицы | числа | разный alignment | `.num` / `.center` | да |
| Рекомендации | пустой фильтр | пустой экран | empty-state | да |
| Drawer | z-index | хаотичный | tokens `--z-*` | да |
