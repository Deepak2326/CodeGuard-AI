export type Category = {
  id: number;
  name: string;
  cwe: string[];
  severity: string;
  description: string;
  root_cause: string;
  impact: string;
  mitigation: string;
  guidance: string;
};
export type Prediction = {
  predicted_category: string;
  class_id: number | null;
  leading_class_id: number;
  confidence: number;
  probabilities: { class_id: number; category: string; probability: number }[];
  uncertain: boolean;
  uncertainty_reasons: string[];
  explanation: Category;
  severity: string;
  severity_note: string;
  localization: string;
  confidence_note: string;
  model_version: string;
  history_id: number | null;
};
export type Metrics = {
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  weighted_f1: number;
  confusion_matrix: number[][];
  classification_report: Record<
    string,
    { precision: number; recall: number; "f1-score": number; support: number }
  >;
};
export type ModelInfo = {
  name: string;
  version: string;
  supported_languages: string[];
  categories: string[];
  evaluation: Metrics;
  dataset: {
    source: string;
    samples: number;
    groups: number;
    class_distribution: Record<string, number>;
    languages: Record<string, number>;
  };
  split_sizes: Record<string, number>;
  limitations: string[];
};
export type Scan = {
  id: number;
  created_at: string;
  language: string;
  predicted_category: string;
  class_id: number | null;
  confidence: number;
  uncertain: boolean;
};
export type HistoryData = {
  enabled: boolean;
  scans: Scan[];
  summary: null | {
    total: number;
    vulnerable: number;
    safe: number;
    uncertain: number;
    categories: Record<string, number>;
  };
};
