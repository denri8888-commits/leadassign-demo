import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

type Props = {
  tip: string
  label?: string
  /** For aria: human-readable metric name */
  metricName?: string
}

type Pos = { top: number; left: number; placement: 'top' | 'bottom' }

const MAX_WIDTH = 320
const GAP = 8
const PAD = 8

function computePosition(anchor: DOMRect): Pos {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const estimatedHeight = 96
  const spaceAbove = anchor.top
  const spaceBelow = vh - anchor.bottom
  const placement: 'top' | 'bottom' =
    spaceAbove < estimatedHeight + GAP && spaceBelow > spaceAbove ? 'bottom' : 'top'

  let top =
    placement === 'top' ? anchor.top - GAP : anchor.bottom + GAP
  // for top placement we position by bottom edge via transform later; store center-x
  let left = anchor.left + anchor.width / 2

  const half = Math.min(MAX_WIDTH, vw - PAD * 2) / 2
  left = Math.max(PAD + half, Math.min(vw - PAD - half, left))

  if (placement === 'top' && top < PAD) {
    return { top: anchor.bottom + GAP, left, placement: 'bottom' }
  }
  if (placement === 'bottom' && top + estimatedHeight > vh - PAD) {
    return { top: Math.max(PAD, anchor.top - GAP), left, placement: 'top' }
  }
  return { top, left, placement }
}

/**
 * Unified help icon. Tooltip renders in document.body via portal —
 * never clipped by overflow:auto tables/cards.
 * Compact fixed size so it does not distort table column widths.
 */
export function Help({ tip, label = '?', metricName }: Props) {
  const id = useId()
  const btnRef = useRef<HTMLButtonElement>(null)
  const tipRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<Pos | null>(null)
  const closeTimer = useRef<number | null>(null)

  const clearTimer = () => {
    if (closeTimer.current != null) {
      window.clearTimeout(closeTimer.current)
      closeTimer.current = null
    }
  }

  const updatePos = useCallback(() => {
    const el = btnRef.current
    if (!el) return
    setPos(computePosition(el.getBoundingClientRect()))
  }, [])

  const show = () => {
    clearTimer()
    setOpen(true)
  }

  const hide = () => {
    clearTimer()
    closeTimer.current = window.setTimeout(() => setOpen(false), 120)
  }

  useLayoutEffect(() => {
    if (!open) return
    updatePos()
  }, [open, tip, updatePos])

  useEffect(() => {
    if (!open) return
    const onScroll = () => updatePos()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('scroll', onScroll, true)
    window.addEventListener('resize', onScroll)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('scroll', onScroll, true)
      window.removeEventListener('resize', onScroll)
      window.removeEventListener('keydown', onKey)
    }
  }, [open, updatePos])

  useEffect(() => () => clearTimer(), [])

  const aria = metricName
    ? `Подсказка: ${metricName}`
    : `Подсказка`

  return (
    <>
      <button
        ref={btnRef}
        type="button"
        className="help-btn"
        aria-label={aria}
        aria-describedby={open ? id : undefined}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        onClick={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setOpen((v) => !v)
        }}
      >
        {label}
      </button>
      {open &&
        pos &&
        createPortal(
          <div
            ref={tipRef}
            id={id}
            role="tooltip"
            className={`help-tooltip help-tooltip--${pos.placement}`}
            style={{
              top: pos.top,
              left: pos.left,
              maxWidth: Math.min(MAX_WIDTH, window.innerWidth - PAD * 2),
            }}
            onMouseEnter={show}
            onMouseLeave={hide}
          >
            {tip}
          </div>,
          document.body,
        )}
    </>
  )
}

/** Compact label + help that keeps table header layout stable. */
export function LabelHelp({
  children,
  tip,
  as = 'span',
}: {
  children: React.ReactNode
  tip: string
  as?: 'span' | 'th-inner'
}) {
  const className = as === 'th-inner' ? 'th-label' : 'label-with-help'
  const name = typeof children === 'string' ? children : undefined
  return (
    <span className={className}>
      <span className="th-label-text">{children}</span>
      <Help tip={tip} metricName={name} />
    </span>
  )
}
