export interface BokehEmbedItem {
  target_id: string
  root_id: string
  doc: Record<string, unknown>
  version: string
}

export interface BokehEmbed {
  item: BokehEmbedItem
}
