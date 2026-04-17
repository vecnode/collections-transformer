export type AnalyserType = "binary" | "score" | "opinion" | "keywords" | string;

export interface User {
  sub: string;
  user_id: string;
  username: string;
  email: string;
  name: string;
  nickname: string;
  role: string;
  affiliation: string;
  [key: string]: unknown;
}

export interface ItemContentValue {
  text?: string;
  [key: string]: unknown;
}

export interface ItemContent {
  content_type?: string;
  content_value?: ItemContentValue;
  [key: string]: unknown;
}

export interface CollectionItem {
  _id: string;
  position?: number;
  object_id?: string | null;
  content?: ItemContent[];
  [key: string]: unknown;
}

export interface Label {
  item_id: string;
  value?: string | number | boolean;
  rationale?: string;
  highlight?: unknown;
  [key: string]: unknown;
}

export interface Labelset {
  _id: string;
  label_type?: AnalyserType;
  labels: Label[];
  [key: string]: unknown;
}

export interface Dataset {
  _id?: string;
  id?: string;
  name: string;
  type?: string;
  dataset_type?: string;
  artworks: CollectionItem[];
  [key: string]: unknown;
}

export interface PredictionResult {
  [itemId: string]: string | number | boolean | null;
}

export interface Analyser {
  _id?: string;
  analyser_id?: string;
  analyser_type?: AnalyserType;
  dataset_id?: string;
  labelset_id?: string;
  owner?: string;
  predictions?: PredictionResult[];
  sample_ids?: string[];
  [key: string]: unknown;
}

export interface ContentFilterThemeResult {
  filtered: boolean;
  [key: string]: unknown;
}

export interface ContentFilterError {
  error?: {
    code?: string;
    inner_error?: {
      content_filter_results?: Record<string, ContentFilterThemeResult>;
    };
  };
}

export interface AuthResult {
  success: boolean;
  error?: string;
}
