import type { ValueContext } from "./context";
import { DatePrecision, SourceType } from "./common";

export interface Event {
  id: string;
  date: string;
  date_precision: DatePrecision;
  title: string;
  description: string | null;
  source: SourceType;
  confidence: number;
  context: ValueContext | null;
}