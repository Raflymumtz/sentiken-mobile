// Tipe data yang mencerminkan skema response backend (app/schemas/*.py).
// Field opsional/nullable mengikuti Pydantic (None -> null).

export interface Pagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface AppSource {
  id: string;
  app_name: string;
  package_id: string;
  play_store_url: string | null;
  description: string | null;
  language: string;
  country: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  app_source_id: string;
  description: string | null;
  period_start: string | null;
  period_end: string | null;
  preprocessing_status: JobLikeStatus;
  labeling_status: JobLikeStatus;
  label_mode: "binary" | "ternary";
  training_status: JobLikeStatus;
  created_at: string;
  updated_at: string;
  review_count: number;
  app_source?: AppSource | null;
}

export type JobLikeStatus = "pending" | "running" | "completed" | "failed";
export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export interface DatasetSummary {
  dataset_id: string;
  total_reviews: number;
  rating_distribution: Record<string, number>;
  label_distribution: Record<string, number>;
  preprocessing_status: JobLikeStatus;
  labeling_status: JobLikeStatus;
  training_status: JobLikeStatus;
  active_training_run_id: string | null;
}

export interface Review {
  id: string;
  dataset_id: string;
  app_source_id: string;
  review_id: string | null;
  username: string | null;
  user_image: string | null;
  content: string;
  score: number | null;
  thumbs_up_count: number;
  review_date: string | null;
  app_version: string | null;
  reply_content: string | null;
  reply_date: string | null;
  source: string;
  fetched_at: string;
  created_at: string;
  preprocessing_result?: PreprocessingResult | null;
  sentiment_labels?: SentimentLabelInfo[];
}

export interface ReviewDetail extends Review {
  predicted_label?: string | null;
  prediction_confidence?: number | null;
  nearest_neighbors?: NeighborInfo[];
}

export interface PreprocessingResult {
  case_folded_text: string;
  cleaned_text: string;
  normalized_text: string;
  tokens: string[];
  tokens_no_stopword: string[];
  stemmed_text: string;
  final_text: string;
  processed_at: string;
}

export interface SentimentLabelInfo {
  label_mode: "binary" | "ternary";
  positive_score: number;
  negative_score: number;
  sentiment_score: number;
  label: "positive" | "negative" | "neutral";
  is_excluded_from_training: boolean;
  labeled_at: string;
}

export interface CollectionJob {
  id: string;
  app_source_id: string;
  dataset_id: string;
  period_start: string | null;
  period_end: string | null;
  max_reviews: number;
  language: string;
  country: string;
  sort_order: string;
  method: string;
  status: JobStatus;
  progress_percent: number;
  found_count: number;
  new_count: number;
  duplicate_count: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImportPreviewRow {
  row_number: number;
  data: Record<string, string | null>;
  is_valid: boolean;
  errors: string[];
}

export interface ImportPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  detected_columns: string[];
  missing_required_columns: string[];
  sample_rows: ImportPreviewRow[];
  upload_token: string;
}

export interface ImportJob {
  id: string;
  dataset_id: string;
  filename: string;
  status: JobStatus;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  new_count: number;
  duplicate_count: number;
  error_message: string | null;
  validation_report: { row_errors?: string[] };
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface DictionaryEntry {
  id: string;
  word?: string;
  weight?: number;
  informal_word?: string;
  formal_word?: string;
  created_at: string;
  updated_at: string;
}

export type DictionaryType = "positive" | "negative" | "normalization" | "stopwords";

export interface PreprocessingStatusResponse {
  dataset_id: string;
  status: JobLikeStatus;
  total_reviews: number;
  processed_reviews: number;
  remaining_reviews: number;
  progress_percent: number;
}

export interface LabelSummary {
  dataset_id: string;
  label_mode: string;
  status: JobLikeStatus;
  total_labeled: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  excluded_from_training: number;
}

export interface DataSplit {
  id: string;
  dataset_id: string;
  label_mode: string;
  train_size: number;
  test_size: number;
  random_state: number;
  stratify: boolean;
  train_count: number;
  test_count: number;
  class_distribution: Record<string, number>;
  created_at: string;
}

export interface TfidfConfig {
  max_features: number | null;
  min_df: number;
  max_df: number;
  ngram_min: number;
  ngram_max: number;
  sublinear_tf: boolean;
  norm: "l1" | "l2" | "none";
}

export interface KnnConfig {
  n_neighbors: number;
  metric: string;
  algorithm: string;
  weights: "uniform" | "distance";
  leaf_size: number;
}

export interface TrainingRunItem {
  id: string;
  k_value: number;
  metric: string;
  weights: string;
  accuracy: number;
  precision_weighted: number;
  recall_weighted: number;
  f1_weighted: number;
  training_time_seconds: number;
  prediction_time_seconds: number;
  is_selected: boolean;
}

export interface TrainingRun {
  id: string;
  dataset_id: string;
  data_split_id: string | null;
  label_mode: string;
  run_type: "single" | "experiment";
  tfidf_config: TfidfConfig;
  knn_config: KnnConfig;
  status: JobLikeStatus;
  is_active: boolean;
  model_version: string | null;
  selection_metric: string;
  training_time_seconds: number | null;
  prediction_time_seconds: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  activated_at: string | null;
  items: TrainingRunItem[];
}

export interface ConfusionMatrix {
  labels: string[];
  matrix: number[][];
}

export interface EvaluationMetrics {
  training_run_id: string;
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  f1_macro: number;
  precision_weighted: number;
  recall_weighted: number;
  f1_weighted: number;
  support: Record<string, number>;
  confusion_matrix: ConfusionMatrix;
  classification_report: Record<string, unknown>;
  warnings: string[];
  created_at: string;
}

export interface NeighborInfo {
  review_id: string | null;
  distance: number;
  label: string;
  text: string;
}

export interface SinglePredictionResult {
  original_text: string;
  final_text: string;
  predicted_label: string;
  confidence: number;
  k_used: number;
  neighbors: NeighborInfo[];
  model_version: string | null;
  training_run_id: string;
  prediction_time_ms: number;
}

export interface DashboardSummary {
  has_data: boolean;
  total_datasets: number;
  total_reviews: number;
  total_reviews_by_app: Record<string, number>;
  total_reviews_pln_mobile: number;
  total_reviews_mypertamina: number;
  sentiment_counts: { positive: number; negative: number; neutral: number };
  sentiment_percentage: { positive: number; negative: number; neutral: number };
  active_model_version: string | null;
  active_k: number | null;
  active_metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
  } | null;
  latest_job_status: string | null;
  latest_job_type: string | null;
}

export interface SentimentComparisonItem {
  app_source_id: string;
  app_name: string;
  total_reviews: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  average_rating: number | null;
  rating_distribution: Record<string, number>;
}

export interface SentimentTrendPoint {
  period: string;
  app_source_id: string;
  app_name: string;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  total_count: number;
}

export interface RatingDistributionItem {
  app_source_id: string;
  app_name: string;
  distribution: Record<string, number>;
}

export interface FrequentTerm {
  term: string;
  frequency: number;
}
