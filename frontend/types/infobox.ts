import { SourceType } from "./common";

export interface InfoboxField {
  key: string;
  label: string;
  /** Подзаголовок группы ("Area" для "Total" у France) или null для поля верхнего уровня. */
  group: string | null;
  value: string;
  normalized_value: string | null;
  source: SourceType;
}