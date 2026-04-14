import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';

export default function Tasks() {
  const dummyTasks = [
    { id: 1, title: "Design System Implementation", priority: "High", status: "Todo" },
    { id: 2, title: "Auth Flow API", priority: "Medium", status: "In Progress" },
    { id: 3, title: "Update README", priority: "Low", status: "Done" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 p-4 sticky top-0 z-10 shadow-sm flex items-center justify-between">
         <Link to="/dashboard" className="font-bold text-xl tracking-tighter hover:opacity-80">justbuildit.</Link>
         <nav className="flex gap-4">
            <Link to="/dashboard"><Button variant="ghost">Dashboard</Button></Link>
         </nav>
      </header>

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8 flex-1">
        <div className="flex justify-between items-end border-b border-gray-200 pb-4">
           <div>
             <h1 className="text-4xl font-extrabold tracking-tight">Tasks</h1>
             <p className="text-gray-500 mt-2">Your team's task list in a glance.</p>
           </div>
           <Button className="bg-secondary text-secondary-foreground hover:bg-secondary/90 font-bold rounded-xl px-6 shadow-sm">
             Create Task
           </Button>
        </div>

        <div className="space-y-4">
          {dummyTasks.map((t) => (
            <Card key={t.id} className="border border-gray-200 shadow-sm hover:border-gray-400 transition-colors bg-white rounded-xl"> 
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                   <h3 className="font-bold text-lg text-gray-900">{t.title}</h3>
                   <div className="flex gap-2 mt-2">
                     <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-md font-medium">Priority: {t.priority}</span>
                     <span className="text-xs px-2 py-1 bg-primary/20 text-primary-foreground rounded-md font-medium">Status: {t.status}</span>
                   </div>
                </div>
                <Button variant="outline" size="sm" className="font-semibold rounded-lg">Open</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
