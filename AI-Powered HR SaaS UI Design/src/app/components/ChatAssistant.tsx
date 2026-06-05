import { useState } from 'react';
import { Send, Paperclip, Sparkles, Plus } from 'lucide-react';
import { motion } from 'motion/react';

const chatHistory = [
  { id: 1, title: 'Candidate screening tips', time: '2 hours ago' },
  { id: 2, title: 'Interview questions for engineers', time: 'Yesterday' },
  { id: 3, title: 'Salary benchmarking data', time: '2 days ago' },
  { id: 4, title: 'Onboarding best practices', time: '3 days ago' },
];

const initialMessages = [
  {
    id: 1,
    role: 'assistant',
    content: "Hello! I'm your AI HR Assistant. I can help you with candidate screening, interview preparation, salary insights, and HR policy questions. What would you like to know?",
    time: '10:30 AM',
  },
  {
    id: 2,
    role: 'user',
    content: 'What are the key skills I should look for when hiring a Senior Software Engineer?',
    time: '10:32 AM',
  },
  {
    id: 3,
    role: 'assistant',
    content: `Great question! When hiring a Senior Software Engineer, focus on these key areas:

**Technical Skills:**
• Proficiency in multiple programming languages (e.g., JavaScript, Python, Java)
• Deep understanding of software architecture and design patterns
• Experience with cloud platforms (AWS, Azure, or GCP)
• Knowledge of CI/CD pipelines and DevOps practices

**Soft Skills:**
• Strong leadership and mentoring abilities
• Excellent problem-solving and analytical thinking
• Clear communication skills for technical and non-technical audiences
• Ability to work in cross-functional teams

**Experience:**
• 5+ years in software development
• Track record of leading complex projects
• Experience with agile methodologies
• Portfolio of successful product launches

Would you like me to generate specific interview questions for these areas?`,
    time: '10:32 AM',
  },
];

export function ChatAssistant() {
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      role: 'user',
      content: inputValue,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages([...messages, newMessage]);
    setInputValue('');

    setTimeout(() => {
      const aiResponse = {
        id: messages.length + 2,
        role: 'assistant',
        content: "I'm processing your request. This is a demo response to show the interface. In a real application, this would be connected to an AI backend service.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-background">
      <aside className="w-72 bg-card border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <button className="w-full px-4 py-3 bg-accent text-accent-foreground rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4">
          <h4 className="text-xs text-muted-foreground mb-3 px-2">Recent Chats</h4>
          <div className="space-y-1">
            {chatHistory.map((chat, idx) => (
              <motion.button
                key={chat.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`w-full px-3 py-3 rounded-lg text-left transition-colors ${
                  idx === 0
                    ? 'bg-accent/10 border border-accent/20'
                    : 'hover:bg-secondary/50'
                }`}
              >
                <p className="text-sm truncate mb-1">{chat.title}</p>
                <p className="text-xs text-muted-foreground">{chat.time}</p>
              </motion.button>
            ))}
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <div className="p-6 border-b border-border bg-card/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-chart-2 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white drop-shadow-lg" />
            </div>
            <div>
              <h3>AI HR Assistant</h3>
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
                Online and ready to help
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-6 space-y-6">
          {messages.map((message, idx) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-chart-2 flex items-center justify-center flex-shrink-0 shadow-lg shadow-accent/20">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
              )}

              <div className={`max-w-2xl ${message.role === 'user' ? 'order-first' : ''}`}>
                <div
                  className={`rounded-2xl px-5 py-4 ${
                    message.role === 'user'
                      ? 'bg-accent text-accent-foreground shadow-lg shadow-accent/10'
                      : 'bg-card border border-border'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                </div>
                <p className={`text-xs text-muted-foreground mt-2 px-1 ${message.role === 'user' ? 'text-right' : ''}`}>
                  {message.time}
                </p>
              </div>

              {message.role === 'user' && (
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-chart-3 to-chart-4 flex items-center justify-center flex-shrink-0 text-sm text-white shadow-lg">
                  JD
                </div>
              )}
            </motion.div>
          ))}
        </div>

        <div className="p-6 border-t border-border bg-card/50 backdrop-blur-sm">
          <div className="flex items-end gap-3">
            <button className="p-3 rounded-lg hover:bg-secondary/50 transition-colors text-muted-foreground hover:text-foreground">
              <Paperclip className="w-5 h-5" />
            </button>

            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask me anything about HR, recruitment, or employee management..."
                rows={1}
                className="w-full px-4 py-3 bg-input-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-ring transition-shadow resize-none max-h-32"
              />
            </div>

            <button
              onClick={handleSend}
              className="p-3 bg-accent text-accent-foreground rounded-xl hover:opacity-90 transition-opacity shadow-lg shadow-accent/20 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!inputValue.trim()}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <p className="text-xs text-muted-foreground mt-3 text-center">
            AI-powered responses are generated for demonstration purposes
          </p>
        </div>
      </div>
    </div>
  );
}
