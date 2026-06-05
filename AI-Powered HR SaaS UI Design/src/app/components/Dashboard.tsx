import { useState } from 'react';
import { Upload, Sparkles, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { motion } from 'motion/react';

const recentActivities = [
  { id: 1, type: 'success', message: 'AI matched 5 candidates for Senior Developer role', time: '2 min ago' },
  { id: 2, type: 'info', message: 'Resume uploaded: Sarah Johnson - Product Manager', time: '15 min ago' },
  { id: 3, type: 'success', message: 'Interview email sent to 3 candidates', time: '1 hour ago' },
  { id: 4, type: 'info', message: 'Job posting created: UX Designer', time: '2 hours ago' },
];

export function Dashboard() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files).map(f => f.name);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  return (
    <div className="flex-1 overflow-auto bg-background">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div>
          <h2>Create Job Posting</h2>
          <p className="text-muted-foreground mt-1">Post new positions and start recruiting top talent</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="bg-card rounded-xl border border-border p-6 backdrop-blur-sm shadow-sm"
          >
            <h3 className="mb-4 flex items-center gap-2">
              Job Details
              <Sparkles className="w-4 h-4 text-accent" />
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block mb-2 text-sm text-muted-foreground">Job Title</label>
                <input
                  type="text"
                  placeholder="e.g. Senior Software Engineer"
                  className="w-full px-4 py-2.5 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                />
              </div>

              <div>
                <label className="block mb-2 text-sm text-muted-foreground">Department</label>
                <select className="w-full px-4 py-2.5 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring transition-shadow">
                  <option>Engineering</option>
                  <option>Product</option>
                  <option>Design</option>
                  <option>Marketing</option>
                  <option>Sales</option>
                </select>
              </div>

              <div>
                <label className="block mb-2 text-sm text-muted-foreground">Job Description</label>
                <textarea
                  rows={6}
                  placeholder="Describe the role, responsibilities, and requirements..."
                  className="w-full px-4 py-2.5 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring transition-shadow resize-none"
                />
              </div>

              <button className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity shadow-lg shadow-primary/20">
                Create Job Posting
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="bg-card rounded-xl border border-border p-6 backdrop-blur-sm shadow-sm"
          >
            <h3 className="mb-4 flex items-center gap-2">
              Candidate Ingestion
              <div className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded-full border border-accent/20">
                AI-Powered
              </div>
            </h3>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
                isDragging
                  ? 'border-accent bg-accent/5 scale-[1.02]'
                  : 'border-border bg-secondary/30 hover:border-accent/50'
              }`}
            >
              <div className={`w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-accent to-chart-2 flex items-center justify-center transition-transform ${
                isDragging ? 'scale-110' : ''
              }`}>
                <Upload className="w-8 h-8 text-white drop-shadow-lg" />
              </div>
              <h4 className="mb-2">Drop PDF Resumes Here</h4>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse files
              </p>
              <input
                type="file"
                multiple
                accept=".pdf"
                className="hidden"
                id="file-upload"
                onChange={(e) => {
                  const files = Array.from(e.target.files || []).map(f => f.name);
                  setUploadedFiles(prev => [...prev, ...files]);
                }}
              />
              <label
                htmlFor="file-upload"
                className="inline-block px-6 py-2 bg-accent text-accent-foreground rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
              >
                Select Files
              </label>
            </div>

            {uploadedFiles.length > 0 && (
              <div className="mt-4 space-y-2">
                {uploadedFiles.map((file, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center gap-3 p-3 bg-success/10 border border-success/20 rounded-lg"
                  >
                    <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />
                    <span className="text-sm flex-1 truncate">{file}</span>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="bg-card rounded-xl border border-border p-6 backdrop-blur-sm shadow-sm"
        >
          <h3 className="mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-accent" />
            Recent AI Activity
          </h3>

          <div className="space-y-3">
            {recentActivities.map((activity) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: activity.id * 0.05 }}
                className="flex items-start gap-4 p-4 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
              >
                {activity.type === 'success' ? (
                  <div className="w-8 h-8 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0">
                    <CheckCircle2 className="w-4 h-4 text-success" />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-accent" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm">{activity.message}</p>
                  <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    {activity.time}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
