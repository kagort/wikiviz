import { SourceType } from "./common";

export interface NumericValue {
  label: string;
  value: number;
  unit: string | null;
  year: number | null;
  source: SourceType;
}