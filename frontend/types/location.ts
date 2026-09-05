import { SourceType } from "./common";

export interface Location {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  description: string | null;
  source: SourceType;
  confidence: number;
}