import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle, AlertCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

interface TemplateValidatorProps {
  template: string;
  criteria: string[];
}

export function TemplateValidator({ template, criteria }: TemplateValidatorProps) {
  const [debouncedTemplate, setDebouncedTemplate] = useState(template);

  // Debounce template changes (500ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTemplate(template);
    }, 500);

    return () => clearTimeout(timer);
  }, [template]);

  // Validate template
  const { data: validation, isLoading } = useQuery({
    queryKey: ['validate-template', debouncedTemplate, criteria],
    queryFn: () => api.validateReviewPrompt(debouncedTemplate, criteria),
    enabled: debouncedTemplate.length > 0,
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <RefreshCw className="h-4 w-4 animate-spin" />
        <span>Validating template...</span>
      </div>
    );
  }

  if (!validation) {
    return null;
  }

  const { valid, errors, warnings } = validation;

  if (valid && errors.length === 0 && warnings.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-md p-2">
        <CheckCircle className="h-4 w-4 flex-shrink-0" />
        <span>Template is valid</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Errors */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800 mb-1">
                {errors.length} Error{errors.length !== 1 ? 's' : ''}
              </p>
              <ul className="space-y-1">
                {errors.map((error, idx) => (
                  <li key={idx} className="text-sm text-red-700">
                    • {error}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-800 mb-1">
                {warnings.length} Warning{warnings.length !== 1 ? 's' : ''}
              </p>
              <ul className="space-y-1">
                {warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-yellow-700">
                    • {warning}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Success with warnings */}
      {valid && errors.length === 0 && warnings.length > 0 && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-md p-2">
          <CheckCircle className="h-4 w-4 flex-shrink-0" />
          <span>Template is valid (with warnings)</span>
        </div>
      )}
    </div>
  );
}
