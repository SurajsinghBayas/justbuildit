import apiClient from '@/api/client';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // Just a sample endpoint call based on backend structure
    apiClient.get('/health').then(res => setData(res.data)).catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <header className="bg-white border-b border-gray-200 p-4 sticky top-0 z-10 shadow-sm flex items-center justify-between">
         <div className="font-bold text-xl tracking-tighter">justbuildit.</div>
         <nav className="flex gap-4">
            <Link to="/projects"><Button variant="ghost" className="font-medium text-gray-600 hover:text-gray-900">Projects</Button></Link>
            <Link to="/tasks"><Button variant="ghost" className="font-medium text-gray-600 hover:text-gray-900">Tasks</Button></Link>
            <Link to="/organizations"><Button variant="ghost" className="font-medium text-gray-600 hover:text-gray-900">Organizations</Button></Link>
         </nav>
      </header>

      <main className="p-8 max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col gap-2 relative">
           <h1 className="text-4xl font-extrabold tracking-tight">Dashboard Overview</h1>
           <p className="text-lg text-gray-500">Track all your team's progress without distractions.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <Card className="border-t-4 border-t-primary shadow-sm rounded-lg overflow-hidden border-x-0 border-b-0 bg-white">
            <CardHeader>
              <CardTitle>Total Projects</CardTitle>
              <CardDescription>Active workspaces</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-5xl font-black text-gray-900">12</p>
            </CardContent>
          </Card>
          
          <Card className="border-t-4 border-t-secondary shadow-sm rounded-lg overflow-hidden border-x-0 border-b-0 bg-white">
            <CardHeader>
              <CardTitle>Tasks Completed</CardTitle>
              <CardDescription>In the last 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-5xl font-black text-gray-900">48</p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-accent shadow-sm rounded-lg overflow-hidden border-x-0 border-b-0 bg-white">
            <CardHeader>
              <CardTitle>Team Status</CardTitle>
              <CardDescription>Backend Health</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">
                {data ? "Online" : "Loading..."}
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
