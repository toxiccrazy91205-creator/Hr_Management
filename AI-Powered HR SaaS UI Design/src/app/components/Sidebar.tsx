import { LayoutDashboard, UserCheck, BarChart3, MessageSquare } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: UserCheck, label: 'AI Approval', path: '/approval' },
  { icon: BarChart3, label: 'Analytics', path: '/analytics' },
  { icon: MessageSquare, label: 'AI Assistant', path: '/chat' },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-sidebar text-sidebar-foreground flex flex-col border-r border-sidebar-border">
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-chart-2 flex items-center justify-center">
            <div className="w-6 h-6 bg-white rounded" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }} />
          </div>
          <div>
            <h1 className="text-lg tracking-tight">TalentAI</h1>
            <p className="text-xs text-sidebar-foreground/60">HR Intelligence</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-lg shadow-sidebar-primary/20'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-5 h-5 ${isActive ? 'drop-shadow-[0_0_8px_rgba(99,102,241,0.6)]' : ''}`} />
                <span>{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-chart-1 to-chart-2 flex items-center justify-center text-sm">
            JD
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm truncate">John Doe</p>
            <p className="text-xs text-sidebar-foreground/50 truncate">HR Manager</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
