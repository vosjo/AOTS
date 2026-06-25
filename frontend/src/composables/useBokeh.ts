import type { BokehEmbedItem } from '@/types/bokeh'

const BOKEH_VERSION = '3.9.1'

const BOKEH_SCRIPTS = [
  `https://cdn.bokeh.org/bokeh/release/bokeh-${BOKEH_VERSION}.min.js`,
  `https://cdn.bokeh.org/bokeh/release/bokeh-widgets-${BOKEH_VERSION}.min.js`,
  `https://cdn.bokeh.org/bokeh/release/bokeh-gl-${BOKEH_VERSION}.min.js`,
]

let loadPromise: Promise<void> | null = null

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve()
      return
    }
    const el = document.createElement('script')
    el.src = src
    el.onload = () => resolve()
    el.onerror = () => reject(new Error(`Failed to load ${src}`))
    document.head.appendChild(el)
  })
}

export async function loadBokeh(): Promise<void> {
  if (window.Bokeh) return
  if (!loadPromise) {
    loadPromise = (async () => {
      for (const src of BOKEH_SCRIPTS) {
        await loadScript(src)
      }
    })()
  }
  await loadPromise
}

export function resizeBokehIn(host: HTMLElement): void {
  const Bokeh = window.Bokeh
  if (!Bokeh?.index) return
  for (const el of host.querySelectorAll('[id]')) {
    const doc = Bokeh.index[el.id]
    if (doc && typeof doc.resize === 'function') {
      doc.resize()
    }
  }
}

function scheduleBokehResize(host: HTMLElement): void {
  const resize = () => resizeBokehIn(host)
  requestAnimationFrame(() => {
    resize()
    requestAnimationFrame(resize)
  })
  window.setTimeout(resize, 100)
}

export async function embedBokehItem(host: HTMLElement, item: BokehEmbedItem): Promise<void> {
  await loadBokeh()
  host.innerHTML = `<div id="${item.target_id}"></div>`
  const Bokeh = window.Bokeh
  if (!Bokeh?.embed?.embed_item) {
    throw new Error('Bokeh embed API not available')
  }
  Bokeh.embed.embed_item(item)
  scheduleBokehResize(host)
}
