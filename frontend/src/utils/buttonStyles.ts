export type AppButtonVariant =
  | 'primary'
  | 'secondary'
  | 'danger'
  | 'ghost'
  | 'ghost-danger'
  | 'link'
  | 'icon'
  | 'icon-danger'

export type AppButtonSize = 'sm' | 'md'

export function buttonClasses(
  variant: AppButtonVariant = 'secondary',
  size: AppButtonSize = 'md',
  extra?: string,
): string {
  const classes: string[] = []

  switch (variant) {
    case 'primary':
      classes.push('aots-btn-primary')
      break
    case 'secondary':
      classes.push('aots-btn-secondary')
      break
    case 'danger':
      classes.push('aots-btn-danger')
      break
    case 'ghost':
      classes.push('aots-btn-ghost')
      break
    case 'ghost-danger':
      classes.push('aots-btn-ghost-danger')
      break
    case 'link':
      classes.push('aots-btn-link')
      break
    case 'icon':
      classes.push('aots-btn-icon')
      break
    case 'icon-danger':
      classes.push('aots-btn-icon-danger')
      break
  }

  if (size === 'sm' && variant !== 'icon' && variant !== 'icon-danger' && variant !== 'link') {
    classes.push('aots-btn-sm')
  }

  if (extra) classes.push(extra)

  return classes.join(' ')
}
