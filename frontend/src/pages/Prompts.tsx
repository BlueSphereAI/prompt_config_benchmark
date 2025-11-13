import { useState, useEffect } from 'react';
import { Plus, X, Save, CheckCircle, Sparkles, ExternalLink } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';
import PromptCard from '../components/PromptCard';
import type { ExperimentRun } from '../types/index';

interface PromptWithRuns {
  name: string;
  runs: ExperimentRun[];
}

export function Prompts() {
  const navigate = useNavigate();
  const [promptsWithRuns, setPromptsWithRuns] = useState<PromptWithRuns[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingPromptName, setEditingPromptName] = useState<string>('');
  const [jsonContent, setJsonContent] = useState<string>('');
  const [jsonError, setJsonError] = useState<string>('');
  const [isCreatingNew, setIsCreatingNew] = useState(false);

  // AI Evaluation state
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiEvalPromptName, setAiEvalPromptName] = useState<string>('');
  const [aiEvalRunId, setAiEvalRunId] = useState<string>('');
  const [evaluatingRunId, setEvaluatingRunId] = useState<string | null>(null);
  const [reviewPrompts, setReviewPrompts] = useState<any[]>([]);
  const [selectedReviewPrompt, setSelectedReviewPrompt] = useState<string>('');
  const [loadingReviewPrompts, setLoadingReviewPrompts] = useState(false);
  const [aiEvalError, setAiEvalError] = useState<string>('');

  // Multi-run session tracking
  const [activeSessionIds, setActiveSessionIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchPromptsWithRuns();
  }, []);

  // Poll active sessions for progress
  useEffect(() => {
    if (activeSessionIds.size === 0) return;

    const pollSessions = async () => {
      for (const sessionId of activeSessionIds) {
        try {
          const progress = await api.getMultiRunSessionProgress(sessionId);

          // If session is completed, remove it from active sessions
          if (progress.status === 'completed' || progress.status === 'failed') {
            setActiveSessionIds(prev => {
              const next = new Set(prev);
              next.delete(sessionId);
              return next;
            });
          }

          // Refresh runs to show latest progress
          await fetchPromptsWithRuns();
        } catch (error) {
          console.error(`Failed to poll session ${sessionId}:`, error);
        }
      }
    };

    // Poll every 2 seconds
    const interval = setInterval(pollSessions, 2000);

    return () => clearInterval(interval);
  }, [activeSessionIds]);

  const fetchPromptsWithRuns = async () => {
    try {
      // Get list of all prompts
      const promptsList = await api.getPromptsList();

      // Fetch runs for each prompt
      const promptsData = await Promise.all(
        promptsList.map(async (promptName: string) => {
          try {
            const runs = await api.getRunsForPrompt(promptName);
            return { name: promptName, runs };
          } catch (error) {
            console.error(`Failed to fetch runs for ${promptName}:`, error);
            return { name: promptName, runs: [] };
          }
        })
      );

      setPromptsWithRuns(promptsData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
      setLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete prompt "${name}" and all its experiments?`)) return;

    try {
      await api.deletePrompt(name);
      await fetchPromptsWithRuns();
    } catch (error) {
      console.error('Failed to delete prompt:', error);
      alert('Failed to delete prompt');
    }
  };

  const handleRunExperiments = async (name: string) => {
    try {
      const data = await api.runAllConfigsForPrompt(name);
      console.log('Started run:', data);

      // Refresh to show the new run
      await fetchPromptsWithRuns();

      // Poll for completion every 5 seconds
      const pollInterval = setInterval(async () => {
        await fetchPromptsWithRuns();
      }, 5000);

      // Stop polling after 5 minutes
      setTimeout(() => clearInterval(pollInterval), 300000);
    } catch (error) {
      console.error('Failed to run configs:', error);
      alert('Failed to start experiments');
    }
  };

  const handleEdit = async (name: string) => {
    try {
      const promptData = await api.getPromptDetail(name);
      setEditingPromptName(promptData.name);
      // Format JSON with 2-space indentation
      setJsonContent(JSON.stringify(promptData.messages, null, 2));
      setJsonError('');
      setIsCreatingNew(false);
      setShowEditor(true);
    } catch (error) {
      console.error('Failed to load prompt:', error);
      alert('Failed to load prompt');
    }
  };

  const handleViewResults = (promptName: string, runId: string) => {
    navigate(`/compare/${promptName}?run_id=${runId}`);
  };

  const handleStartMultiRunSession = (sessionId: string, numRuns: number) => {
    console.log(`Multi-run session started: ${sessionId}, ${numRuns} runs`);

    // Add to active sessions for polling
    setActiveSessionIds(prev => new Set(prev).add(sessionId));

    // Refresh to show new runs
    fetchPromptsWithRuns();
  };

  const handleStartAIEvaluation = async (promptName: string, runId: string) => {
    setAiEvalPromptName(promptName);
    setAiEvalRunId(runId);
    setSelectedReviewPrompt('');
    setAiEvalError('');
    setShowAIModal(true);

    // Fetch review prompts
    setLoadingReviewPrompts(true);
    try {
      const prompts = await api.getReviewPrompts(true);
      setReviewPrompts(prompts);
    } catch (error) {
      console.error('Failed to load review prompts:', error);
      setAiEvalError('Failed to load review prompts');
    } finally {
      setLoadingReviewPrompts(false);
    }
  };

  const handleStartEvaluation = async () => {
    if (!selectedReviewPrompt || !aiEvalPromptName || !aiEvalRunId) {
      setAiEvalError('Please select a review prompt template');
      return;
    }

    setAiEvalError('');
    setShowAIModal(false);
    setEvaluatingRunId(aiEvalRunId);

    try {
      await api.startBatchEvaluation({
        prompt_name: aiEvalPromptName,
        review_prompt_id: selectedReviewPrompt,
        model_evaluator: 'gpt-5',
        run_id: aiEvalRunId,
      });

      // Poll for completion every 5 seconds
      const pollInterval = setInterval(async () => {
        await fetchPromptsWithRuns();

        // Check if the run status has changed
        const currentPrompt = promptsWithRuns.find(p => p.name === aiEvalPromptName);
        const currentRun = currentPrompt?.runs.find(r => r.run_id === aiEvalRunId);

        if (currentRun && currentRun.status === 'analysis_completed') {
          clearInterval(pollInterval);
          setEvaluatingRunId(null);
        }
      }, 5000);

      // Stop polling after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setEvaluatingRunId(null);
      }, 300000);
    } catch (error) {
      console.error('Failed to start AI evaluation:', error);
      setEvaluatingRunId(null);
      alert('Failed to start AI evaluation: ' + (error as Error).message);
    }
  };

  const handleCreateNew = () => {
    setEditingPromptName('');
    // Default prompt structure
    const defaultMessages = [
      { role: 'user', content: '' }
    ];
    setJsonContent(JSON.stringify(defaultMessages, null, 2));
    setJsonError('');
    setIsCreatingNew(true);
    setShowEditor(true);
  };

  const validateJSON = (json: string): { valid: boolean; messages?: any[]; error?: string } => {
    if (!json.trim()) {
      return { valid: false, error: 'JSON cannot be empty' };
    }

    try {
      const parsed = JSON.parse(json);

      // Validate it's an array
      if (!Array.isArray(parsed)) {
        return { valid: false, error: 'JSON must be an array of message objects' };
      }

      // Validate each message has required fields
      for (let i = 0; i < parsed.length; i++) {
        const msg = parsed[i];
        if (!msg.role || !msg.content) {
          return { valid: false, error: `Message at index ${i} must have 'role' and 'content' fields` };
        }
        if (!['system', 'user', 'assistant'].includes(msg.role)) {
          return { valid: false, error: `Message at index ${i} has invalid role: ${msg.role}. Must be 'system', 'user', or 'assistant'` };
        }
      }

      return { valid: true, messages: parsed };
    } catch (e: any) {
      return { valid: false, error: `Invalid JSON: ${e.message}` };
    }
  };

  const handleValidate = () => {
    const result = validateJSON(jsonContent);
    if (result.valid) {
      setJsonError('');
    } else {
      setJsonError(result.error || 'Unknown error');
    }
  };

  const handleSavePrompt = async () => {
    if (!editingPromptName.trim()) {
      alert('Please enter a prompt name');
      return;
    }

    const result = validateJSON(jsonContent);
    if (!result.valid) {
      setJsonError(result.error || 'Invalid JSON');
      return;
    }

    try {
      await api.savePrompt(editingPromptName, result.messages!);
      setShowEditor(false);
      setEditingPromptName('');
      setJsonContent('');
      setJsonError('');
      await fetchPromptsWithRuns();
    } catch (error) {
      console.error('Failed to save prompt:', error);
      alert('Failed to save prompt');
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonContent(value);

    // Live validation as user types
    if (value.trim()) {
      const result = validateJSON(value);
      if (!result.valid) {
        setJsonError(result.error || '');
      } else {
        setJsonError('');
      }
    } else {
      setJsonError('');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading prompts...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Prompt Library</h1>
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Prompt
          </button>
        </div>
      </div>

      {/* Prompts Grid */}
      {promptsWithRuns.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No prompts found</p>
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Your First Prompt
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {promptsWithRuns.map((prompt) => (
            <PromptCard
              key={prompt.name}
              promptName={prompt.name}
              runs={prompt.runs}
              onEdit={handleEdit}
              onDeletePrompt={handleDelete}
              onRunExperiments={handleRunExperiments}
              onViewResults={handleViewResults}
              onRunsUpdated={fetchPromptsWithRuns}
              onStartAIEvaluation={handleStartAIEvaluation}
              evaluatingRunId={evaluatingRunId}
              onStartMultiRunSession={handleStartMultiRunSession}
            />
          ))}
        </div>
      )}

      {/* JSON Editor Modal */}
      {showEditor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">
                {isCreatingNew ? 'New Prompt' : 'Edit Prompt'}
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={handleSavePrompt}
                  className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Save
                </button>
                <button
                  onClick={() => {
                    setShowEditor(false);
                    setEditingPromptName('');
                    setJsonContent('');
                    setJsonError('');
                  }}
                  className="p-2 text-gray-500 hover:text-gray-700 rounded hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                {/* Prompt Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Prompt Name
                  </label>
                  <input
                    type="text"
                    value={editingPromptName}
                    onChange={(e) => setEditingPromptName(e.target.value)}
                    disabled={!isCreatingNew}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="my-prompt-name"
                  />
                  {!isCreatingNew && (
                    <p className="mt-1 text-xs text-gray-500">Prompt name cannot be changed when editing</p>
                  )}
                </div>

                {/* JSON Editor */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Messages (JSON)
                    </label>
                    <button
                      onClick={handleValidate}
                      className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
                    >
                      <CheckCircle className="w-3 h-3" />
                      Validate
                    </button>
                  </div>
                  <textarea
                    value={jsonContent}
                    onChange={(e) => handleJsonChange(e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg font-mono text-sm focus:ring-2 focus:border-transparent ${
                      jsonError
                        ? 'border-red-300 focus:ring-red-500'
                        : 'border-gray-300 focus:ring-blue-500'
                    }`}
                    rows={20}
                    placeholder={`[\n  {\n    "role": "system",\n    "content": "You are a helpful assistant."\n  },\n  {\n    "role": "user",\n    "content": "Hello!"\n  }\n]`}
                    spellCheck={false}
                  />
                  {jsonError && (
                    <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800 flex items-start gap-2">
                        <span className="font-semibold">✗</span>
                        <span className="flex-1">{jsonError}</span>
                      </p>
                    </div>
                  )}
                  {!jsonError && jsonContent.trim() && (
                    <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-800 flex items-start gap-2">
                        <span className="font-semibold">✓</span>
                        <span>Valid JSON</span>
                      </p>
                    </div>
                  )}
                </div>

                {/* Help Text */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-900 mb-2">Format Guide</h4>
                  <ul className="text-xs text-blue-800 space-y-1">
                    <li>• Must be a JSON array of message objects</li>
                    <li>• Each message must have "role" (system/user/assistant) and "content" fields</li>
                    <li>• Example: <code className="bg-blue-100 px-1 rounded">{`[{"role": "user", "content": "Hello"}]`}</code></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Evaluation Modal */}
      {showAIModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-lg shadow-2xl max-w-lg w-full transform transition-all">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Sparkles className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Run AI Evaluation</h2>
                  <p className="text-xs text-gray-500 mt-0.5">{aiEvalPromptName}</p>
                </div>
              </div>
              <button
                onClick={() => setShowAIModal(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-600 leading-relaxed">
                Select a review prompt template and the AI will evaluate all configurations in this run,
                ranking them from best to worst with detailed comments.
              </p>

              {/* Review Prompt Selection */}
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
                  disabled={loadingReviewPrompts}
                  className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
                >
                  <option value="">
                    {loadingReviewPrompts ? 'Loading templates...' : 'Select a template...'}
                  </option>
                  {reviewPrompts.map((prompt) => (
                    <option key={prompt.prompt_id} value={prompt.prompt_id}>
                      {prompt.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Selected Template Details */}
              {selectedReviewPrompt && reviewPrompts.length > 0 && (
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
                  {(() => {
                    const selected = reviewPrompts.find((p) => p.prompt_id === selectedReviewPrompt);
                    if (!selected) return null;
                    return (
                      <>
                        <p className="text-sm font-semibold text-green-900 mb-2">{selected.name}</p>
                        {selected.description && (
                          <p className="text-xs text-green-800 mb-3 leading-relaxed">{selected.description}</p>
                        )}
                        <div className="flex flex-wrap gap-1.5">
                          <span className="text-xs text-green-700 font-medium">Criteria:</span>
                          {selected.criteria.map((c: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium"
                            >
                              {c}
                            </span>
                          ))}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}

              {/* Info Box */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 space-y-2">
                <div className="flex items-start gap-2">
                  <div className="text-blue-600 mt-0.5">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div className="flex-1 space-y-2 text-xs text-blue-800">
                    <p>
                      <strong className="font-semibold">Evaluator:</strong> GPT-5 with extended thinking (most powerful model)
                    </p>
                    <p>
                      <strong className="font-semibold">Process:</strong> All configurations will be comparatively evaluated and ranked best→worst with succinct comments.
                    </p>
                    <p>
                      <strong className="font-semibold">Estimated Time:</strong> 30-60 seconds
                      {' • '}
                      <strong className="font-semibold">Cost:</strong> ~$0.10-0.30
                    </p>
                  </div>
                </div>
              </div>

              {/* Error Display */}
              {aiEvalError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800 flex items-start gap-2">
                    <span className="font-semibold">✗</span>
                    <span className="flex-1">{aiEvalError}</span>
                  </p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3 justify-end rounded-b-lg">
              <button
                onClick={() => setShowAIModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartEvaluation}
                disabled={!selectedReviewPrompt || loadingReviewPrompts}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all shadow-sm hover:shadow flex items-center gap-2"
              >
                <Sparkles className="h-4 w-4" />
                Start Evaluation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
