import { SourceType } from "./common";

export interface InfoboxField {
  key: string;
  label: string;
  value: string;
  normalized_value: string | null;
  source: SourceType;
}