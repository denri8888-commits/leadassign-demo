"""Сборка коротких PDF для работодателя (кириллица, Arial)."""
from __future__ import annotations

import shutil
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "employer_pdf"
OUT.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "T", parent=base["Title"], fontName="Arial-Bold", fontSize=16, leading=20,
            alignment=TA_CENTER, spaceAfter=8,
        ),
        "sub": ParagraphStyle(
            "S", parent=base["Normal"], fontName="Arial", fontSize=10, leading=13,
            alignment=TA_CENTER, textColor=colors.HexColor("#4b5563"), spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Arial-Bold", fontSize=12, leading=15,
            spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#111827"),
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontName="Arial", fontSize=10, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "BU", parent=base["Normal"], fontName="Arial", fontSize=10, leading=13,
            leftIndent=4, spaceAfter=2,
        ),
        "note": ParagraphStyle(
            "N", parent=base["Normal"], fontName="Arial", fontSize=9, leading=12,
            textColor=colors.HexColor("#4b5563"), spaceBefore=4, spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "F", parent=base["Normal"], fontName="Arial", fontSize=8,
            textColor=colors.HexColor("#6b7280"), alignment=TA_CENTER,
        ),
    }


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawCentredString(A4[0] / 2, 10 * mm, f"LeadAssign · стр. {doc.page}")
    canvas.restoreState()


def bullets(items, s):
    return ListFlowable(
        [ListItem(Paragraph(x, s["bullet"]), leftIndent=8, bulletColor=colors.HexColor("#111827")) for x in items],
        bulletType="bullet",
        start="•",
    )


def build(path: Path, story):
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def pdf_quick_start(s):
    story = [
        Paragraph("Быстрый старт", s["title"]),
        Paragraph("LeadAssign — демо для тестового задания", s["sub"]),
        Paragraph("1. Как запустить", s["h1"]),
        bullets([
            "Распакуйте архив в любую папку.",
            "Откройте файл <b>ЗАПУСТИТЬ_ДЕМО.bat</b> двойным щелчком.",
            "Дождитесь открытия браузера. Python и интернет не нужны.",
            "Если Windows спросит разрешение — разрешите запуск.",
        ], s),
        Paragraph("2. Что посмотреть за 5 минут", s["h1"]),
        bullets([
            "<b>Распределение заявок</b> — 70 заявок, 50 к обработке, 20 в очереди.",
            "<b>Рекомендации</b> — откройте любую заявку: почему этот менеджер, альтернативы, ручная замена.",
            "<b>Менеджеры</b> — загрузка и текущая форма.",
            "<b>Проверка эффекта</b> — сравнение с простым ручным правилом на демо-данных.",
        ], s),
        Paragraph("3. Главные документы", s["h1"]),
        bullets([
            "<b>01_Ответ_на_тестовое_задание.pdf</b> — полный ответ на задание (главный файл).",
            "<b>02_Краткие_результаты_демо.pdf</b> — цифры демо-дня.",
            "<b>03_Техническая_инструкция.pdf</b> — запуск из исходников и ограничения.",
        ], s),
        Paragraph(
            "Важно: все цифры в демо — на синтетических данных. Это не прибыль реальной компании.",
            s["note"],
        ),
    ]
    build(OUT / "00_Быстрый_старт.pdf", story)
    shutil.copyfile(OUT / "00_Быстрый_старт.pdf", OUT / "Быстрый_старт.pdf")


def pdf_answer(s):
    story = [
        Paragraph("Ответ на тестовое задание LeadAssign", s["title"]),
        Paragraph(
            "Тестовое задание сформулировано на примере мебельной компании. "
            "Подход не зависит от конкретного товара и может быть адаптирован "
            "к продажам окон, дверей и других продуктов.",
            s["sub"],
        ),
        Paragraph("1. Понимание бизнес-задачи", s["h1"]),
        Paragraph(
            "Задача не в том, чтобы найти «лучшего менеджера вообще». Нужно каждый день "
            "выбрать, какие заявки обработать и кому их отдать, чтобы при ограниченном "
            "числе переговоров получить больше ожидаемой валовой маржи. "
            "Ключевая единица решения — пара «заявка × менеджер».",
            s["body"],
        ),
        Paragraph("2. Данные и показатели", s["h1"]),
        Paragraph(
            "Для оценки используются история переговоров и новые заявки. Основные показатели: "
            "вероятность продажи, средняя валовая маржа при продаже, число наблюдений, "
            "свежесть данных, регион, продукт, менеджер, текущая форма. "
            "В демо часть полей упрощена: это синтетика для показа логики, а не выгрузка CRM.",
            s["body"],
        ),
        Paragraph("3. Логика назначения", s["h1"]),
        Paragraph(
            "Для каждой пары «заявка × менеджер» считаем ожидаемую валовую маржу: "
            "сглаженная вероятность продажи × средняя маржа при успешной сделке. "
            "Дальше выбираем набор назначений с учётом лимитов менеджеров и общего лимита команды. "
            "В демо для этого используется понятная математическая оптимизация; "
            "для первого запуска компании достаточно и более простого ранжирования.",
            s["body"],
        ),
        Paragraph("4. Изменение формы во времени", s["h1"]),
        Paragraph(
            "Свежие сделки весят больше старых (экспоненциальное затухание; "
            "период, когда вес примерно вдвое меньше, около 23–30 дней — настраивается). "
            "Отдельно смотрим короткое окно (14 дней) и длинную базу (около 6 месяцев): "
            "если есть просадка, это видно в объяснении. Отдельный «множитель формы» "
            "в целевую функцию не добавляли — иначе форма учитывалась бы дважды.",
            s["body"],
        ),
        Paragraph("5. Малые выборки", s["h1"]),
        Paragraph(
            "2 продажи из 2 переговоров не означают 100%. Используется сглаживание к общему уровню: "
            "p = (продажи + α × общий уровень) / (наблюдения + α), где α = 8 в демо. "
            "Пример: 2 из 2 при общем 50% даёт примерно 64%, а не 100%.",
            s["body"],
        ),
        Paragraph("6. Совместный учёт факторов", s["h1"]),
        Paragraph(
            "Регион, продукт и менеджер учитываются вместе через иерархию: "
            "сначала узкое сочетание, при нехватке данных — более общий уровень. "
            "Уверенность оценки влияет на отображение и понятность, но не умножается "
            "отдельно поверх уже сглаженной вероятности — без двойного учёта.",
            s["body"],
        ),
        Paragraph("7. 70 заявок → 50 переговоров", s["h1"]),
        Paragraph(
            "В демо-дне: 70 заявок, 5 менеджеров, до 10 переговоров на человека, до 50 на команду. "
            "Система одновременно выбирает, какие 50 обработать и кому их отдать; 20 остаются в очереди "
            "с понятной причиной. Одна заявка не назначается двум менеджерам.",
            s["body"],
        ),
        Paragraph("8. MVP за несколько недель", s["h1"]),
        Paragraph(
            "Для первого запуска компании достаточно простого пути: "
            "выгрузка из CRM → Excel или короткий скрипт на Python → расчёт показателей → "
            "сглаживание → оценка заявок → ранжирование → назначение с учётом лимитов. "
            "Полноценное веб-приложение и более сложная оптимизация — следующий этап. "
            "Текущий LeadAssign — рабочая демонстрация расширенной версии.",
            s["body"],
        ),
        Paragraph("9. Технологии и обоснование", s["h1"]),
        Paragraph(
            "Демо: Python (FastAPI), React, открытый решатель для назначения. "
            "При простых ограничениях хватает ранжирования и жадного распределения. "
            "Когда решение зависит от одновременного выбора многих заявок и менеджеров, "
            "удобна математическая оптимизация. Она не нужна «всегда» — только когда ограничений больше.",
            s["body"],
        ),
        Paragraph("10. Проверка эффекта", s["h1"]),
        Paragraph(
            "Эффект нужно проверить на реальных данных компании. Предлагаемый дизайн: "
            "4–8 недель, сравнение ручного распределения и системного. "
            "Главная метрика — валовая маржа на один состоявшийся переговорный контакт. "
            "Дополнительно: конверсия, средний чек, скидка, доля необработанных заявок, "
            "загрузка менеджеров, доля ручных изменений. "
            "Демо-симулятор показывает принцип сравнения, но не доказывает прибыль.",
            s["body"],
        ),
        Paragraph("11. Пример карточки заявки", s["h1"]),
        Paragraph("<b>Демонстрационный пример на синтетических данных.</b>", s["body"]),
        Paragraph(
            "Заявка A1033 · регион и продукт из демо · ожидаемая валовая маржа лучшей пары 91,51 · "
            "приоритет в таблице 89,59 (это не то же самое: приоритет только для сортировки) · "
            "вероятность продажи, маржа при продаже, число наблюдений, форма менеджера, "
            "свободная загрузка, альтернативы и причина выбора видны в карточке. "
            "Менеджера можно сменить вручную с указанием причины; если загрузка заполнена — система откажет.",
            s["body"],
        ),
        Paragraph(
            "Итог: сначала разобрана бизнес-задача, выбран простой объяснимый подход, "
            "определён MVP и способ проверки эффекта; затем собран рабочий прототип следующего этапа.",
            s["note"],
        ),
    ]
    build(OUT / "01_Ответ_на_тестовое_задание.pdf", story)
    shutil.copyfile(OUT / "01_Ответ_на_тестовое_задание.pdf", OUT / "Ответ_на_тестовое_задание_LeadAssign.pdf")


def pdf_results(s):
    story = [
        Paragraph("Краткие результаты демо", s["title"]),
        Paragraph("Синтетический день, код воспроизводимости 42", s["sub"]),
        Paragraph("Что получается на демо-дне", s["h1"]),
        bullets([
            "70 заявок → 50 к обработке → 20 в очереди.",
            "5 менеджеров, у каждого до 10 переговоров; загрузка полная 10/10.",
            "Ожидаемая валовая маржа оптимального назначения: <b>6074,34</b>.",
            "Против простого ручного правила на тех же данных — прирост около 7% (только демо).",
            "Защита от «заглядывания в будущее»: в оценку входит только история до даты решения.",
            "Ручная замена менеджера сохраняет исходную рекомендацию и не ломает лимиты.",
        ], s),
        Paragraph("Что сознательно не утверждаем", s["h1"]),
        Paragraph(
            "Мы не утверждаем, что система уже доказала экономический эффект для реальной компании. "
            "Цифры нужны, чтобы показать логику выбора и сравнить подходы на одинаковых данных.",
            s["body"],
        ),
        Paragraph("Проверки", s["h1"]),
        bullets([
            "Автотесты на утечку данных, малые выборки, лимиты, назначение, ручные изменения.",
            "На демо-дне текущий выбор 70→50 совпадает с проверкой оптимальности.",
        ], s),
    ]
    build(OUT / "02_Краткие_результаты_демо.pdf", story)


def pdf_tech(s):
    story = [
        Paragraph("Техническая инструкция", s["title"]),
        Paragraph("Как запустить и что внутри", s["sub"]),
        Paragraph("Вариант для работодателя (без установки)", s["h1"]),
        bullets([
            "Распаковать ZIP → ЗАПУСТИТЬ_ДЕМО.bat → браузер.",
            "EXE и BAT иногда режет почта или Windows SmartScreen — тогда лучше GitHub + исходники.",
        ], s),
        Paragraph("Вариант для разработчика", s["h1"]),
        Paragraph(
            "Backend: Python, venv, pip install -r backend/requirements.txt, "
            "uvicorn app.main:app --port 8000 (из папки backend, PYTHONPATH=.). "
            "Frontend: npm install && npm run dev в папке frontend.",
            s["body"],
        ),
        Paragraph("Структура", s["h1"]),
        bullets([
            "backend/ — API, оценка, назначение, генератор демо.",
            "frontend/ — интерфейс.",
            "tests/ — автотесты.",
            "data/demo/ — примеры CSV/Excel для импорта.",
            "docs/employer_pdf/ — PDF для работодателя.",
        ], s),
        Paragraph("Ограничения демо", s["h1"]),
        bullets([
            "Синтетические данные, не production CRM.",
            "Статистическая модель, не нейросеть — осознанно.",
            "Онлайн-хостинг на бесплатном тарифе возможен, но с «засыпанием» сервиса; для передачи задания надёжнее GitHub + ZIP + PDF.",
        ], s),
    ]
    build(OUT / "03_Техническая_инструкция.pdf", story)


def main():
    # убрать старые лишние PDF
    for old in OUT.glob("*.pdf"):
        old.unlink()
    s = styles()
    pdf_quick_start(s)
    pdf_answer(s)
    pdf_results(s)
    pdf_tech(s)
    print("PDFs:", sorted(p.name for p in OUT.glob("*.pdf")))


if __name__ == "__main__":
    main()
