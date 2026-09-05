import { SourceType } from "./common";

export interface Table {
  id: string;
  title: string | null;
  columns: string[];
  rows: string[][];
  source: SourceType;
}