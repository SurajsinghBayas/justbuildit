// Phase 3 & 4 — AI Insights & Sprint/Priority Re-balancer
// Shown on the ProjectDetail page

import { useState } from 'react';
import apiClient from '@/api/client';
import { predictSprintOutcome } from '@/api/aiClient';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, TrendingUp, AlertTriangle, ShieldCheck, Zap, BarChart3, Target, ArrowRight } from 'lucide-react';

interface Props {
  project: any;
  tasks: any[];
}

export default function AIInsightsPanel({ project, tasks }: Props) {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [sprintOutcome, setSprintOutcome] = useState<any>(null);

  // Generate Bedrock Insights (Phase 3 & 4)
  const generateInsights = async () => {
    setLoading(true);
    try {
      const payload = {
        project: { name: project.name, description: project.description },
        tasks: tasks.map(t => ({
          title: t.title,
          status: t.status,
          priority: t.priority,
          complexity: t.complexity_label,
          risk: t.risk_factors,
          sprint_points: t.story_points,
        }))
      };

      // 1. Bedrock health report
      const res = await apiClient.post('/analytics/ai-insights', payload);
      setReport(res.data.report || res.data);

      // 2. ML Sprint Outcome prediction (needs tasks + velocity)
      // Assuming a default team velocity of 20 for the demo
      const sprintTasks = tasks.filter(t => t.status === 'TODO' || t.status === 'IN_PROGRESS');
      if (sprintTasks.length > 0) {
        const mlRes = await predictSprintOutcome(sprintTasks, 20);
        setSprintOutcome(mlRes);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!report && !loading) {
    return (
      <div className="py-12 flex flex-col justify-center items-center text-center border-2 border-dashed border-purple-100 bg-purple-50/30 rounded-xl">
        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4 text-purple-600">
          <BarChart3 className="w-6 h-6" />
        </div>
        <h3 className="text-gray-900 font-semibold mb-1">AI Project Intelligence</h3>
        <p className="text-gray-500 text-sm max-w-sm mb-5">
          Generate a comprehensive health report, bottleneck analysis, and ML-driven sprint outcome prediction.
        </p>
        <Button onClick={generateInsights} className="bg-purple-600 hover:bg-purple-700 text-white gap-2">
          <Zap className="w-4 h-4" /> Run AI Analysis
        </Button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="py-16 flex flex-col justify-center items-center text-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin mb-4" />
        <p className="text-sm font-medium text-purple-800 animate-pulse">Running full AI diagnostic pipeline...</p>
        <p className="text-xs text-purple-400 mt-1">Calling Bedrock & AI Service ML models</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── ML Sprint Prediction ──────────────────────────── */}
      {sprintOutcome && (
        <Card className={`border ${sprintOutcome.sprint_outcome === 'ON TRACK' ? 'border-emerald-200 bg-emerald-50/50' : sprintOutcome.sprint_outcome === 'AT RISK' ? 'border-amber-200 bg-amber-50/50' : 'border-red-200 bg-red-50/50'}`}>
          <CardContent className="p-5 flex items-center justify-between">
            <div className="flex gap-4 items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-lg
                ${sprintOutcome.sprint_outcome === 'ON TRACK' ? 'bg-emerald-500' : sprintOutcome.sprint_outcome === 'AT RISK' ? 'bg-amber-500' : 'bg-red-500'}`}>
                {Math.round(sprintOutcome.predicted_completion_percent)}%
              </div>
              <div>
                <h3 className="font-bold text-gray-900 flex items-center gap-1.5">
                  ML Sprint Forecast: {sprintOutcome.sprint_outcome}
                  <span className="text-[9px] uppercase tracking-wider bg-gray-900 text-white px-1.5 py-0.5 rounded ml-2">XGBoost + Sequence MLP</span>
                </h3>
                <p className={`text-sm mt-0.5 font-medium ${sprintOutcome.sprint_outcome === 'ON TRACK' ? 'text-emerald-700' : sprintOutcome.sprint_outcome === 'AT RISK' ? 'text-amber-700' : 'text-red-700'}`}>
                  {sprintOutcome.recommendation}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500 mb-1">Total Points: <strong className="text-gray-900">{sprintOutcome.total_story_points}</strong></p>
              <p className="text-xs text-gray-500 mb-1">At Risk: <strong className="text-orange-600">{sprintOutcome.at_risk_story_points}</strong></p>
              <p className="text-xs text-gray-500">Avg Delay Prob: <strong>{Math.round(sprintOutcome.avg_task_delay_probability * 100)}%</strong></p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Bedrock Health Report ──────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Health Score */}
        <Card className="sleek-card">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
              <h3 className="font-semibold text-gray-900">Health Summary</h3>
            </div>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-3xl font-bold text-gray-900">{report?.health_score || 85}/100</span>
              <span className="text-sm font-medium text-emerald-600">Project Score</span>
            </div>
            <p className="text-sm text-gray-600">{report?.summary || 'The project is generally stable but has some risks to address.'}</p>
          </CardContent>
        </Card>

        {/* Bottlenecks */}
        <Card className="sleek-card border-red-100">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <h3 className="font-semibold text-red-900">Current Bottlenecks</h3>
            </div>
            {report?.bottlenecks && report.bottlenecks.length > 0 ? (
              <ul className="space-y-2">
                {report.bottlenecks.map((b: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2 text-gray-700">
                    <span className="text-red-500 font-bold">•</span> {b}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500 italic">No major bottlenecks detected.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actionable Recommendations */}
      <Card className="sleek-card">
        <CardContent className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">Bedrock Priority Recommendations</h3>
          </div>
          <div className="space-y-3">
            {report?.actionable_recommendations?.map((rec: string, i: number) => (
              <div key={i} className="flex gap-3 items-start bg-gray-50 p-3 rounded-lg border border-gray-100">
                <ArrowRight className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-800">{rec}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button variant="outline" className="text-xs" onClick={generateInsights}>
          <TrendingUp className="w-3 h-3 mr-1.5" /> Refresh Analytics
        </Button>
      </div>
    </div>
  );
}
