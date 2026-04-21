import LandingHeader from '@/components/LandingHeader';
import Footer from '@/components/Footer';
import { BookOpen, Sparkles, Shield, Users, Rocket } from 'lucide-react';

export default function DocumentationPage() {
  const steps = [
    { title: 'Getting Started', icon: Rocket, desc: 'Set up your organization and create your first project in minutes.' },
    { title: 'AI Task Generation', icon: Sparkles, desc: 'Use Bedrock-powered AI to break down complex projects into actionable tasks.' },
    { title: 'Project Management', icon: Users, desc: 'Manage your kanban board, track status, and assign tasks to your team.' },
    { title: 'AI Insights', icon: Shield, desc: 'Understand risks and project health with our ML-driven analytics dashboard.' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 font-sans transition-colors">
      <LandingHeader />
      <main className="max-w-7xl mx-auto px-4 py-20 sm:px-6 lg:px-8">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-violet-50 text-violet-700 rounded-full text-xs font-bold mb-6">
            <BookOpen className="w-3.5 h-3.5" /> Documentation
          </div>
          <h1 className="text-5xl font-black text-gray-900 mb-6">Master JustBuildIt</h1>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            Everything you need to know about optimizing your engineering workflow with AI and predictive analytics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((s, i) => (
            <div key={i} className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm hover:shadow-xl transition-all">
              <div className="w-12 h-12 bg-gray-900 rounded-2xl flex items-center justify-center mb-6">
                <s.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{s.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{s.desc}</p>
              <button className="mt-6 text-violet-600 text-sm font-bold hover:underline flex items-center gap-1">
                Learn more
              </button>
            </div>
          ))}
        </div>

        <section className="mt-24 bg-gray-900 rounded-[40px] p-12 text-white relative overflow-hidden">
          <div className="relative z-10 max-w-2xl">
            <h2 className="text-3xl font-bold mb-6 italic">"The future of coding is collaborative AI."</h2>
            <p className="text-gray-400 leading-relaxed mb-8">
              JustBuildIt isn't just a task tracker. It's a partner that learns from your code quality, velocity, and delivery patterns to provide real-time guidance.
            </p>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-violet-600 flex items-center justify-center font-bold">J</div>
              <div>
                <div className="font-bold">JustBuildIt Team</div>
                <div className="text-xs text-gray-500 uppercase tracking-widest font-bold mt-0.5">Core Contributors</div>
              </div>
            </div>
          </div>
          <div className="absolute top-0 right-0 w-1/3 h-full bg-gradient-to-l from-violet-600/20 to-transparent pointer-events-none" />
        </section>
      </main>
      <Footer />
    </div>
  );
}
