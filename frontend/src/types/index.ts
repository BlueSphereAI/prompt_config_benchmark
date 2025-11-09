export interface Experiment {
  id: number;
  experiment_id: string;
  prompt_name: string;
  config_name: string;
  rendered_prompt: string;
  config_json: Record<string, any>;
  response: string;
  finish_reason: string | null;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  error: string | null;
  success: boolean;
  metadata_json: Record<string, any> | null;
  created_at: string;
}

export interface Evaluation {
  id: number;
  evaluation_id: string;
  experiment_id: string;
  result_id: number;
  evaluation_type: string;
  evaluator_name: string;
  score: number;
  criteria_json: Record<string, any> | null;
  notes: string | null;
  strengths: string | null;
  weaknesses: string | null;
  evaluated_at: string;
  metadata_json: Record<string, any> | null;
}

export interface ConfigStats {
  count: number;
  success_rate: number;
  avg_duration: number | null;
  min_duration: number | null;
  max_duration: number | null;
  avg_cost: number | null;
  total_cost: number;
  avg_tokens: number | null;
  total_tokens: number;
  avg_score: number | null;
  min_score: number | null;
  max_score: number | null;
  num_evaluations: number;
}

export interface ConfigComparison {
  prompt_name: string;
  best_by_score: string | null;
  best_by_speed: string | null;
  best_by_cost: string | null;
  config_stats: Record<string, ConfigStats>;
  total_experiments: number;
  total_evaluations: number;
}

export interface DashboardStats {
  total_experiments: number;
  total_prompts: number;
  total_configs: number;
  total_evaluations: number;
  total_cost: number;
  avg_duration: number;
  success_rate: number;
  recent_experiments: Experiment[];
}

export interface EvaluationCreate {
  experiment_id: string;
  evaluation_type?: string;
  evaluator_name: string;
  score: number;
  criteria?: Record<string, any>;
  notes?: string;
  strengths?: string;
  weaknesses?: string;
  metadata?: Record<string, any>;
}
