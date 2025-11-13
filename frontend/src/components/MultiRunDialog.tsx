import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { api } from '../api/client';

interface MultiRunDialogProps {
  promptName: string;
  isOpen: boolean;
  onClose: () => void;
  onStartSession: (sessionId: string, numRuns: number) => void;
}

interface ReviewPrompt {
  prompt_id: string;
  name: string;
  description: string;
}

export default function MultiRunDialog({
  promptName,
  isOpen,
  onClose,
  onStartSession
}: MultiRunDialogProps) {
  const [numRuns, setNumRuns] = useState(1);
  const [reviewPromptId, setReviewPromptId] = useState('');
  const [reviewPrompts, setReviewPrompts] = useState<ReviewPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load review prompts when dialog opens
  useEffect(() => {
    if (isOpen) {
      loadReviewPrompts();
    }
  }, [isOpen]);

  const loadReviewPrompts = async () => {
    try {
      const prompts = await api.getReviewPrompts(true); // active_only=true
      setReviewPrompts(prompts);
      // Auto-select first prompt if available
      if (prompts.length > 0) {
        setReviewPromptId(prompts[0].prompt_id);
      }
    } catch (err) {
      console.error('Failed to load review prompts:', err);
      setError('Failed to load review prompts. Please try again.');
    }
  };

  const handleStart = async () => {
    if (!reviewPromptId) {
      setError('Please select a review prompt');
      return;
    }

    if (numRuns < 1 || numRuns > 10) {
      setError('Number of runs must be between 1 and 10');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.runMultiRunSession(promptName, numRuns, reviewPromptId);
      onStartSession(response.session_id, numRuns);
      onClose();
    } catch (err: any) {
      console.error('Failed to start multi-run session:', err);
      setError(err.message || 'Failed to start runs. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Run Multiple Experiments
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Prompt Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prompt
            </label>
            <div className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded border border-gray-200">
              {promptName}
            </div>
          </div>

          {/* Number of Runs */}
          <div>
            <label htmlFor="numRuns" className="block text-sm font-medium text-gray-700 mb-1">
              Number of Runs
            </label>
            <input
              id="numRuns"
              type="number"
              min="1"
              max="10"
              value={numRuns}
              onChange={(e) => setNumRuns(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="mt-1 text-xs text-gray-500">
              Min: 1, Max: 10
            </p>
          </div>

          {/* Review Prompt Selection */}
          <div>
            <label htmlFor="reviewPrompt" className="block text-sm font-medium text-gray-700 mb-1">
              Review Prompt Template
            </label>
            <select
              id="reviewPrompt"
              value={reviewPromptId}
              onChange={(e) => setReviewPromptId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select a review prompt...</option>
              {reviewPrompts.map((prompt) => (
                <option key={prompt.prompt_id} value={prompt.prompt_id}>
                  {prompt.name}
                </option>
              ))}
            </select>
            {reviewPromptId && (
              <p className="mt-1 text-xs text-gray-500">
                {reviewPrompts.find(p => p.prompt_id === reviewPromptId)?.description}
              </p>
            )}
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Runs will execute sequentially. Each run will:
            </p>
            <ol className="mt-2 text-sm text-blue-700 list-decimal list-inside space-y-1">
              <li>Run all active configs</li>
              <li>Perform AI ranking</li>
              <li>Proceed to the next run</li>
            </ol>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            disabled={isLoading || !reviewPromptId}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Starting...' : 'Start Runs'}
          </button>
        </div>
      </div>
    </div>
  );
}
