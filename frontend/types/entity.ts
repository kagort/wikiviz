import { EntityType, SourceType } from "./common";

export interface Entity {
  id: string;
  type: EntityType;
  label: string;
  description: string | null;
  source: SourceType;
  confidence: number;
}