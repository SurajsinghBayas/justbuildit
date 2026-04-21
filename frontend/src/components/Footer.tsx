import { GitBranch, Globe, Bird, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-100 py-12 dark:bg-gray-900 dark:border-gray-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center dark:bg-white">
                <span className="text-white font-bold text-lg dark:text-gray-900">J</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">JustBuildIt</span>
            </div>
            <p className="text-gray-500 text-sm leading-relaxed dark:text-gray-400">
              The AI-powered project management platform built for modern engineering teams. 
              Automate tasks, predict risks, and build faster.
            </p>
            <div className="flex items-center gap-4 mt-6">
              <a href="https://github.com/SurajsinghBayas/justbuildit" target="_blank" rel="noreferrer" className="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                <GitBranch className="w-5 h-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                <Bird className="w-5 h-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                <Globe className="w-5 h-5" />
              </a>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 dark:text-white">Product</h3>
            <ul className="space-y-3">
              <li><Link to="/tasks" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Tasks</Link></li>
              <li><Link to="/projects" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Projects</Link></li>
              <li><Link to="/dashboard" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">AI Insights</Link></li>
              <li><a href="#" className="text-gray-500 hover:text-gray-900 text-sm flex items-center gap-1 dark:text-gray-400 dark:hover:text-white">Changelog <ExternalLink className="w-3 h-3" /></a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 dark:text-white">Resources</h3>
            <ul className="space-y-3">
              <li><Link to="/docs" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Documentation</Link></li>
              <li><a href="#" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">API Reference</a></li>
              <li><a href="#" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Community</a></li>
              <li><a href="#" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Blog</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 dark:text-white">Legal</h3>
            <ul className="space-y-3">
              <li><Link to="/privacy" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Privacy Policy</Link></li>
              <li><Link to="/terms" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Terms of Service</Link></li>
              <li><a href="#" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Cookie Policy</a></li>
              <li><a href="#" className="text-gray-500 hover:text-gray-900 text-sm dark:text-gray-400 dark:hover:text-white">Security</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4 dark:border-gray-800">
          <p className="text-gray-400 text-xs">
            © {currentYear} JustBuildIt. All rights reserved. Built with ❤️ for developers.
          </p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5 text-gray-400 text-xs">
              <Globe className="w-3.5 h-3.5" /> English (US)
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
