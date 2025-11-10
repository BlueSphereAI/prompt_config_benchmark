import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { X, Plus, Trash2, Code } from 'lucide-react';
import { api } from '../api/client';
import { TemplateValidator } from './TemplateValidator';

interface ReviewPromptEditorProps {
  promptId: string | null; // null for create, string for edit
  onClose: () => void;
  onSuccess: () => void;
}

const DEFAULT_TEMPLATE = `You are an expert evaluator ranking different LLM configurations.

ORIGINAL PROMPT:
{original_prompt}

You will evaluate {num_configs} different configurations. Each produced a response to the prompt above.

{all_responses}

RANK these configurations from BEST to WORST based on:
1. RELEVANCE: How well does it address the original prompt?
2. ACCURACY: Is the information correct and factual?
3. CLARITY: Is the response clear and easy to understand?

Provide your evaluation in the following JSON format:
{{
  "rankings": [
    {{
      "config_name": "<name of best config>",
      "rank": 1,
      "overall_score": <score 1-10>,
      "comment": "<1-2 sentence succinct explanation>",
      "criteria_scores": {{
        "relevance": <1-10>,
        "accuracy": <1-10>,
        "clarity": <1-10>
      }}
    }},
    ... (continue for all configs, ordered best to worst)
  ]
}}`;

const DEFAULT_SYSTEM_PROMPT = `You are an objective evaluator of language model outputs. Provide balanced, comparative assessments. When ranking, consider the relative quality of responses - the best response should score highest, even if none are perfect.`;

export function ReviewPromptEditor({ promptId, onClose, onSuccess }: ReviewPromptEditorProps) {
  const isEditMode = promptId !== null;

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [template, setTemplate] = useState(DEFAULT_TEMPLATE);
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);
  const [criteria, setCriteria] = useState<string[]>(['relevance', 'accuracy', 'clarity']);
  const [defaultModel, setDefaultModel] = useState('gpt-5');
  const [newCriterion, setNewCriterion] = useState('');
  const [showVariableHelp, setShowVariableHelp] = useState(false);

  // Fetch existing prompt if editing
  const { data: existingPrompt } = useQuery({
    queryKey: ['review-prompt', promptId],
    queryFn: () => api.getReviewPrompt(promptId!),
    enabled: isEditMode,
  });

  // Populate form when editing
  useEffect(() => {
    if (existingPrompt) {
      setName(existingPrompt.name);
      setDescription(existingPrompt.description || '');
      setTemplate(existingPrompt.template);
      setSystemPrompt(existingPrompt.system_prompt || DEFAULT_SYSTEM_PROMPT);
      setCriteria(existingPrompt.criteria);
      setDefaultModel(existingPrompt.default_model);
    }
  }, [existingPrompt]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (params: any) => api.createReviewPrompt(params),
    onSuccess: () => {
      onSuccess();
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, params }: { id: string; params: any }) =>
      api.updateReviewPrompt(id, params),
    onSuccess: () => {
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const params = {
      name,
      description,
      template,
      system_prompt: systemPrompt,
      criteria,
      default_model: defaultModel,
    };

    if (isEditMode) {
      updateMutation.mutate({ id: promptId, params });
    } else {
      createMutation.mutate({
        ...params,
        created_by: 'user', // TODO: Get from auth
      });
    }
  };

  const addCriterion = () => {
    if (newCriterion && !criteria.includes(newCriterion)) {
      setCriteria([...criteria, newCriterion]);
      setNewCriterion('');
    }
  };

  const removeCriterion = (index: number) => {
    setCriteria(criteria.filter((_, i) => i !== index));
  };

  const insertVariable = (variable: string) => {
    const textarea = document.getElementById('template-textarea') as HTMLTextAreaElement;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newTemplate = template.substring(0, start) + variable + template.substring(end);
      setTemplate(newTemplate);
      // Set cursor after inserted variable
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + variable.length, start + variable.length);
      }, 0);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;
  const error = createMutation.error || updateMutation.error;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            {isEditMode ? 'Edit Review Prompt' : 'Create Review Prompt'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Code Quality Reviewer"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="What does this review prompt evaluate?"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Model <span className="text-red-500">*</span>
              </label>
              <select
                value={defaultModel}
                onChange={(e) => setDefaultModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="gpt-5">GPT-5 (Recommended)</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-4">GPT-4</option>
              </select>
            </div>
          </div>

          {/* Criteria */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Evaluation Criteria <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {criteria.map((criterion, index) => (
                <div
                  key={index}
                  className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full"
                >
                  <span className="text-sm">{criterion}</span>
                  <button
                    type="button"
                    onClick={() => removeCriterion(index)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newCriterion}
                onChange={(e) => setNewCriterion(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCriterion())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Add new criterion..."
              />
              <button
                type="button"
                onClick={addCriterion}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            {criteria.length === 0 && (
              <p className="text-sm text-red-600 mt-1">At least one criterion is required</p>
            )}
          </div>

          {/* System Prompt */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt
            </label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="Instructions for the AI evaluator..."
            />
          </div>

          {/* Template */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">
                Evaluation Template <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={() => setShowVariableHelp(!showVariableHelp)}
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                <Code className="h-4 w-4" />
                {showVariableHelp ? 'Hide' : 'Show'} Variables
              </button>
            </div>

            {showVariableHelp && (
              <div className="mb-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-800 mb-2 font-medium">
                  Required Variables (click to insert):
                </p>
                <div className="flex flex-wrap gap-2">
                  {['{original_prompt}', '{num_configs}', '{all_responses}'].map((variable) => (
                    <button
                      key={variable}
                      type="button"
                      onClick={() => insertVariable(variable)}
                      className="px-2 py-1 bg-white border border-blue-300 text-blue-700 text-sm rounded hover:bg-blue-100 font-mono"
                    >
                      {variable}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <textarea
              id="template-textarea"
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              required
              rows={15}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="Enter the evaluation template..."
            />

            {/* Template Validator */}
            <div className="mt-2">
              <TemplateValidator template={template} criteria={criteria} />
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">
                Error: {error instanceof Error ? error.message : 'Failed to save review prompt'}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending || criteria.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? 'Saving...' : isEditMode ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
