import axios from 'axios';

// AI service client — separate base URL from backend
const aiClient = axios.create({
  baseURL: 'http://localhost:8001',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

export default aiClient;

// ── Prediction helpers ─────────────────────────────────────────────────────

export async function predictDelay(task: any) {
  try {
    const res = await aiClient.post('/predict/delay', {
      task_id: task.id,
      title: task.title || '',
      description: task.description || '',
      tags: task.tags || [],
      complexity_label: task.complexity_label || 'medium',
      risk_factors: task.risk_factors || [],
      subtask_count: (task.subtasks || []).length,
      assignee_load: 3,
      story_points: task.story_points || 3,
      estimated_time: task.estimated_time || 4,
      past_delay_rate_assignee: 0.2,
    });
    return res.data;
  } catch { return null; }
}

export async function predictDuration(task: any) {
  try {
    const res = await aiClient.post('/predict/duration', {
      task_id: task.id,
      title: task.title || '',
      description: task.description || '',
      tags: task.tags || [],
      complexity_label: task.complexity_label || 'medium',
      subtask_count: (task.subtasks || []).length,
      story_points: task.story_points || 3,
      estimated_time: task.estimated_time || 4,
      task_type: task.task_type || 'backend',
      assignee_speed: 1.0,
    });
    return res.data;
  } catch { return null; }
}

export async function predictBottleneck(task: any) {
  try {
    const res = await aiClient.post('/predict/bottleneck', {
      task_id: task.id,
      title: task.title || '',
      description: task.description || '',
      risk_factors: task.risk_factors || [],
      dependency_count: (task.dependencies || []).length,
      dependency_depth: (task.dependencies || []).length,
      num_downstream_tasks: 0,
      task_delay_history: 0.2,
      complexity_label: task.complexity_label || 'medium',
    });
    return res.data;
  } catch { return null; }
}

export async function recommendNextTask(userId: string, tasks: any[]) {
  try {
    const res = await aiClient.post('/recommend/next-task', {
      user_id: userId,
      user_skills: [],
      project_tasks: tasks.map(t => ({
        id: t.id,
        title: t.title,
        priority: t.priority,
        status: t.status,
        required_skills: t.required_skills || [],
        story_points: t.story_points || 3,
        complexity_label: t.complexity_label || 'medium',
        dependency_blocked: false,
        created_at: t.created_at,
      })),
    });
    return res.data;
  } catch { return null; }
}

export async function predictSprintOutcome(tasks: any[], velocity: number) {
  try {
    const res = await aiClient.post('/predict/sprint-outcome', {
      tasks: tasks.map(t => ({
        story_points: t.story_points || 3,
        complexity_label: t.complexity_label || 'medium',
        delay_probability: 0.25,
      })),
      sprint_days: 14,
      team_velocity: velocity,
      blocked_tasks: tasks.filter(t => (t.dependencies || []).length > 0).length,
    });
    return res.data;
  } catch { return null; }
}
