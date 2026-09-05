export enum EntityType {
  Person = "person",
  Location = "location",
  Organization = "organization",
  Event = "event",
  Work = "work",
  Concept = "concept",
  Unknown = "unknown",
}

export enum SourceType {
  Infobox = "infobox",
  Template = "template",
  Table = "table",
  Coordinate = "coordinate",
  ArticleText = "article_text",
  Derived = "derived",
  // зарезервировано на будущее (не используется в MVP):
  Nlp = "nlp",
  Wikidata = "wikidata",
}

export enum DatePrecision {
  Day = "day",
  Month = "month",
  Year = "year",
  Decade = "decade",
  Century = "century",
  Unknown = "unknown",
}