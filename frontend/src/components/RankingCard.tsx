interface RankingCardProps {
  experiment: {
    experiment_id: string;
    config_name: string;
    response: string;
    duration_seconds: number;
    estimated_cost_usd: number;
    total_tokens: number;
    is_acceptable?: boolean;
  };
  humanRank: number;
  aiScore?: number;
  aiRank?: number;
  aiComment?: string;
  aiCriteriaScores?: Record<string, number>;
  isDragging: boolean;
  dragHandleProps?: any;
  onToggleAcceptability?: (experimentId: string, isAcceptable: boolean) => void;
}

export function RankingCard({
  experiment,
  humanRank,
  aiScore,
  aiRank,
  aiComment,
  aiCriteriaScores,
  isDragging,
  dragHandleProps,
  onToggleAcceptability,
}: RankingCardProps) {
  const isAcceptable = experiment.is_acceptable !== false;

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent drag behavior when clicking toggle
    e.preventDefault(); // Prevent any default behavior
    if (onToggleAcceptability) {
      onToggleAcceptability(experiment.experiment_id, !isAcceptable);
    }
  };

  return (
    <div
      className={`
        w-full h-[900px]
        bg-white rounded-lg shadow-md
        ${isAcceptable ? 'border border-gray-200' : 'border-2 border-red-400'}
        flex flex-col
        transition-all duration-300
        ${isDragging ? 'scale-105 shadow-2xl opacity-80 rotate-2' : 'hover:shadow-lg'}
      `}
    >
      {/* Header - Sticky */}
      <div
        className="
          bg-gray-50 text-gray-700
          p-3 rounded-t-lg border-b border-gray-200
          sticky top-0 z-10
        "
      >
        {/* Top row: Rank, Config Name, Acceptable button */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2 cursor-grab active:cursor-grabbing flex-1" {...dragHandleProps}>
            <div className="flex-1">
              <div className="font-bold text-base">RANK #{humanRank}</div>
              <div className="text-sm font-medium truncate max-w-[180px] text-gray-600">
                {experiment.config_name}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {aiScore !== undefined && (
              <div className="text-right">
                <div className="text-xs text-gray-500">AI Score</div>
                <div className="text-base font-bold text-blue-600">{aiScore.toFixed(1)}/10</div>
                {aiRank !== undefined && aiRank !== humanRank && (
                  <div className="text-xs text-orange-600">AI: #{aiRank}</div>
                )}
              </div>
            )}
            {onToggleAcceptability && (
              <button
                onClick={handleToggle}
                onMouseDown={(e) => e.stopPropagation()}
                onTouchStart={(e) => e.stopPropagation()}
                className={`
                  px-2 py-1 rounded text-xs font-medium cursor-pointer
                  transition-colors duration-200
                  ${isAcceptable
                    ? 'bg-green-100 text-green-800 hover:bg-green-200 border border-green-300'
                    : 'bg-red-100 text-red-800 hover:bg-red-200 border border-red-300'}
                `}
                title={isAcceptable ? 'Mark as unacceptable' : 'Mark as acceptable'}
              >
                {isAcceptable ? '✓' : '✗'}
              </button>
            )}
          </div>
        </div>

        {/* AI Criteria Scores - Compact horizontal layout */}
        {aiCriteriaScores && Object.keys(aiCriteriaScores).length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1 border-t border-gray-200">
            {Object.entries(aiCriteriaScores).map(([criterion, score]) => (
              <span
                key={criterion}
                className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200"
              >
                {criterion}: {typeof score === 'number' ? score.toFixed(1) : score}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* AI Comment Section */}
      {aiComment && (
        <div className="bg-blue-50 border-b border-blue-200 p-3">
          <div className="flex items-start gap-2">
            <span className="text-blue-600 text-sm">🤖</span>
            <div className="flex-1">
              <div className="text-xs font-semibold text-blue-800 mb-1">AI Evaluation</div>
              <div className="text-sm text-blue-900 italic leading-relaxed">
                "{aiComment}"
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Response (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="prose prose-sm max-w-none">
          <div className="whitespace-pre-wrap text-gray-800 leading-relaxed text-sm">
            {experiment.response}
          </div>
        </div>
      </div>

      {/* Footer - Metrics */}
      <div className="p-3 bg-gray-50 rounded-b-lg border-t border-gray-200 flex justify-around text-xs">
        <div className="flex items-center gap-1">
          <span>⏱</span>
          <span className="font-medium">{experiment.duration_seconds.toFixed(1)}s</span>
        </div>
        <div className="flex items-center gap-1">
          <span>💰</span>
          <span className="font-medium">${experiment.estimated_cost_usd.toFixed(4)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>📊</span>
          <span className="font-medium">{experiment.total_tokens.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
