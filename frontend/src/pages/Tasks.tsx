import { useEffect, useState } from 'react';
import apiClient from '@/api/client';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';
import { CheckSquare, Plus, Loader2, ArrowLeft, Clock, AlertCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function Tasks() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [orgs, setOrgs] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [projectId, setProjectId] = useState('');
  const [orgId, setOrgId] = useState('');

  async function fetchData() {
    setLoading(true);
    try {
      const [tRes, pRes, oRes] = await Promise.all([
        apiClient.get('/tasks/'),
        apiClient.get('/projects/'),
        apiClient.get('/organizations/')
      ]);
      setTasks(tRes.data);
      setProjects(pRes.data);
      setOrgs(oRes.data);
      if (pRes.data.length > 0) setProjectId(pRes.data[0].id);
      if (oRes.data.length > 0) setOrgId(oRes.data[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !orgId) return alert("You must have a project and organization first.");
    setIsCreating(true);
    try {
      await apiClient.post('/tasks/', { 
        title, 
        description: desc, 
        project_id: projectId,
        organization_id: orgId
      });
      setOpen(false);
      setTitle('');
      setDesc('');
      fetchData(); // refresh tasks
    } catch (err) {
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      <header className="bg-white px-6 py-4 flex items-center justify-between border-b border-gray-200">
         <Link to="/dashboard" className="font-bold text-sm flex items-center gap-2 text-gray-600 hover:text-gray-900">
           <ArrowLeft className="w-4 h-4" /> Back to Dashboard
         </Link>
      </header>

      <main className="p-8 max-w-5xl mx-auto w-full space-y-8 flex-1">
        <div className="flex justify-between items-end border-b border-gray-200 pb-4">
           <div>
             <h1 className="text-3xl font-bold tracking-tight text-gray-900">Tasks</h1>
             <p className="text-sm text-gray-500 mt-1 font-medium">Your team's task list in a glance.</p>
           </div>
           
           <Dialog open={open} onOpenChange={setOpen}>
             <DialogTrigger asChild>
               <Button className="bg-gray-900 text-white hover:bg-gray-800 text-sm h-9">
                 <Plus className="w-4 h-4 mr-2" /> Create Task
               </Button>
             </DialogTrigger>
             <DialogContent className="sm:max-w-[425px] bg-white">
               <DialogHeader>
                 <DialogTitle>Create Task</DialogTitle>
               </DialogHeader>
               <form onSubmit={handleCreateTask} className="space-y-4 mt-4">
                 <div className="space-y-2">
                   <Label>Task Title</Label>
                   <Input value={title} onChange={e => setTitle(e.target.value)} required className="sleek-input" placeholder="What needs to be done?" />
                 </div>
                 <div className="space-y-2">
                   <Label>Description</Label>
                   <Input value={desc} onChange={e => setDesc(e.target.value)} className="sleek-input" placeholder="Task details" />
                 </div>
                 <div className="space-y-2 flex flex-col">
                   <Label>Select Project</Label>
                   <select value={projectId} onChange={e => setProjectId(e.target.value)} className="sleek-input bg-white h-10">
                     {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                     {projects.length === 0 && <option value="">No projects available</option>}
                   </select>
                 </div>
                 <div className="pt-4 flex justify-end">
                   <Button type="submit" disabled={isCreating || !projectId || !orgId} className="bg-gray-900 text-white w-full">
                     {isCreating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : 'Create Task'}
                   </Button>
                 </div>
               </form>
             </DialogContent>
           </Dialog>
        </div>

        {loading ? (
          <div className="flex justify-center p-20">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.length > 0 ? tasks.map((t: any) => (
              <Card key={t.id} className="sleek-card cursor-pointer"> 
                <CardContent className="p-4 flex items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="mt-1 flex-shrink-0 w-8 h-8 rounded border border-gray-200 bg-gray-50 flex items-center justify-center text-gray-500">
                      <CheckSquare className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{t.title}</h3>
                      <div className="flex flex-wrap gap-2 mt-2">
                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded
                          ${t.priority === 'High' ? 'bg-red-50 text-red-600 border border-red-100' : 'bg-gray-100 text-gray-600 border border-gray-200'}
                        `}>
                          {t.priority || 'Medium'} Priority
                        </span>
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 bg-blue-50 text-blue-600 border border-blue-100 rounded flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {t.status || 'TODO'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" className="font-semibold text-xs border-gray-200">Open</Button>
                </CardContent>
              </Card>
            )) : (
              <div className="py-16 text-center border border-dashed border-gray-200 rounded-lg">
                <CheckSquare className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-gray-900 mb-1">No tasks found</h3>
                <p className="text-sm text-gray-500">You're all caught up!</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
