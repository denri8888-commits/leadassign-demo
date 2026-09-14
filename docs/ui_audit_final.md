# UI Audit Final

## Найдено
14+ проблем (tooltip clipping, layout helpers, термины GM/capacity/baseline, alignment, empty states, z-index).

## Исправлено
Все перечисленные в docs/ui_audit.md.

## Не исправлено
Полноценные Playwright screenshot-тесты не добавлялись (избегаем тяжёлого framework ради MVP). Backend smoke + ручная проверка ZIP.

## Основные изменения
1. Единый Help с portal в document.body и auto-placement
2. Фиксированный размер иконки — не ломает ширину колонок
3. Design tokens z-index / control height
4. Терминология: валовая маржа, доступная загрузка, простой вариант
5. Empty states, выравнивание .num/.center
6. Пересборка GermanWindows_AI_TestTask_Demo_v2.zip

## Проверенные страницы
Все 10 вкладок + drawer рекомендаций.

## Проверенные состояния
hover/focus tooltip, table overflow, filters, loading, empty filter.
