import { useState, useEffect } from 'react';
import { Plus, X, Save, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
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

  useEffect(() => {
    fetchPromptsWithRuns();
  }, []);

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
    </div>
  );
}
