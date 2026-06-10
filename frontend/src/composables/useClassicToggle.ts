const APP_PREFIX = '/app'

export function classicPath(spaPath: string): string {
  if (spaPath.startsWith(APP_PREFIX)) {
    return spaPath.slice(APP_PREFIX.length) || '/w/projects/'
  }
  return spaPath
}

export function spaPath(classicPath: string): string {
  if (classicPath.startsWith('/app')) return classicPath
  return `${APP_PREFIX}${classicPath}`
}

export function useClassicToggle() {
  function toClassic(): string {
    return classicPath(window.location.pathname + window.location.search)
  }

  function toSpa(): string {
    return spaPath(window.location.pathname + window.location.search)
  }

  return { toClassic, toSpa, classicPath, spaPath }
}
