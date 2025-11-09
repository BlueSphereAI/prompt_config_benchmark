interface RecommendationBannerProps {
  recommendation: {
    recommended_config: string;
    final_score: number;
    quality_score: number;
    speed_score: number;
    cost_score: number;
    confidence: string;
    confidence_factors: string[];
    reasoning: string;
    runner_up_config?: string;
    score_difference?: number;
  };
}

export function RecommendationBanner({ recommendation }: RecommendationBannerProps) {
  const confidenceColors = {
    HIGH: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', badge: 'bg-green-100' },
    MEDIUM: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', badge: 'bg-yellow-100' },
    LOW: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-800', badge: 'bg-orange-100' },
  };

  const colors = confidenceColors[recommendation.confidence as keyof typeof confidenceColors] || confidenceColors.MEDIUM;

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-6 mb-6`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🏆</span>
          <div>
            <h2 className={`text-xl font-bold ${colors.text}`}>
              RECOMMENDED CONFIGURATION
            </h2>
            <p className="text-lg font-semibold text-gray-900 mt-1">
              {recommendation.recommended_config}
            </p>
          </div>
        </div>
        <span className={`${colors.badge} ${colors.text} px-3 py-1 rounded-full text-sm font-medium`}>
          {recommendation.confidence} Confidence
        </span>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 leading-relaxed">
          {recommendation.reasoning}
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="bg-white rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">Weighted Score</div>
          <div className="text-2xl font-bold text-gray-900">
            {recommendation.final_score.toFixed(1)}/10
          </div>
        </div>
        <div className="bg-white rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">Quality (60%)</div>
          <div className="text-2xl font-bold text-blue-600">
            {recommendation.quality_score.toFixed(1)}
          </div>
        </div>
        <div className="bg-white rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">Speed (30%)</div>
          <div className="text-2xl font-bold text-green-600">
            {recommendation.speed_score.toFixed(1)}
          </div>
        </div>
        <div className="bg-white rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">Cost (10%)</div>
          <div className="text-2xl font-bold text-purple-600">
            {recommendation.cost_score.toFixed(1)}
          </div>
        </div>
      </div>

      {recommendation.confidence_factors.length > 0 && (
        <div className="bg-white bg-opacity-60 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-700 mb-2">
            Confidence Factors:
          </div>
          <ul className="text-sm text-gray-600 space-y-1">
            {recommendation.confidence_factors.map((factor, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-green-500 mr-2">✓</span>
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      {recommendation.runner_up_config && (
        <div className="mt-4 text-sm text-gray-600">
          Runner-up: <span className="font-medium">{recommendation.runner_up_config}</span>
          {recommendation.score_difference !== undefined && (
            <span className="ml-2">
              (Score difference: {recommendation.score_difference.toFixed(2)})
            </span>
          )}
        </div>
      )}
    </div>
  );
}
