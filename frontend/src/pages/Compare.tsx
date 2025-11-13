import { useState, useEffect } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, RefreshCw, X, ExternalLink, ArrowUpDown } from 'lucide-react';
import { api } from '../api/client';
import { DragCarousel } from '../components/DragCarousel';

type SortOption = 'ai' | 'human' | 'time' | 'price' | 'tokens';

export default function Compare() {
  const { promptName } = useParams<{ promptName: string }>();
  const [searchParams] = useSearchParams();
  const runId = searchParams.get('run_id');
  const queryClient = useQueryClient();
  const [rankedIds, setRankedIds] = useState<string[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [startTime] = useState(Date.now());
  const [showAIModal, setShowAIModal] = useState(false);
  const [selectedReviewPrompt, setSelectedReviewPrompt] = useState<string>('');
  const [evaluatorModel] = useState('gpt-5'); // Always use GPT-5 with reasoning
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>('ai');

  // Fetch all compare data (with optional run_id filtering)
  const { data: compareData, isLoading, error, refetch } = useQuery({
    queryKey: ['compare', promptName, runId],
    queryFn: async () => {
      const data = await api.getCompareData(promptName!, runId || undefined);
      console.log('Compare data received:', {
        hasOriginalPrompt: !!data.original_prompt,
        originalPromptLength: data.original_prompt?.length || 0,
        originalPromptPreview: data.original_prompt?.substring(0, 100),
        numExperiments: data.experiments?.length || 0
      });
      return data;
    },
    enabled: !!promptName,
  });

  // Fetch review prompts for AI evaluation
  const { data: reviewPrompts } = useQuery({
    queryKey: ['review-prompts'],
    queryFn: () => api.getReviewPrompts(true),
  });

  // Toggle acceptability mutation
  const toggleAcceptability = useMutation({
    mutationFn: ({ experimentId, isAcceptable }: { experimentId: string; isAcceptable: boolean }) =>
      api.updateExperimentAcceptability(experimentId, isAcceptable),
    onSuccess: async () => {
      await refetch();
    },
  });

  const handleToggleAcceptability = (experimentId: string, isAcceptable: boolean) => {
    toggleAcceptability.mutate({ experimentId, isAcceptable });
  };

  const startAIEvaluation = useMutation({
    mutationFn: (params: { prompt_name: string; review_prompt_id: string; model_evaluator: string; run_id?: string }) => {
      console.log('Starting AI evaluation with params:', params);
      setIsEvaluating(true);
      return api.startBatchEvaluation(params);
    },
    onSuccess: (data) => {
      console.log('AI evaluation started successfully:', data);
      setShowAIModal(false);
      // Poll for completion every 5 seconds for up to 2 minutes
      const pollInterval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['compare', promptName, runId] });
      }, 5000);

      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setIsEvaluating(false);
        queryClient.invalidateQueries({ queryKey: ['compare', promptName, runId] });
      }, 120000);
    },
    onError: (error) => {
      console.error('AI evaluation failed:', error);
      setIsEvaluating(false);
    },
  });

  const saveRanking = useMutation({
    mutationFn: (ranking: any) => api.saveRanking(ranking),
    onSuccess: () => {
      // Refresh data to get updated recommendation
      queryClient.invalidateQueries({ queryKey: ['compare', promptName] });
      setHasChanges(false);
    },
  });

  // Sort experiments based on selected sort option
  const getSortedExperimentIds = (sortOption: SortOption): string[] => {
    if (!compareData || !compareData.experiments) return [];

    const experiments = [...compareData.experiments];

    switch (sortOption) {
      case 'ai':
        // Use AI ranking if available, otherwise fallback to original order
        return compareData.ai_evaluation?.ranked_experiment_ids
          || experiments.map((exp: any) => exp.experiment_id);

      case 'human':
        // Use the most recent human ranking if available
        if (compareData.human_rankings && compareData.human_rankings.length > 0) {
          const mostRecentRanking = compareData.human_rankings.reduce((latest: any, current: any) => {
            return new Date(current.created_at) > new Date(latest.created_at) ? current : latest;
          });
          return mostRecentRanking.ranked_experiment_ids;
        }
        // Fallback to AI or original order
        return compareData.ai_evaluation?.ranked_experiment_ids
          || experiments.map((exp: any) => exp.experiment_id);

      case 'time':
        // Sort by duration (fastest first)
        return experiments
          .sort((a: any, b: any) => (a.duration_seconds || 0) - (b.duration_seconds || 0))
          .map((exp: any) => exp.experiment_id);

      case 'price':
        // Sort by cost (cheapest first)
        return experiments
          .sort((a: any, b: any) => (a.estimated_cost_usd || 0) - (b.estimated_cost_usd || 0))
          .map((exp: any) => exp.experiment_id);

      case 'tokens':
        // Sort by tokens (fewest first)
        return experiments
          .sort((a: any, b: any) => (a.total_tokens || 0) - (b.total_tokens || 0))
          .map((exp: any) => exp.experiment_id);

      default:
        return experiments.map((exp: any) => exp.experiment_id);
    }
  };

  useEffect(() => {
    if (compareData && compareData.experiments) {
      // Initialize rankedIds on first load
      if (rankedIds.length === 0) {
        const sortedIds = getSortedExperimentIds(sortBy);
        setRankedIds(sortedIds);

        // If AI evaluation exists and no human ranking yet, save AI ranking as initial human ranking
        if (compareData.ai_evaluation && !compareData.human_rankings?.length) {
          const timeSpent = (Date.now() - startTime) / 1000;
          saveRanking.mutate({
            prompt_name: promptName!,
            evaluator_name: 'User',
            ranked_experiment_ids: sortedIds,
            based_on_ai_batch_id: compareData.ai_evaluation.batch_id,
            time_spent_seconds: timeSpent,
          });
        }
      }

      // Stop evaluating spinner if AI evaluation is complete
      if (compareData.ai_evaluation && isEvaluating) {
        setIsEvaluating(false);
      }
    }
  }, [compareData, isEvaluating, rankedIds.length]);

  // Handle sort option changes
  useEffect(() => {
    if (compareData && compareData.experiments && rankedIds.length > 0) {
      const sortedIds = getSortedExperimentIds(sortBy);
      setRankedIds(sortedIds);
      setHasChanges(false); // Reset changes when sorting
    }
  }, [sortBy]);

  const handleReorder = (newOrder: string[]) => {
    setRankedIds(newOrder);

    // Auto-save the human ranking whenever user drags
    const timeSpent = (Date.now() - startTime) / 1000;
    saveRanking.mutate({
      prompt_name: promptName!,
      evaluator_name: 'User', // TODO: Get from auth/settings
      ranked_experiment_ids: newOrder,
      based_on_ai_batch_id: compareData?.ai_evaluation?.batch_id,
      time_spent_seconds: timeSpent,
    });

    // Check if different from AI ranking (for display purposes)
    const aiOrder = compareData?.ai_evaluation?.ranked_experiment_ids || [];
    setHasChanges(JSON.stringify(newOrder) !== JSON.stringify(aiOrder));
  };


  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600" />
          <p className="mt-2 text-gray-600">Loading compare data...</p>
        </div>
      </div>
    );
  }

  if (error || !compareData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Data</h3>
        <p className="text-red-600">
          {error instanceof Error ? error.message : 'Failed to load compare data'}
        </p>
        <Link to="/" className="text-blue-600 hover:underline mt-4 inline-block">
          ← Back to Prompt Library
        </Link>
      </div>
    );
  }

  // Create AI evaluations map
  interface AIEvaluation {
    experiment_id: string;
    ai_rank: number;
    overall_score: number;
    justification: string;
  }

  const aiEvalMap = new Map<string, AIEvaluation>(
    compareData.ai_evaluation?.evaluations?.map((evaluation: any) => [
      evaluation.experiment_id,
      evaluation,
    ]) || []
  );

  // Order experiments by current ranking, with acceptable first, unacceptable last
  // Force new object creation to avoid React Query structural sharing issues
  const allExperiments = rankedIds
    .map((id) => {
      const exp = compareData.experiments.find((e: any) => e.experiment_id === id);
      // Create a new object to break any cached references
      return exp ? { ...exp } : null;
    })
    .filter(Boolean);

  // Separate acceptable and unacceptable
  const acceptable = allExperiments.filter((exp: any) => exp.is_acceptable !== false);
  const unacceptable = allExperiments.filter((exp: any) => exp.is_acceptable === false);

  // Combine: acceptable first, then unacceptable
  const orderedExperiments = [...acceptable, ...unacceptable];

  // Calculate changes from AI
  const changes = rankedIds
    .map((id, idx) => {
      const aiOrder = compareData.ai_evaluation?.ranked_experiment_ids || [];
      const aiIdx = aiOrder.indexOf(id);
      if (aiIdx !== -1 && aiIdx !== idx) {
        const exp = compareData.experiments.find((e: any) => e.experiment_id === id);
        return {
          config_name: exp?.config_name,
          from_rank: aiIdx + 1,
          to_rank: idx + 1,
          direction: idx < aiIdx ? 'up' : 'down',
        };
      }
      return null;
    })
    .filter(Boolean);

  return (
    <div className="w-full px-4">
      {/* Compact Header */}
      <div className="mb-4">
        <Link
          to="/"
          className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1 mb-3"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Link>

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          {/* Title Row */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <h1 className="text-xl font-bold text-gray-900 mb-1">
                {promptName}
              </h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>{compareData?.experiments?.length || 0} configs</span>
                {compareData.ai_evaluation && (
                  <>
                    <span>•</span>
                    <span className="text-green-600 font-medium">✓ AI Ranked</span>
                  </>
                )}
                {isEvaluating && (
                  <>
                    <span>•</span>
                    <span className="text-blue-600 font-medium flex items-center gap-1">
                      <RefreshCw className="h-3 w-3 animate-spin" />
                      Evaluating...
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              {!compareData.ai_evaluation && !isEvaluating && (
                <button
                  onClick={() => setShowAIModal(true)}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 font-medium"
                >
                  Run AI Evaluation
                </button>
              )}
            </div>
          </div>

          {/* Original Prompt */}
          {compareData.original_prompt && (
            <div className="border-t border-gray-200 pt-3 mt-3">
              <div className="text-sm font-medium text-gray-700 mb-2">Original Prompt</div>
              <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm text-gray-700 whitespace-pre-wrap font-mono text-xs max-h-32 overflow-y-auto">
                {compareData.original_prompt}
              </div>
            </div>
          )}

          {/* Recommendation Badge */}
          {compareData.recommendation && (
            <div className="border-t border-gray-200 pt-3 mt-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600">Recommended:</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                  {compareData.recommendation.recommended_config}
                </span>
                <span className="text-xs text-gray-500">
                  Score: {compareData.recommendation.final_score.toFixed(2)}
                </span>
              </div>
            </div>
          )}

          {/* Sort Options */}
          <div className="border-t border-gray-200 pt-3 mt-3">
            <div className="flex items-center gap-2 mb-2">
              <ArrowUpDown className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Sort by:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSortBy('ai')}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  sortBy === 'ai'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                AI Score
              </button>
              <button
                onClick={() => setSortBy('human')}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  sortBy === 'human'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Human Ranking
              </button>
              <button
                onClick={() => setSortBy('time')}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  sortBy === 'time'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Time (Fastest)
              </button>
              <button
                onClick={() => setSortBy('price')}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  sortBy === 'price'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Price (Cheapest)
              </button>
              <button
                onClick={() => setSortBy('tokens')}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  sortBy === 'tokens'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Tokens (Fewest)
              </button>
            </div>
          </div>

          {/* Drag Instructions */}
          <div className="border-t border-gray-200 pt-3 mt-3">
            <p className="text-xs text-gray-600">
              <span className="font-semibold">💡 Tip:</span> Drag cards left/right to rank (Best ← → Worst)
            </p>
          </div>
        </div>
      </div>

      {/* Carousel */}
      {orderedExperiments.length > 0 && (
        <DragCarousel
          experiments={orderedExperiments}
          aiEvaluations={aiEvalMap}
          humanRankedIds={rankedIds}
          onReorder={handleReorder}
          onToggleAcceptability={handleToggleAcceptability}
        />
      )}

      {/* Changes Summary */}
      {hasChanges && changes.length > 0 && (
        <div className="mt-6 bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h3 className="font-semibold text-orange-900 mb-2">
            Changes from AI ranking:
          </h3>
          <ul className="space-y-1 text-sm text-orange-800">
            {changes.map((change: any, idx: number) => (
              <li key={idx}>
                • {change.config_name}: #{change.from_rank} → #{change.to_rank}
                {' '}
                <span className={change.direction === 'up' ? 'text-green-600' : 'text-red-600'}>
                  ({change.direction === 'up' ? '↑' : '↓'} {Math.abs(change.to_rank - change.from_rank)})
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Auto-save status indicator */}
      {saveRanking.isPending && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
          <p className="text-blue-800 text-sm">Saving ranking...</p>
        </div>
      )}
      {saveRanking.isSuccess && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3 text-center">
          <p className="text-green-800 text-sm">✓ Ranking saved</p>
        </div>
      )}

      {/* AI Evaluation Modal */}
      {showAIModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Run AI Evaluation</h2>
              <button
                onClick={() => setShowAIModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              Select a review prompt template and evaluator model. The AI will evaluate all configurations
              and rank them from best to worst.
            </p>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Review Prompt Template
                  </label>
                  <Link
                    to="/review-prompts"
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                  >
                    Manage Templates
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
                <select
                  value={selectedReviewPrompt}
                  onChange={(e) => setSelectedReviewPrompt(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="">Select a template...</option>
                  {reviewPrompts?.map((prompt: any) => (
                    <option key={prompt.prompt_id} value={prompt.prompt_id}>
                      {prompt.name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedReviewPrompt && reviewPrompts && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  {(() => {
                    const selected = reviewPrompts.find((p: any) => p.prompt_id === selectedReviewPrompt);
                    if (!selected) return null;
                    return (
                      <>
                        <p className="text-sm font-medium text-green-900 mb-2">{selected.name}</p>
                        {selected.description && (
                          <p className="text-xs text-green-800 mb-2">{selected.description}</p>
                        )}
                        <div className="flex flex-wrap gap-1.5">
                          <span className="text-xs text-green-700 font-medium">Criteria:</span>
                          {selected.criteria.map((c: string, idx: number) => (
                            <span key={idx} className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                              {c}
                            </span>
                          ))}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-xs text-blue-800">
                  <strong>Evaluator:</strong> GPT-5 with extended thinking (most powerful model)
                </p>
                <p className="text-xs text-blue-800 mt-2">
                  <strong>Process:</strong> All {compareData?.experiments?.length || 0} configurations will be sent in a single comparative evaluation.
                  The AI will rank them best→worst with succinct comments for each.
                </p>
                <p className="text-xs text-blue-800 mt-2">
                  <strong>Time:</strong> ~30-60 seconds • <strong>Cost:</strong> ~$0.10-0.30
                </p>
              </div>
            </div>

            <div className="mt-6 flex gap-3 justify-end">
              <button
                onClick={() => setShowAIModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (selectedReviewPrompt && promptName) {
                    startAIEvaluation.mutate({
                      prompt_name: promptName,
                      review_prompt_id: selectedReviewPrompt,
                      model_evaluator: evaluatorModel,
                      run_id: runId || undefined,
                    });
                  }
                }}
                disabled={!selectedReviewPrompt || startAIEvaluation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {startAIEvaluation.isPending ? 'Starting...' : 'Start Evaluation'}
              </button>
            </div>

            {startAIEvaluation.isError && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800">
                  Error: {startAIEvaluation.error instanceof Error ? startAIEvaluation.error.message : 'Failed to start evaluation'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
