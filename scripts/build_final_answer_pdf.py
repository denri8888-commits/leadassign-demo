"""Один финальный PDF-ответ на тестовое задание для работодателя."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "employer_pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "Ответ_на_тестовое_задание_LeadAssign.pdf"
OUT_ROOT = ROOT / "Ответ_на_тестовое_задание_LeadAssign.pdf"

DEMO_URL = "https://leadassign-demo.vercel.app"
GITHUB_URL = "https://github.com/denri8888-commits/leadassign-demo"

pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf"))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "T", parent=base["Title"], fontName="Arial-Bold", fontSize=15, leading=19,
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "sub": ParagraphStyle(
            "S", parent=base["Normal"], fontName="Arial", fontSize=9.5, leading=12,
            alignment=TA_CENTER, textColor=colors.HexColor("#4b5563"), spaceAfter=8,
        ),
        "link": ParagraphStyle(
            "L", parent=base["Normal"], fontName="Arial", fontSize=10, leading=13,
            alignment=TA_CENTER, textColor=colors.HexColor("#1d4ed8"), spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Arial-Bold", fontSize=11, leading=14,
            spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#111827"),
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontName="Arial", fontSize=9.5, leading=13,
            alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "BU", parent=base["Normal"], fontName="Arial", fontSize=9.5, leading=12,
            leftIndent=2, spaceAfter=1,
        ),
        "note": ParagraphStyle(
            "N", parent=base["Normal"], fontName="Arial", fontSize=8.5, leading=11,
            textColor=colors.HexColor("#4b5563"), spaceBefore=4, spaceAfter=4,
        ),
    }


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawCentredString(A4[0] / 2, 10 * mm, f"LeadAssign · ответ на тестовое · стр. {doc.page}")
    canvas.restoreState()


def bullets(items, s):
    return ListFlowable(
        [ListItem(Paragraph(x, s["bullet"]), leftIndent=6, bulletColor=colors.HexColor("#111827")) for x in items],
        bulletType="bullet",
        start="•",
    )


def main():
    s = styles()
    story = [
        Paragraph("Ответ на тестовое задание LeadAssign", s["title"]),
        Paragraph(
            "Тестовое задание сформулировано на примере мебельной компании. "
            "Подход не зависит от конкретного товара и может быть адаптирован "
            "к продажам окон, дверей и других продуктов.",
            s["sub"],
        ),
        Paragraph(f'<link href="{DEMO_URL}"><u>Онлайн-демо: {DEMO_URL}</u></link>', s["link"]),
        Paragraph(f'<link href="{GITHUB_URL}"><u>Код: {GITHUB_URL}</u></link>', s["link"]),
        Paragraph(
            "Цифры в демо — на синтетических данных. Это не прибыль реальной компании. "
            "Первый заход по ссылке после паузы может занять 15–40 секунд.",
            s["note"],
        ),
        Paragraph("1. Понимание бизнес-задачи", s["h1"]),
        Paragraph(
            "Задача не в том, чтобы найти «лучшего менеджера вообще». Нужно каждый день выбрать, "
            "какие заявки обработать и кому их отдать, чтобы при ограниченном числе переговоров "
            "получить больше ожидаемой валовой маржи. Единица решения — пара «заявка × менеджер».",
            s["body"],
        ),
        Paragraph("2. Данные и показатели", s["h1"]),
        Paragraph(
            "Используются история переговоров и новые заявки. Основные показатели: вероятность продажи, "
            "средняя валовая маржа при продаже, число наблюдений, свежесть данных, регион, продукт, "
            "менеджер, текущая форма. В демо часть полей упрощена — это синтетика для показа логики.",
            s["body"],
        ),
        Paragraph("3. Логика назначения", s["h1"]),
        Paragraph(
            "Для каждой пары «заявка × менеджер» считаем ожидаемую валовую маржу: "
            "сглаженная вероятность продажи × средняя маржа при успешной сделке. "
            "Дальше выбираем назначения с учётом лимитов менеджеров и общего лимита команды.",
            s["body"],
        ),
        Paragraph("4. Изменение формы во времени", s["h1"]),
        Paragraph(
            "Свежие сделки весят больше старых (вес примерно вдвое меньше через ~23–30 дней — настраивается). "
            "Отдельно смотрим короткое окно (14 дней) и длинную базу (~6 месяцев). "
            "Отдельный множитель «формы» в целевую функцию не добавляли — иначе форма учитывалась бы дважды.",
            s["body"],
        ),
        Paragraph("5. Малые выборки", s["h1"]),
        Paragraph(
            "2 продажи из 2 переговоров не означают 100%. Используется сглаживание к общему уровню "
            "(в демо сила сглаживания α = 8). Пример: 2 из 2 при общем 50% даёт около 64%, а не 100%.",
            s["body"],
        ),
        Paragraph("6. Совместный учёт факторов", s["h1"]),
        Paragraph(
            "Регион, продукт и менеджер учитываются вместе: сначала узкое сочетание, "
            "при нехватке данных — более общий уровень. Уверенность влияет на понятность оценки, "
            "но не умножается отдельно поверх уже сглаженной вероятности.",
            s["body"],
        ),
        Paragraph("7. 70 заявок → 50 переговоров", s["h1"]),
        Paragraph(
            "В демо-дне: 70 заявок, 5 менеджеров, до 10 переговоров на человека, до 50 на команду. "
            "Система одновременно выбирает, какие 50 обработать и кому их отдать; 20 остаются в очереди "
            "с причиной. Одна заявка не назначается двум менеджерам. "
            "На демо (код 42) ожидаемая валовая маржа выбранного набора: <b>6074,34</b>.",
            s["body"],
        ),
        Paragraph("8. MVP за несколько недель", s["h1"]),
        Paragraph(
            "Для первого запуска компании достаточно простого пути: выгрузка из CRM → Excel или короткий "
            "скрипт на Python → расчёт показателей → сглаживание → оценка заявок → ранжирование → "
            "назначение с учётом лимитов. Полноценное веб-приложение — следующий этап. "
            "Текущий LeadAssign — рабочая демонстрация расширенной версии.",
            s["body"],
        ),
        Paragraph("9. Технологии и обоснование", s["h1"]),
        Paragraph(
            "Демо: Python (FastAPI), React, открытый решатель для назначения. "
            "При простых ограничениях хватает ранжирования. Когда решение зависит от одновременного "
            "выбора многих заявок и менеджеров, удобна математическая оптимизация. "
            "Она не нужна «всегда» — только когда ограничений больше.",
            s["body"],
        ),
        Paragraph("10. Проверка эффекта", s["h1"]),
        Paragraph(
            "Эффект нужно проверить на реальных данных компании. Предложение: 4–8 недель, "
            "сравнение ручного распределения и системного. Главная метрика — валовая маржа "
            "на один состоявшийся переговорный контакт. Дополнительно: конверсия, средний чек, "
            "скидка, доля необработанных заявок, загрузка, доля ручных изменений. "
            "Демо показывает принцип сравнения, но не доказывает прибыль.",
            s["body"],
        ),
        Paragraph("11. Пример карточки заявки", s["h1"]),
        Paragraph("<b>Демонстрационный пример на синтетических данных.</b>", s["body"]),
        Paragraph(
            "Заявка A1033: ожидаемая валовая маржа лучшей пары <b>91,51</b>; "
            "приоритет в таблице <b>89,59</b> (это не то же самое — приоритет только для сортировки). "
            "В карточке видны вероятность продажи, маржа при продаже, число наблюдений, форма менеджера, "
            "свободная загрузка, альтернативы и причина выбора. Менеджера можно сменить вручную "
            "с указанием причины; если загрузка заполнена — система откажет.",
            s["body"],
        ),
        Paragraph("Что открыть в демо", s["h1"]),
        bullets(
            [
                f'<link href="{DEMO_URL}"><u>{DEMO_URL}</u></link> — рабочий сервис;',
                "экран «Распределение заявок» — 70 / 50 / 20;",
                "«Рекомендации» — карточка заявки и ручная замена;",
                "«Проверка эффекта» — сравнение с простым правилом на демо-данных;",
                f'<link href="{GITHUB_URL}"><u>{GITHUB_URL}</u></link> — исходный код.',
            ],
            s,
        ),
        Spacer(1, 4),
        Paragraph(
            "Итог: сначала разобрана бизнес-задача, выбран простой объяснимый подход, "
            "определён MVP и способ проверки эффекта; затем собран рабочий прототип следующего этапа.",
            s["note"],
        ),
    ]

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    OUT_ROOT.write_bytes(OUT.read_bytes())
    print(f"OK: {OUT}")
    print(f"OK: {OUT_ROOT}")


if __name__ == "__main__":
    main()
