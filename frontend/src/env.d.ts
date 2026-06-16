/// <reference types="vite/client" />

interface AOTSBootstrap {
  csrfToken: string
  testInstallation?: boolean
}

interface Window {
  __AOTS_BOOTSTRAP__?: AOTSBootstrap
  Bokeh?: {
    embed: { embed_item: (item: unknown, el: HTMLElement) => void }
    index: Record<string, { resize?: () => void }>
  }
}

declare module 'aladin-lite' {
  interface AladinInstance {
    destroy?: () => void
    addCatalog?: (catalog: unknown) => void
  }

  interface AladinLite {
    init: Promise<void>
    aladin: (target: HTMLElement | string, options?: Record<string, unknown>) => AladinInstance
    catalogFromVizieR: (
      catalog: string,
      target: string,
      radius: number,
      options?: Record<string, unknown>,
    ) => unknown
  }

  const A: AladinLite
  export default A
}
