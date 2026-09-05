export interface Article {
  id: number;
  title: string;
  language: string;
  url: string;
  description: string | null;
  summary: string | null;
}

export interface Section {
  id: string;
  title: string;
  level: number;
  children: Section[];
}