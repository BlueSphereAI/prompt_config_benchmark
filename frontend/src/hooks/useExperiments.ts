import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { EvaluationCreate } from '../types';

export function useExperiments(params?: {
  prompt_name?: string;
  config_name?: string;
  success_only?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['experiments', params],
    queryFn: () => api.getExperiments(params),
  });
}

export function useExperiment(experimentId: string) {
  return useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => api.getExperiment(experimentId),
    enabled: !!experimentId,
  });
}

export function usePrompts() {
  return useQuery({
    queryKey: ['prompts'],
    queryFn: () => api.getPrompts(),
  });
}

export function useConfigs() {
  return useQuery({
    queryKey: ['configs'],
    queryFn: () => api.getConfigs(),
  });
}

export function usePromptAnalysis(promptName: string, includeUnevaluated = true) {
  return useQuery({
    queryKey: ['analysis', 'prompt', promptName, includeUnevaluated],
    queryFn: () => api.analyzePrompt(promptName, includeUnevaluated),
    enabled: !!promptName,
  });
}

export function useOverallAnalysis(includeUnevaluated = true) {
  return useQuery({
    queryKey: ['analysis', 'overall', includeUnevaluated],
    queryFn: () => api.analyzeOverall(includeUnevaluated),
  });
}

export function useEvaluations(experimentId: string) {
  return useQuery({
    queryKey: ['evaluations', experimentId],
    queryFn: () => api.getEvaluations(experimentId),
    enabled: !!experimentId,
  });
}

export function useCreateEvaluation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (evaluation: EvaluationCreate) => api.createEvaluation(evaluation),
    onSuccess: (_, variables) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['evaluations', variables.experiment_id] });
      queryClient.invalidateQueries({ queryKey: ['analysis'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.getDashboardStats(),
  });
}
