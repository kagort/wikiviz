import { SourceType } from "./common";

export interface Table {
  id: string;
  title: string | null;
  columns: string[];
  rows: string[][];
  /** Строки во всю ширину, не являющиеся данными: пояснения и "Источник: ...". */
  notes: string[];
  source: SourceType;
}