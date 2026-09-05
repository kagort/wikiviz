import { Article, Section } from "./article";
import { Entity } from "./entity";
import { Event } from "./event";
import { Image } from "./image";
import { InfoboxField } from "./infobox";
import { Location } from "./location";
import { NumericValue } from "./number";
import { Table } from "./table";

export interface NormalizedArticleModel {
  article: Article;
  sections: Section[];
  infobox: Record<string, InfoboxField>;
  tables: Table[];
  locations: Location[];
  events: Event[];
  numbers: NumericValue[];
  people: Entity[];
  organizations: Entity[];
  works: Entity[];
  relations: Record<string, unknown>[];
  images: Image[];
  links: string[];
  metadata: Record<string, unknown>;
}