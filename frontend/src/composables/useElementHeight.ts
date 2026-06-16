import { onUnmounted, ref, watch, type Ref } from 'vue'

/** Tracks an element's border-box height via ResizeObserver. */
export function useElementHeight(element: Ref<HTMLElement | null>) {
  const height = ref<number | null>(null)
  let observer: ResizeObserver | null = null

  function stop() {
    observer?.disconnect()
    observer = null
  }

  function start(el: HTMLElement) {
    stop()
    const update = () => {
      height.value = el.getBoundingClientRect().height
    }
    update()
    observer = new ResizeObserver(update)
    observer.observe(el)
  }

  watch(
    element,
    (el) => {
      if (el) start(el)
      else {
        stop()
        height.value = null
      }
    },
    { immediate: true },
  )

  onUnmounted(stop)

  return { height }
}
