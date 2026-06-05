import { Download, Users, TrendingUp, Award } from 'lucide-react';
import { motion } from 'motion/react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

const attendanceData = [
  { month: 'Jan', rate: 94 },
  { month: 'Feb', rate: 92 },
  { month: 'Mar', rate: 96 },
  { month: 'Apr', rate: 95 },
  { month: 'May', rate: 93 },
  { month: 'Jun', rate: 97 },
];

const skillsData = [
  { skill: 'Leadership', value: 85 },
  { skill: 'Technical', value: 92 },
  { skill: 'Communication', value: 88 },
  { skill: 'Problem Solving', value: 90 },
  { skill: 'Creativity', value: 78 },
  { skill: 'Teamwork', value: 95 },
];

const employeeData = [
  { id: 1, name: 'Sarah Johnson', department: 'Engineering', score: 92, status: 'Excellent' },
  { id: 2, name: 'Michael Chen', department: 'Product', score: 88, status: 'Good' },
  { id: 3, name: 'Emily Rodriguez', department: 'Design', score: 85, status: 'Good' },
  { id: 4, name: 'David Kim', department: 'Marketing', score: 82, status: 'Good' },
  { id: 5, name: 'Lisa Anderson', department: 'Sales', score: 79, status: 'Average' },
  { id: 6, name: 'James Wilson', department: 'Engineering', score: 94, status: 'Excellent' },
];

function MetricCard({ icon: Icon, label, value, trend, color }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-card rounded-xl border border-border p-6 hover:shadow-lg hover:shadow-accent/5 transition-all duration-300"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{label}</p>
          <h3 className="mb-2">{value}</h3>
          <div className={`flex items-center gap-1 text-sm ${color}`}>
            <TrendingUp className="w-4 h-4" />
            <span>{trend}</span>
          </div>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color === 'text-success' ? 'from-success/10 to-success/20' : 'from-accent/10 to-chart-2/20'} flex items-center justify-center`}>
          <Icon className={`w-6 h-6 ${color === 'text-success' ? 'text-success' : 'text-accent'}`} />
        </div>
      </div>
    </motion.div>
  );
}

export function AnalyticsDashboard() {
  return (
    <div className="flex-1 overflow-auto bg-background">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div>
          <h2>Performance Analytics</h2>
          <p className="text-muted-foreground mt-1">Track employee performance and team metrics</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricCard
            icon={Users}
            label="Total Employees"
            value="1,247"
            trend="+12% from last month"
            color="text-accent"
          />
          <MetricCard
            icon={TrendingUp}
            label="Attendance Rate"
            value="95.3%"
            trend="+2.1% from last month"
            color="text-success"
          />
          <MetricCard
            icon={Award}
            label="Average Performance"
            value="87.5"
            trend="+5.2% from last month"
            color="text-accent"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-card rounded-xl border border-border p-6 backdrop-blur-sm shadow-sm"
          >
            <h3 className="mb-6">Attendance Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={attendanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="rate" fill="url(#barGradient)" radius={[8, 8, 0, 0]} />
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-card rounded-xl border border-border p-6 backdrop-blur-sm shadow-sm"
          >
            <h3 className="mb-6">Employee Skills Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={skillsData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="skill" stroke="#64748b" />
                <PolarRadiusAxis stroke="#64748b" />
                <Radar
                  name="Skills"
                  dataKey="value"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-card rounded-xl border border-border backdrop-blur-sm shadow-sm overflow-hidden"
        >
          <div className="p-6 border-b border-border">
            <h3>Employee Performance Table</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-secondary/30">
                <tr>
                  <th className="px-6 py-4 text-left text-sm text-muted-foreground">Name</th>
                  <th className="px-6 py-4 text-left text-sm text-muted-foreground">Department</th>
                  <th className="px-6 py-4 text-left text-sm text-muted-foreground">Score</th>
                  <th className="px-6 py-4 text-left text-sm text-muted-foreground">Status</th>
                  <th className="px-6 py-4 text-left text-sm text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody>
                {employeeData.map((employee, idx) => (
                  <motion.tr
                    key={employee.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + idx * 0.05 }}
                    className="border-b border-border hover:bg-secondary/20 transition-colors"
                  >
                    <td className="px-6 py-4">{employee.name}</td>
                    <td className="px-6 py-4 text-muted-foreground">{employee.department}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden max-w-[100px]">
                          <div
                            className="h-full bg-gradient-to-r from-accent to-chart-2 rounded-full"
                            style={{ width: `${employee.score}%` }}
                          />
                        </div>
                        <span className="text-sm">{employee.score}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 text-xs rounded-full ${
                          employee.status === 'Excellent'
                            ? 'bg-success/10 text-success border border-success/20'
                            : employee.status === 'Good'
                            ? 'bg-accent/10 text-accent border border-accent/20'
                            : 'bg-muted text-muted-foreground border border-border'
                        }`}
                      >
                        {employee.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button className="px-4 py-2 text-sm bg-accent/10 text-accent rounded-lg hover:bg-accent/20 transition-colors border border-accent/20 flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        Download Report
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 border-t border-border flex items-center justify-between bg-secondary/10">
            <p className="text-sm text-muted-foreground">Showing 6 of 1,247 employees</p>
            <div className="flex items-center gap-2">
              <button className="px-3 py-1 text-sm border border-border rounded hover:bg-secondary/50 transition-colors">
                Previous
              </button>
              <button className="px-3 py-1 text-sm bg-accent text-accent-foreground rounded">
                1
              </button>
              <button className="px-3 py-1 text-sm border border-border rounded hover:bg-secondary/50 transition-colors">
                2
              </button>
              <button className="px-3 py-1 text-sm border border-border rounded hover:bg-secondary/50 transition-colors">
                Next
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
