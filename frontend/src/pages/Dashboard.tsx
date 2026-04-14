import apiClient from '@/api/client';
import { useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { LogOut, LayoutDashboard, Briefcase, CheckSquare, Building, Loader2, Plus, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [meRes, summaryRes, projectsRes] = await Promise.all([
          apiClient.get('/auth/me'),
          apiClient.get('/analytics/summary'),
          apiClient.get('/projects/')
        ]);
        setUser(meRes.data);
        setSummary(summaryRes.data);
        setProjects(projectsRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <header className="bg-white px-6 py-4 flex items-center justify-between border-b border-gray-200">
         <div className="font-bold text-xl tracking-tighter flex items-center gap-2 text-gray-900">
            justbuildit.
         </div>
         <nav className="flex gap-2">
            <Link to="/dashboard"><Button variant="ghost" className="font-semibold px-3 h-8 text-sm"><LayoutDashboard className="w-4 h-4 mr-2"/> Dashboard</Button></Link>
            <Link to="/projects"><Button variant="ghost" className="font-medium text-gray-600 px-3 h-8 text-sm"><Briefcase className="w-4 h-4 mr-2"/> Projects</Button></Link>
            <Link to="/tasks"><Button variant="ghost" className="font-medium text-gray-600 px-3 h-8 text-sm"><CheckSquare className="w-4 h-4 mr-2"/> Tasks</Button></Link>
            <Link to="/organizations"><Button variant="ghost" className="font-medium text-gray-600 px-3 h-8 text-sm"><Building className="w-4 h-4 mr-2"/> Organizations</Button></Link>
         </nav>
         <div className="flex items-center gap-4">
            <span className="font-medium text-sm text-gray-700">{user?.name || user?.email}</span>
            <Button variant="outline" size="sm" onClick={handleLogout} className="border-gray-200 text-gray-600">
              <LogOut className="w-4 h-4 mr-2" /> Logout
            </Button>
         </div>
      </header>

      <main className="p-8 max-w-6xl mx-auto space-y-10">
        <div className="flex flex-col gap-1 mt-4">
           <h1 className="text-3xl font-bold tracking-tight text-gray-900">Welcome back, {user?.name?.split(' ')[0] || 'Builder'}</h1>
           <p className="text-gray-500 font-medium">Overview of your workspace performance.</p>
        </div>

        <div className="grid md:grid-cols-4 gap-4">
          <StatCard title="Projects" value={summary?.total_projects || projects.length} />
          <StatCard title="Tasks" value={summary?.total_tasks || 0} />
          <StatCard title="Organizations" value={summary?.total_organizations || 0} />
          <StatCard title="Completed" value={summary?.completed_tasks || 0} />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Projects</h2>
            <Link to="/projects">
              <Button variant="ghost" size="sm" className="text-gray-600">View All <ArrowRight className="w-4 h-4 ml-1" /></Button>
            </Link>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {projects.length > 0 ? projects.slice(0, 3).map((proj: any) => (
              <Card key={proj.id} className="sleek-card cursor-pointer">
                <CardContent className="p-5">
                  <h3 className="font-semibold text-gray-900 truncate">{proj.name}</h3>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">{proj.description || 'No description'}</p>
                  <div className="mt-4 flex items-center gap-2">
                     <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                     <span className="text-xs font-medium text-gray-500">Active</span>
                  </div>
                </CardContent>
              </Card>
            )) : (
              <div className="col-span-3 border border-dashed border-gray-200 rounded-lg p-10 flex flex-col items-center text-center">
                <Briefcase className="w-8 h-8 text-gray-300 mb-3" />
                <h3 className="text-sm font-semibold text-gray-900 mb-1">No projects yet</h3>
                <p className="text-sm text-gray-500 mb-4">Create your first project to get started</p>
                <Link to="/projects"><Button size="sm"><Plus className="w-4 h-4 mr-2" /> Create Project</Button></Link>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({ title, value }: { title: string, value: number }) {
  return (
    <Card className="sleek-card">
      <CardContent className="p-5">
        <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
        <h3 className="text-3xl font-semibold tracking-tight text-gray-900">{value}</h3>
      </CardContent>
    </Card>
  );
}
