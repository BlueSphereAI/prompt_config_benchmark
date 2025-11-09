import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, RefreshCw, X } from 'lucide-react';
import { api } from '../api/client';
import { DragCarousel } from '../components/DragCarousel';
import { RecommendationBanner } from '../components/RecommendationBanner';

export default function Compare() {
  const { promptName } = useParams<{ promptName: string }>();
  const queryClient = useQueryClient();
  const [rankedIds, setRankedIds] = useState<string[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [startTime] = useState(Date.now());
  const [showAIModal, setShowAIModal] = useState(false);
  const [selectedReviewPrompt, setSelectedReviewPrompt] = useState<string>('');
  const [evaluatorModel] = useState('gpt-5'); // Always use GPT-5 with reasoning
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Fetch all compare data
  const { data: compareData, isLoading, error } = useQuery({
    queryKey: ['compare', promptName],
    queryFn: () => api.getCompareData(promptName!),
    enabled: !!promptName,
  });

  // Fetch review prompts for AI evaluation
  const { data: reviewPrompts } = useQuery({
    queryKey: ['review-prompts'],
    queryFn: () => api.getReviewPrompts(true),
  });

  const startAIEvaluation = useMutation({
    mutationFn: (params: { prompt_name: string; review_prompt_id: string; model_evaluator: string }) => {
      console.log('Starting AI evaluation with params:', params);
      setIsEvaluating(true);
      return api.startBatchEvaluation(params);
    },
    onSuccess: (data) => {
      console.log('AI evaluation started successfully:', data);
      setShowAIModal(false);
      // Poll for completion every 5 seconds for up to 2 minutes
      const pollInterval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['compare', promptName] });
      }, 5000);

      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setIsEvaluating(false);
        queryClient.invalidateQueries({ queryKey: ['compare', promptName] });
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

  useEffect(() => {
    if (compareData && compareData.experiments) {
      // Initialize with AI ranking or default order
      const initialOrder = compareData.ai_evaluation?.ranked_experiment_ids
        || compareData.experiments.map((exp: any) => exp.experiment_id);

      setRankedIds(initialOrder);

      // Stop evaluating spinner if AI evaluation is complete
      if (compareData.ai_evaluation && isEvaluating) {
        setIsEvaluating(false);
      }
    }
  }, [compareData, isEvaluating]);

  const handleReorder = (newOrder: string[]) => {
    setRankedIds(newOrder);

    // Check if different from AI ranking
    const aiOrder = compareData?.ai_evaluation?.ranked_experiment_ids || [];
    setHasChanges(JSON.stringify(newOrder) !== JSON.stringify(aiOrder));
  };

  const handleSave = () => {
    const timeSpent = (Date.now() - startTime) / 1000;

    saveRanking.mutate({
      prompt_name: promptName!,
      evaluator_name: 'User', // TODO: Get from auth/settings
      ranked_experiment_ids: rankedIds,
      based_on_ai_batch_id: compareData?.ai_evaluation?.batch_id,
      time_spent_seconds: timeSpent,
    });
  };

  const handleReset = () => {
    if (compareData?.ai_evaluation?.ranked_experiment_ids) {
      setRankedIds(compareData.ai_evaluation.ranked_experiment_ids);
      setHasChanges(false);
    }
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

  // Order experiments by current ranking
  const orderedExperiments = rankedIds
    .map((id) => compareData.experiments.find((exp: any) => exp.experiment_id === id))
    .filter(Boolean);

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
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/"
          className="text-blue-600 hover:underline inline-flex items-center gap-2 mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Prompt Library
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">
          Compare & Rank: {promptName}
        </h1>
      </div>

      {/* AI Evaluation Status */}
      {isEvaluating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
            <div>
              <h3 className="font-semibold text-blue-800">🤖 AI Evaluation Running...</h3>
              <p className="text-sm text-blue-700">
                GPT-5 is comparing all {compareData?.experiments?.length || 0} configurations. This takes ~30-60 seconds.
              </p>
            </div>
          </div>
        </div>
      )}

      {!isEvaluating && compareData.ai_evaluation ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-green-800">✅ AI Evaluation Complete</h3>
              <p className="text-sm text-green-700">
                Model: {compareData.ai_evaluation.model_evaluator}
              </p>
            </div>
            <button
              className="text-sm text-green-700 hover:text-green-900 underline"
              onClick={() => {
                // TODO: Show AI evaluation details modal
                alert('AI evaluation details coming soon!');
              }}
            >
              View AI Reasoning
            </button>
          </div>
        </div>
      ) : !isEvaluating && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-yellow-800">⚠️ No AI Evaluation Yet</h3>
          <p className="text-sm text-yellow-700 mb-3">
            Run AI evaluation first to get automated rankings and recommendations.
          </p>
          <button
            className="bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 text-sm"
            onClick={() => setShowAIModal(true)}
          >
            Run AI Evaluation
          </button>
        </div>
      )}

      {/* Recommendation */}
      {compareData.recommendation && (
        <RecommendationBanner recommendation={compareData.recommendation} />
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <span className="font-semibold">💡 Drag cards left/right to rank</span>
          {' • '}
          Best (left) → Worst (right)
        </p>
      </div>

      {/* Carousel */}
      {orderedExperiments.length > 0 && (
        <DragCarousel
          experiments={orderedExperiments}
          aiEvaluations={aiEvalMap}
          onReorder={handleReorder}
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

      {/* Actions */}
      <div className="mt-6 flex gap-4 justify-center pb-8">
        {compareData.ai_evaluation && (
          <button
            onClick={handleReset}
            disabled={!hasChanges}
            className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset to AI Order
          </button>
        )}
        <button
          onClick={handleSave}
          disabled={!hasChanges || saveRanking.isPending}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saveRanking.isPending ? 'Saving...' : 'Save My Ranking'}
        </button>
      </div>

      {saveRanking.isSuccess && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <p className="text-green-800 font-medium">✓ Ranking saved successfully!</p>
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Review Prompt Template
                </label>
                <select
                  value={selectedReviewPrompt}
                  onChange={(e) => setSelectedReviewPrompt(e.target.value)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="">Select a template...</option>
                  {reviewPrompts?.map((prompt: any) => (
                    <option key={prompt.prompt_id} value={prompt.prompt_id}>
                      {prompt.name} - {prompt.description}
                    </option>
                  ))}
                </select>
              </div>

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
