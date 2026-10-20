/**
 * Происхождение значения в статье (упрощённый Provenance, ТЗ §21;
 * решение владельца В2, docs/SELECTION_TZ.md). Синхронно с
 * backend/app/models/context.py.
 */
export enum BlockType {
  Infobox = "infobox",
  Paragraph = "paragraph",
  ListItem = "list_item",
  Table = "table",
  Figure = "figure",
  Gallery = "gallery",
  Other = "other",
}

export interface ValueContext {
  block: BlockType;
  /** Заголовки разделов от верхнего уровня к вложенному; [] - до первого заголовка. */
  section_path: string[];
  /** Внутри служебного раздела (литература, ссылки, примечания...) или его подраздела. */
  service_section: boolean;
}
