import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Play, FileText, X, Save, Eye, BarChart, Loader, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

interface Prompt {
  name: string;
  messages: any[];
}

interface PromptMetadata {
  name: string;
  status: 'not_run' | 'results_ready' | 'ai_evaluated' | 'user_ranked';
  recommended_config: string | null;
  last_run_date: string | null;
  total_cost: number | null;
  num_configs: number;
  has_ai_evaluation: boolean;
  has_user_ranking: boolean;
  is_running: boolean;
}

export function Prompts() {
  const navigate = useNavigate();
  const [promptsMetadata, setPromptsMetadata] = useState<PromptMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [editingPromptMetadata, setEditingPromptMetadata] = useState<PromptMetadata | null>(null);
  const [viewMode, setViewMode] = useState<'preview' | 'edit'>('preview');

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      const data = await api.getPromptsMetadata();
      setPromptsMetadata(data.prompts);
    } catch (error) {
      console.error('Failed to fetch prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete prompt "${name}"?`)) return;

    try {
      await fetch(`http://localhost:8000/api/prompts/delete/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      await fetchPrompts();
    } catch (error) {
      console.error('Failed to delete prompt:', error);
      alert('Failed to delete prompt');
    }
  };

  const handleRunAllConfigs = async (name: string) => {
    try {
      await fetch(
        `http://localhost:8000/api/experiments/run-all-configs?prompt_name=${encodeURIComponent(name)}`,
        { method: 'POST' }
      );

      // Poll for results every 10 seconds
      const pollInterval = setInterval(async () => {
        await fetchPrompts();

        // Check if experiments have completed (no longer running and has results)
        const updatedData = await api.getPromptsMetadata();
        const updatedPrompt = updatedData.prompts.find((p: any) => p.name === name);
        if (updatedPrompt && !updatedPrompt.is_running && updatedPrompt.status !== 'not_run') {
          clearInterval(pollInterval);
          navigate(`/compare/${name}`);
        }
      }, 10000);

      // Stop polling after 5 minutes
      setTimeout(() => clearInterval(pollInterval), 300000);
    } catch (error) {
      console.error('Failed to run configs:', error);
      alert('Failed to start experiments');
    }
  };

  const handleDeleteResults = async (promptName: string) => {
    const prompt = promptsMetadata.find(p => p.name === promptName);
    if (!prompt || prompt.num_configs === 0) return;

    if (!confirm(`Delete all ${prompt.num_configs} experiment results for "${promptName}"?\n\nThis will also delete AI evaluations and rankings.`)) {
      return;
    }

    try {
      await api.deleteExperimentsByPrompt(promptName);
      await fetchPrompts();
      alert('Experiment results deleted successfully');
    } catch (error) {
      console.error('Failed to delete results:', error);
      alert('Failed to delete experiment results');
    }
  };

  const handleEdit = async (promptName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/prompts/detail/${encodeURIComponent(promptName)}`);
      const prompt = await response.json();
      const metadata = promptsMetadata.find(p => p.name === promptName);
      setEditingPrompt(prompt);
      setEditingPromptMetadata(metadata || null);
      setViewMode('edit');
      setShowEditor(true);
    } catch (error) {
      console.error('Failed to fetch prompt:', error);
      alert('Failed to load prompt');
    }
  };

  const handleCreate = () => {
    setEditingPrompt(null);
    setViewMode('edit');
    setShowEditor(true);
  };

  const handleView = async (promptName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/prompts/detail/${encodeURIComponent(promptName)}`);
      const prompt = await response.json();
      setEditingPrompt(prompt);
      setViewMode('preview');
      setShowEditor(true);
    } catch (error) {
      console.error('Failed to fetch prompt:', error);
      alert('Failed to load prompt');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading prompts...</div>
      </div>
    );
  }

  const getStatusBadge = (status: PromptMetadata['status']) => {
    const badges = {
      not_run: { label: 'Not Run', className: 'bg-gray-100 text-gray-700' },
      results_ready: { label: 'Results Ready', className: 'bg-blue-100 text-blue-700' },
      ai_evaluated: { label: 'AI Evaluated', className: 'bg-purple-100 text-purple-700' },
      user_ranked: { label: 'User Ranked', className: 'bg-green-100 text-green-700' },
    };
    return badges[status];
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatCost = (cost: number | null) => {
    if (cost === null) return '—';
    return `$${cost.toFixed(4)}`;
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Prompt Library</h1>
          <p className="text-gray-600 mt-1">Manage prompts and compare LLM configurations</p>
        </div>
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus size={20} />
          New Prompt
        </button>
      </div>

      {/* Prompts Table */}
      {promptsMetadata.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No prompts yet</h3>
          <p className="text-gray-500 mb-4">Create your first prompt to get started</p>
          <button
            onClick={handleCreate}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Create Prompt
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Prompt Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Recommended Config
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Configs Tested
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Run
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Cost
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {promptsMetadata.map((prompt) => {
                const statusBadge = getStatusBadge(prompt.status);
                const isRunning = prompt.is_running;
                return (
                  <tr key={prompt.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="text-sm font-medium text-gray-900 break-words">{prompt.name}</div>
                        {isRunning && (
                          <Loader className="h-4 w-4 text-blue-600 animate-spin flex-shrink-0" />
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {isRunning ? (
                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-700 whitespace-nowrap">
                          Running...
                        </span>
                      ) : (
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full whitespace-nowrap ${statusBadge.className}`}>
                          {statusBadge.label}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 break-words">
                        {prompt.recommended_config || '—'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {prompt.num_configs > 0 ? prompt.num_configs : '—'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 whitespace-nowrap">
                        {formatDate(prompt.last_run_date)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 whitespace-nowrap">
                        {formatCost(prompt.total_cost)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex gap-1 justify-end">
                        {prompt.status !== 'not_run' && (
                          <button
                            onClick={() => navigate(`/compare/${prompt.name}`)}
                            className="p-2 text-purple-600 hover:bg-purple-50 rounded"
                            title="View Results"
                          >
                            <BarChart size={18} />
                          </button>
                        )}
                        <button
                          onClick={() => handleView(prompt.name)}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                          title="View JSON"
                        >
                          <Eye size={18} />
                        </button>
                        <button
                          onClick={() => handleRunAllConfigs(prompt.name)}
                          disabled={isRunning}
                          className={`p-2 rounded ${
                            isRunning
                              ? 'text-gray-400 cursor-not-allowed'
                              : 'text-green-600 hover:bg-green-50'
                          }`}
                          title={isRunning ? 'Running...' : 'Run all configs'}
                        >
                          <Play size={18} />
                        </button>
                        {prompt.status !== 'not_run' && (
                          <button
                            onClick={() => handleDeleteResults(prompt.name)}
                            className="p-2 text-orange-600 hover:bg-orange-50 rounded"
                            title="Delete Results"
                          >
                            <XCircle size={18} />
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(prompt.name)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(prompt.name)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Full-Screen JSON Editor/Viewer */}
      {showEditor && (
        <PromptEditorModal
          prompt={editingPrompt}
          promptMetadata={editingPromptMetadata}
          mode={viewMode}
          onClose={() => {
            setShowEditor(false);
            setEditingPrompt(null);
            setEditingPromptMetadata(null);
          }}
          onSave={async (shouldRerun: boolean) => {
            await fetchPrompts();
            setShowEditor(false);
            setEditingPrompt(null);
            setEditingPromptMetadata(null);
            if (shouldRerun && editingPrompt) {
              handleRunAllConfigs(editingPrompt.name);
            }
          }}
          onDeleteResults={handleDeleteResults}
        />
      )}
    </div>
  );
}

// Full-screen JSON editor modal
function PromptEditorModal({
  prompt,
  promptMetadata,
  mode: initialMode,
  onClose,
  onSave,
  onDeleteResults,
}: {
  prompt: Prompt | null;
  promptMetadata: PromptMetadata | null;
  mode: 'preview' | 'edit';
  onClose: () => void;
  onSave: (shouldRerun: boolean) => void;
  onDeleteResults: (promptName: string) => void;
}) {
  const [mode, setMode] = useState<'preview' | 'edit'>(initialMode);
  const [jsonText, setJsonText] = useState(() => {
    if (prompt) {
      return JSON.stringify(prompt.messages, null, 2);
    }
    return JSON.stringify(
      [
        {
          role: 'system',
          content: 'You are a helpful assistant.',
        },
        {
          role: 'user',
          content: 'Hello!',
        },
      ],
      null,
      2
    );
  });
  const [name, setName] = useState(prompt?.name || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRerunDialog, setShowRerunDialog] = useState(false);

  const validateJSON = () => {
    try {
      const parsed = JSON.parse(jsonText);
      if (!Array.isArray(parsed)) {
        throw new Error('JSON must be an array');
      }
      setError(null);
      return parsed;
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Invalid JSON';
      setError(errorMsg);
      return null;
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    const messages = validateJSON();
    if (!messages) return;

    // Check if this is an edit with existing results
    if (prompt && promptMetadata && promptMetadata.status !== 'not_run') {
      setShowRerunDialog(true);
      return;
    }

    await performSave(false);
  };

  const performSave = async (shouldRerun: boolean) => {
    setSaving(true);
    setError(null);

    try {
      const url = prompt
        ? `http://localhost:8000/api/prompts/update/${encodeURIComponent(prompt.name)}`
        : 'http://localhost:8000/api/prompts/create';

      const method = prompt ? 'PUT' : 'POST';

      const params = new URLSearchParams();
      params.append('name', name);

      const messages = validateJSON();
      if (!messages) return;

      const response = await fetch(`${url}?${params.toString()}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save prompt');
      }

      onSave(shouldRerun);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save prompt');
    } finally {
      setSaving(false);
    }
  };

  // Format JSON
  const handleFormat = () => {
    try {
      const parsed = JSON.parse(jsonText);
      setJsonText(JSON.stringify(parsed, null, 2));
      setError(null);
    } catch (e) {
      setError('Cannot format invalid JSON');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-2xl w-full h-full max-w-7xl max-h-[95vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold">
              {prompt ? (mode === 'preview' ? 'View Prompt' : 'Edit Prompt') : 'Create Prompt'}
            </h2>
            {prompt && (
              <div className="flex gap-2">
                <button
                  onClick={() => setMode('preview')}
                  className={`px-3 py-1 rounded text-sm ${
                    mode === 'preview'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <Eye size={16} className="inline mr-1" />
                  Preview
                </button>
                <button
                  onClick={() => setMode('edit')}
                  className={`px-3 py-1 rounded text-sm ${
                    mode === 'edit'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <Edit2 size={16} className="inline mr-1" />
                  Edit
                </button>
              </div>
            )}
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded">
            <X size={24} />
          </button>
        </div>

        {/* Name Field */}
        {mode === 'edit' && (
          <div className="p-6 border-b bg-gray-50">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Prompt Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={!!prompt}
              className="w-full border rounded px-3 py-2 disabled:bg-gray-100 disabled:text-gray-600"
              placeholder="my-prompt-name"
            />
          </div>
        )}

        {/* JSON Editor/Preview */}
        <div className="flex-1 p-6 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-semibold text-gray-700">
              JSON Array
              {mode === 'preview' && <span className="ml-2 text-gray-500">(read-only)</span>}
            </div>
            {mode === 'edit' && (
              <div className="flex gap-2">
                <button
                  onClick={handleFormat}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Format JSON
                </button>
                <button
                  onClick={validateJSON}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 hover:bg-blue-200 rounded"
                >
                  Validate
                </button>
              </div>
            )}
          </div>

          <textarea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            readOnly={mode === 'preview'}
            className={`flex-1 w-full font-mono text-sm border rounded p-4 ${
              mode === 'preview' ? 'bg-gray-50 text-gray-700' : 'bg-white'
            } focus:outline-none focus:ring-2 focus:ring-blue-500`}
            style={{ resize: 'none' }}
            spellCheck={false}
          />

          {error && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        {mode === 'edit' && (
          <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
            <button
              onClick={onClose}
              disabled={saving}
              className="px-6 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Save size={18} />
              {saving ? 'Saving...' : 'Save Prompt'}
            </button>
          </div>
        )}
      </div>

      {/* Rerun Dialog */}
      {showRerunDialog && promptMetadata && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg shadow-2xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold mb-4">Existing Results Found</h3>
            <p className="text-sm text-gray-700 mb-4">
              This prompt has {promptMetadata.num_configs} existing experiment results.
            </p>
            <p className="text-sm text-gray-700 mb-6">
              What would you like to do?
            </p>
            <div className="space-y-3">
              <button
                onClick={async () => {
                  setShowRerunDialog(false);
                  await performSave(false);
                }}
                className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-left"
              >
                <div className="font-medium">Keep existing results</div>
                <div className="text-xs text-gray-600">Save changes without deleting or rerunning</div>
              </button>
              <button
                onClick={async () => {
                  setShowRerunDialog(false);
                  if (prompt) {
                    await onDeleteResults(prompt.name);
                  }
                  await performSave(false);
                }}
                className="w-full px-4 py-2 bg-orange-100 hover:bg-orange-200 text-orange-900 rounded-lg text-left"
              >
                <div className="font-medium">Delete existing results</div>
                <div className="text-xs text-orange-700">Remove all results, save changes, don't rerun</div>
              </button>
              <button
                onClick={async () => {
                  setShowRerunDialog(false);
                  if (prompt) {
                    await onDeleteResults(prompt.name);
                  }
                  await performSave(true);
                }}
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-left"
              >
                <div className="font-medium">Delete & rerun all configs</div>
                <div className="text-xs text-green-100">Remove results, save changes, and start new run</div>
              </button>
              <button
                onClick={() => setShowRerunDialog(false)}
                className="w-full px-4 py-2 border border-gray-300 hover:bg-gray-50 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
