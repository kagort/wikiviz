import type { ValueContext } from "./context";
import { SourceType } from "./common";

export interface Image {
  url: string;
  thumbnail_url: string | null;
  caption: string | null;
  alt: string | null;
  source: SourceType;
  context: ValueContext | null;
}