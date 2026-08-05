/**
 * ui.tsx — dependency-free React primitives built on the tokens defined in
 * `src/styles/tokens.css`. Styling approach: Tailwind arbitrary-value
 * utilities referencing CSS custom properties (e.g. `bg-[var(--hub-accent)]`)
 * — chosen over inline `style` objects so variants stay declarative,
 * greppable, and easy to diff. Inline `style` is not used anywhere in this
 * file; keep it that way when extending these components.
 *
 * See DESIGN.md for the full component contract, when-to-use rules, and
 * the migration checklist that points existing pages at these primitives.
 */
import { X } from 'lucide-react'
import { forwardRef, useEffect, useRef, useState, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { t } from './i18n'
import type { ProviderId } from './uiHelpers'

const cx = (...parts: Array<string | false | undefined>) => parts.filter(Boolean).join(' ')

const focusRing = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent'

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive'
export type ButtonSize = 'sm' | 'md'

export type ButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> & {
  variant?: ButtonVariant
  size?: ButtonSize
  selected?: boolean
  /** Optional leading icon slot, rendered before the label and marked decorative. */
  icon?: ReactNode
  children: ReactNode
}

const buttonBase = cx(
  'inline-flex items-center justify-center gap-space-2',
  'rounded-md font-medium whitespace-nowrap transition-colors',
  'disabled:cursor-not-allowed disabled:opacity-40',
  focusRing,
)

const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-app hover:bg-accent-hover',
  secondary: cx(
    'border border-border-strong bg-elevated',
    'text-primary hover:bg-hover',
  ),
  ghost: 'text-secondary hover:bg-hover hover:text-primary',
  destructive: cx(
    'border border-error text-error',
    'hover:bg-error-subtle',
  ),
}

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'h-10 px-space-3 text-caption leading-caption',
  md: 'h-10 px-space-4 text-label leading-label',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'secondary', size = 'md', selected = false, icon, className, children, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx(buttonBase, selected ? 'border border-accent bg-accent-subtle text-primary' : buttonVariants[variant], buttonSizes[size], className)}
      {...rest}
    >
      {icon ? <span aria-hidden="true" className="inline-flex shrink-0 items-center">{icon}</span> : null}
      {children}
    </button>
  )
})

// ---------------------------------------------------------------------------
// IconButton
// ---------------------------------------------------------------------------

export type IconButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> & {
  icon: ReactNode
  variant?: 'default' | 'handle'
  /** Required — icon-only controls must always expose an accessible name. */
  'aria-label': string
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { icon, variant = 'default', className, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx(
        variant === 'handle'
          ? 'inline-flex h-10 w-10 min-h-10 min-w-10 items-center justify-center rounded-full border border-accent bg-app'
          : cx(
            'inline-flex h-10 w-10 min-h-10 min-w-10 items-center justify-center',
            'rounded-md text-secondary transition-colors',
            'hover:bg-hover hover:text-primary',
            'disabled:cursor-not-allowed disabled:opacity-40',
            focusRing,
          ),
        className,
      )}
      {...rest}
    >
      {icon}
    </button>
  )
})

// ---------------------------------------------------------------------------
// Input / Select / Textarea
// ---------------------------------------------------------------------------

const controlBase = cx(
  'w-full rounded-md border border-border-subtle',
  'bg-elevated text-primary',
  'text-body leading-body',
  'placeholder:text-muted',
  'focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent',
  'disabled:cursor-not-allowed disabled:opacity-40',
)

export type InputProps = InputHTMLAttributes<HTMLInputElement>

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input({ className, ...rest }, ref) {
  return (
    <input
      ref={ref}
      className={cx(controlBase, 'h-input px-space-3', className)}
      {...rest}
    />
  )
})

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select({ className, children, ...rest }, ref) {
  return (
    <select
      ref={ref}
      className={cx(controlBase, 'h-input px-space-3', className)}
      {...rest}
    >
      {children}
    </select>
  )
})

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea({ className, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      className={cx(
        controlBase,
        'min-h-composer-min px-space-3 py-space-2',
        className,
      )}
      {...rest}
    />
  )
})

// ---------------------------------------------------------------------------
// Chip
// ---------------------------------------------------------------------------

export type ChipProps = {
  children: ReactNode
  selected?: boolean
  muted?: boolean
  /** Presence enables the removable variant and renders a close-icon affordance. */
  onRemove?: () => void
  /** Accessible label for the remove button. Defaults to the translated Remove label. */
  removeLabel?: string
  className?: string
}

export function Chip({ children, selected = false, muted = false, onRemove, removeLabel = t('misc.ui.remove'), className }: ChipProps) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-space-1 rounded-full',
        selected ? 'border border-accent bg-accent-subtle text-primary' : 'border border-border-subtle bg-elevated',
        'px-space-3 py-[3px] text-caption',
        !selected && (muted ? 'text-muted opacity-60' : 'text-secondary'),
        className,
      )}
    >
      {children}
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          aria-label={removeLabel}
          className={cx(
            'ml-[2px] inline-flex h-10 w-10 items-center justify-center rounded-full leading-none',
            'text-muted hover:bg-hover hover:text-primary',
            focusRing,
          )}
        >
          <X size={16} strokeWidth={1.75} aria-hidden="true" />
        </button>
      ) : null}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Status
// ---------------------------------------------------------------------------

export type StatusKind =
  | 'ready'
  | 'running'
  | 'paused'
  | 'setup-required'
  | 'not-installed'
  | 'rate-limited'
  | 'error'
  | 'offline'

export type StatusProps = {
  kind: StatusKind
  /** Override the default Vietnamese label. The label is always rendered — colour is never the only signal. */
  label?: string
  className?: string
}

const statusDotClass: Record<StatusKind, string> = {
  ready: 'bg-success',
  running: 'bg-accent',
  paused: 'bg-muted',
  'setup-required': 'bg-warning',
  'not-installed': 'bg-muted',
  'rate-limited': 'bg-warning',
  error: 'bg-error',
  offline: 'bg-muted',
}

const statusLabels: Record<StatusKind, string> = {
  ready: t('misc.status.ready'),
  running: t('misc.status.running'),
  paused: t('misc.status.paused'),
  'setup-required': t('misc.status.setupRequired'),
  'not-installed': t('misc.status.notInstalled'),
  'rate-limited': t('misc.status.rateLimited'),
  error: t('misc.status.error'),
  offline: t('misc.status.offline'),
}

export function Status({ kind, label, className }: StatusProps) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-[6px] text-caption text-secondary',
        className,
      )}
    >
      <span aria-hidden="true" className={cx('h-2 w-2 shrink-0 rounded-full', statusDotClass[kind])} />
      {label ?? statusLabels[kind]}
    </span>
  )
}

export type RunStatusKind = 'running' | 'success' | 'error' | 'interrupted' | 'queued' | 'neutral'
export type RunStatusBadgeProps = { kind: RunStatusKind; label: string; className?: string }

const runStatusBadgeClass: Record<RunStatusKind, string> = {
  running: 'border border-accent bg-accent-subtle text-primary', success: 'border border-success bg-surface text-primary', error: 'border border-error bg-error-subtle text-primary', interrupted: 'border border-warning bg-warning-subtle text-primary', queued: 'border border-border-strong bg-elevated text-secondary', neutral: 'border border-border-subtle bg-elevated text-secondary',
}
const runStatusBadgeMark: Record<RunStatusKind, string> = { running: '●', success: '✓', error: '!', interrupted: '◆', queued: '○', neutral: '?' }

export function RunStatusBadge({ kind, label, className }: RunStatusBadgeProps) {
  return <span className={cx('inline-flex items-center gap-[5px] rounded-full px-space-2 py-[2px] text-caption leading-caption', runStatusBadgeClass[kind], className)}><span aria-hidden="true" className="text-[10px] leading-none">{runStatusBadgeMark[kind]}</span>{label}</span>
}

// ---------------------------------------------------------------------------
// ProviderDot
// ---------------------------------------------------------------------------

export type ProviderDotProps = {
  provider: ProviderId
  className?: string
}

// Reuses the existing --color-claude/codex/nvidia tokens from
// index.css's @theme block via their Tailwind bg-* utilities — provider
// colour usage is restricted to this 6-8px identity dot everywhere else.
const providerDotClass: Record<ProviderId, string> = {
  claude: 'bg-claude',
  codex: 'bg-codex',
  nvidia: 'bg-nvidia',
}

export function ProviderDot({ provider, className }: ProviderDotProps) {
  return (
    <span
      aria-hidden="true"
      className={cx('inline-block h-[7px] w-[7px] shrink-0 rounded-full', providerDotClass[provider], className)}
    />
  )
}

// ---------------------------------------------------------------------------
// EmptyState
// ---------------------------------------------------------------------------

export type EmptyStateAction = {
  label: string
  onClick: () => void
  icon?: ReactNode
}

export type EmptyStateProps = {
  icon?: ReactNode
  title: string
  description?: string
  /** Only the first 4 actions are rendered. */
  actions?: EmptyStateAction[]
  className?: string
}

export function EmptyState({ icon, title, description, actions = [], className }: EmptyStateProps) {
  const visibleActions = actions.slice(0, 4)
  return (
    <div
      className={cx(
        'flex flex-col items-center justify-center gap-space-2 text-center',
        'rounded-lg border border-dashed border-border-subtle',
        'px-space-4 py-space-8',
        className,
      )}
    >
      {icon ? <span aria-hidden="true" className="text-muted">{icon}</span> : null}
      <h3 className="text-label leading-label font-semibold text-primary">
        {title}
      </h3>
      {description ? (
        <p className="max-w-sm text-caption leading-caption text-secondary">
          {description}
        </p>
      ) : null}
      {visibleActions.length > 0 ? (
        <div className="mt-space-2 flex flex-wrap justify-center gap-space-2">
          {visibleActions.map(action => (
            <Button key={action.label} variant="ghost" size="sm" icon={action.icon} onClick={action.onClick}>
              {action.label}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Popover
// ---------------------------------------------------------------------------

type PopoverProps = {
  /** Rendered as the trigger. Receives the current open state so it can show a caret. */
  label: ReactNode
  children: ReactNode | ((close: () => void) => ReactNode)
  align?: 'start' | 'end'
  triggerClassName?: string
  className?: string
  'aria-label'?: string
}

/**
 * Click-to-open disclosure anchored to its trigger. Use it to keep secondary
 * controls — model pickers, provider health, pane settings — out of the layout
 * until asked for, instead of stacking them permanently above the content.
 */
export function Popover({ label, children, align = 'start', triggerClassName, className, ...rest }: PopoverProps) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: MouseEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false) }
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => { document.removeEventListener('mousedown', onPointerDown); document.removeEventListener('keydown', onKeyDown) }
  }, [open])

  return (
    <div ref={root} className="relative">
      <Button
        variant="ghost"
        size="sm"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={rest['aria-label']}
        onClick={() => setOpen(current => !current)}
        className={triggerClassName}
      >
        {label}
      </Button>
      {open ? (
        <div
          className={cx(
            'absolute z-20 mt-space-1 min-w-[220px] rounded-[var(--hub-radius-lg)] border border-border-subtle bg-surface p-space-3 shadow-lg',
            align === 'end' ? 'right-0' : 'left-0',
            className,
          )}
        >
          {typeof children === 'function' ? children(() => setOpen(false)) : children}
        </div>
      ) : null}
    </div>
  )
}
