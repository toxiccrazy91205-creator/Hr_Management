import { useState } from 'react';
import { CheckCircle2, XCircle, Sparkles, Mail } from 'lucide-react';
import { motion } from 'motion/react';

const candidates = [
  { id: 1, name: 'Sarah Johnson', score: 92, skills: ['React', 'TypeScript', 'Node.js', 'AWS'] },
  { id: 2, name: 'Michael Chen', score: 88, skills: ['Python', 'Django', 'PostgreSQL', 'Docker'] },
  { id: 3, name: 'Emily Rodriguez', score: 85, skills: ['Vue.js', 'GraphQL', 'MongoDB', 'CI/CD'] },
  { id: 4, name: 'David Kim', score: 82, skills: ['Java', 'Spring Boot', 'Kubernetes', 'Redis'] },
  { id: 5, name: 'Lisa Anderson', score: 79, skills: ['Angular', 'RxJS', 'Firebase', 'Azure'] },
  { id: 6, name: 'James Wilson', score: 76, skills: ['Go', 'Microservices', 'gRPC', 'Terraform'] },
];

const defaultEmailTemplate = `Dear [Candidate Name],

We are pleased to inform you that your application for the Senior Software Engineer position at TalentAI has been shortlisted by our AI-powered recruitment system.

Your profile demonstrates exceptional alignment with our requirements, particularly in the areas of:
• Technical Skills: [Key Skills]
• Experience Level: [Years] years
• AI Match Score: [Score]%

We would like to invite you to the next stage of our recruitment process. Please let us know your availability for a technical interview in the coming week.

Interview Details:
• Format: Virtual/In-person
• Duration: 60 minutes
• Focus: Technical assessment and cultural fit

Please confirm your availability at your earliest convenience.

Best regards,
The TalentAI Recruitment Team`;

function CircularProgress({ score }: { score: number }) {
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-20 h-20">
      <svg className="transform -rotate-90 w-full h-full">
        <circle
          cx="40"
          cy="40"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="none"
          className="text-secondary"
        />
        <circle
          cx="40"
          cy="40"
          r={radius}
          stroke="url(#gradient)"
          strokeWidth="6"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
          strokeLinecap="round"
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-semibold">{score}</span>
      </div>
    </div>
  );
}

export function ApprovalScreen() {
  const [emailContent, setEmailContent] = useState(defaultEmailTemplate);

  return (
    <div className="flex-1 overflow-auto bg-background">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2>AI Human-in-the-Loop Approval</h2>
            <p className="text-muted-foreground mt-1">Review and approve AI-shortlisted candidates</p>
          </div>
          <div className="px-4 py-2 bg-accent/10 text-accent rounded-lg border border-accent/20 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm">6 Candidates Shortlisted</span>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {candidates.map((candidate, idx) => (
            <motion.div
              key={candidate.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="bg-card rounded-xl border border-border p-6 hover:shadow-lg hover:shadow-accent/5 transition-all duration-300 hover:border-accent/30"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="mb-1">{candidate.name}</h3>
                  <p className="text-xs text-muted-foreground">Senior Software Engineer</p>
                </div>
                <CircularProgress score={candidate.score} />
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Key Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {candidate.skills.map((skill) => (
                      <span
                        key={skill}
                        className="px-2 py-1 bg-accent/10 text-accent text-xs rounded border border-accent/20"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-border">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Sparkles className="w-3 h-3" />
                    <span>AI Matched on {new Date().toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-card rounded-xl border border-border p-6 backdrop-blur-sm shadow-sm"
        >
          <div className="flex items-center gap-2 mb-4">
            <Mail className="w-5 h-5 text-accent" />
            <h3>AI-Drafted Interview Email</h3>
            <div className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded-full border border-accent/20">
              Review & Edit
            </div>
          </div>

          <textarea
            value={emailContent}
            onChange={(e) => setEmailContent(e.target.value)}
            rows={16}
            className="w-full px-4 py-3 bg-input-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring transition-shadow resize-none mb-4 font-mono text-sm"
          />

          <div className="flex items-center gap-3">
            <button className="flex-1 px-6 py-3 bg-success text-success-foreground rounded-lg hover:opacity-90 transition-all shadow-lg shadow-success/20 flex items-center justify-center gap-2">
              <CheckCircle2 className="w-5 h-5" />
              Approve & Send to All Candidates
            </button>
            <button className="px-6 py-3 bg-destructive/10 text-destructive rounded-lg hover:bg-destructive/20 transition-all border border-destructive/20 flex items-center gap-2">
              <XCircle className="w-5 h-5" />
              Reject
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
