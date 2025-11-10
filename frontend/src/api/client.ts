import type {
  Experiment,
  Evaluation,
  EvaluationCreate,
  ConfigComparison,
  DashboardStats,
  ExperimentRun,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // Experiments
  async getExperiments(params?: {
    prompt_name?: string;
    config_name?: string;
    success_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<Experiment[]> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return fetchAPI<Experiment[]>(`/experiments${query ? `?${query}` : ''}`);
  },

  async getExperiment(experimentId: string): Promise<Experiment> {
    return fetchAPI<Experiment>(`/experiments/${experimentId}`);
  },

  // Prompts and Configs
  async getPrompts(): Promise<string[]> {
    return fetchAPI<string[]>('/prompts');
  },

  async getPromptsList(): Promise<string[]> {
    const response = await fetchAPI<{ prompts: Array<{ name: string }> }>('/prompts/list');
    return response.prompts.map(p => p.name);
  },

  async getConfigs(): Promise<string[]> {
    return fetchAPI<string[]>('/configs');
  },

  // Analysis
  async analyzePrompt(
    promptName: string,
    includeUnevaluated = true
  ): Promise<ConfigComparison> {
    return fetchAPI<ConfigComparison>(
      `/analysis/prompt/${encodeURIComponent(promptName)}?include_unevaluated=${includeUnevaluated}`
    );
  },

  async analyzeOverall(includeUnevaluated = true): Promise<{
    config_stats: Record<string, any>;
    total_experiments: number;
    total_evaluations: number;
  }> {
    return fetchAPI(
      `/analysis/overall?include_unevaluated=${includeUnevaluated}`
    );
  },

  // Evaluations
  async getEvaluations(experimentId: string): Promise<Evaluation[]> {
    return fetchAPI<Evaluation[]>(`/evaluations/${experimentId}`);
  },

  async createEvaluation(evaluation: EvaluationCreate): Promise<Evaluation> {
    return fetchAPI<Evaluation>('/evaluations', {
      method: 'POST',
      body: JSON.stringify(evaluation),
    });
  },

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return fetchAPI<DashboardStats>('/dashboard');
  },

  // AI-Assisted Ranking System
  async getCompareData(promptName: string, runId?: string): Promise<any> {
    const url = runId
      ? `/compare/${encodeURIComponent(promptName)}?run_id=${encodeURIComponent(runId)}`
      : `/compare/${encodeURIComponent(promptName)}`;
    return fetchAPI(url);
  },

  async getReviewPrompts(activeOnly = true): Promise<any[]> {
    return fetchAPI(`/review-prompts?active_only=${activeOnly}`);
  },

  async startBatchEvaluation(params: {
    prompt_name: string;
    review_prompt_id: string;
    model_evaluator?: string;
    parallel?: boolean;
    run_id?: string;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    searchParams.append('prompt_name', params.prompt_name);
    searchParams.append('review_prompt_id', params.review_prompt_id);
    if (params.model_evaluator) {
      searchParams.append('model_evaluator', params.model_evaluator);
    }
    if (params.parallel !== undefined) {
      searchParams.append('parallel', String(params.parallel));
    }
    if (params.run_id) {
      searchParams.append('run_id', params.run_id);
    }
    return fetchAPI(`/ai-evaluate/batch?${searchParams.toString()}`, {
      method: 'POST',
    });
  },

  async saveRanking(params: {
    prompt_name: string;
    evaluator_name: string;
    ranked_experiment_ids: string[];
    based_on_ai_batch_id?: string;
    notes?: string;
    time_spent_seconds?: number;
  }): Promise<any> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          // For arrays, we'll send as JSON in body
          return;
        }
        searchParams.append(key, String(value));
      }
    });

    // For array param, we need to use POST body
    return fetchAPI(`/rankings?${searchParams.toString()}`, {
      method: 'POST',
    });
  },

  async getRecommendation(promptName: string): Promise<any> {
    return fetchAPI(`/recommendations/${encodeURIComponent(promptName)}`);
  },

  // Prompt Management
  async runAllConfigsForPrompt(promptName: string): Promise<any> {
    const searchParams = new URLSearchParams();
    searchParams.append('prompt_name', promptName);
    return fetchAPI(`/experiments/run-all-configs?${searchParams.toString()}`, {
      method: 'POST',
    });
  },

  async getPromptsMetadata(activeOnly = true): Promise<any> {
    return fetchAPI(`/prompts/metadata?active_only=${activeOnly}`);
  },

  async getPromptDetail(name: string): Promise<any> {
    return fetchAPI(`/prompts/detail/${encodeURIComponent(name)}`);
  },

  async savePrompt(name: string, messages: any[], description?: string, category?: string, tags?: string[]): Promise<any> {
    return fetchAPI(`/prompts/update/${encodeURIComponent(name)}`, {
      method: 'PUT',
      body: JSON.stringify({
        messages,
        description,
        category,
        tags,
      }),
    });
  },

  async deletePrompt(name: string): Promise<any> {
    return fetchAPI(`/prompts/delete/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });
  },

  async deleteExperimentsByPrompt(promptName: string): Promise<any> {
    return fetchAPI(`/experiments/delete-by-prompt/${encodeURIComponent(promptName)}`, {
      method: 'DELETE',
    });
  },

  // LLM Config Management
  async listConfigs(activeOnly = true): Promise<any[]> {
    return fetchAPI(`/configs/list?active_only=${activeOnly}`);
  },

  async getConfig(name: string): Promise<any> {
    return fetchAPI(`/configs/get/${encodeURIComponent(name)}`);
  },

  async createConfig(config: {
    name: string;
    model: string;
    max_output_tokens?: number;
    verbosity?: string;
    reasoning_effort?: string;
    description?: string;
  }): Promise<any> {
    return fetchAPI('/configs/create', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  async updateConfig(name: string, config: {
    model?: string;
    max_output_tokens?: number;
    verbosity?: string;
    reasoning_effort?: string;
    description?: string;
  }): Promise<any> {
    return fetchAPI(`/configs/update/${encodeURIComponent(name)}`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  async deleteConfig(name: string): Promise<any> {
    return fetchAPI(`/configs/delete/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });
  },

  async cloneConfig(name: string, newName: string): Promise<any> {
    return fetchAPI(`/configs/clone/${encodeURIComponent(name)}?new_name=${encodeURIComponent(newName)}`, {
      method: 'POST',
    });
  },

  // Experiment Acceptability
  async updateExperimentAcceptability(experimentId: string, isAcceptable: boolean): Promise<any> {
    return fetchAPI(`/experiments/${experimentId}/acceptability`, {
      method: 'PUT',
      body: JSON.stringify({ is_acceptable: isAcceptable }),
    });
  },

  // Experiment Runs
  async getRunsForPrompt(promptName: string): Promise<ExperimentRun[]> {
    return fetchAPI<ExperimentRun[]>(`/prompts/${encodeURIComponent(promptName)}/runs`);
  },

  async getRun(runId: string): Promise<{ run: ExperimentRun; experiments: Experiment[] }> {
    return fetchAPI(`/runs/${encodeURIComponent(runId)}`);
  },

  async deleteRun(runId: string): Promise<{ status: string; run_id: string }> {
    return fetchAPI(`/runs/${encodeURIComponent(runId)}`, {
      method: 'DELETE',
    });
  },
};
