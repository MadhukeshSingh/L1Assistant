import { MessageSquare, Plus, Clock, FileText, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
}

interface ChatSidebarProps {
  sessions: ChatSession[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
}

const ChatSidebar = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
}: ChatSidebarProps) => {
  return (
    <aside className="w-64 sidebar-gradient flex flex-col h-full">
      {/* New Chat Button */}
      <div className="p-4">
        <Button
          onClick={onNewChat}
          className="w-full bg-white/20 hover:bg-white/30 text-white border-0 gap-2"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </Button>
      </div>

      {/* Recent Chats */}
      <div className="flex-1 px-4 overflow-y-auto">
        <div className="mb-3">
          <span className="text-xs font-medium text-white/60 uppercase tracking-wider">
            Recent Chats
          </span>
        </div>

        <div className="space-y-1">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors flex items-start gap-3 group ${
                currentSessionId === session.id
                  ? "bg-white/20 text-white"
                  : "text-white/80 hover:bg-white/10"
              }`}
            >
              <MessageSquare className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="overflow-hidden">
                <p className="text-sm font-medium truncate">{session.title}</p>
                <p className="text-xs text-white/50 flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3" />
                  {session.timestamp}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Bottom Links */}
      <div className="p-4 border-t border-white/10 space-y-1">
        <button className="w-full text-left px-3 py-2 rounded-lg text-white/70 hover:bg-white/10 transition-colors flex items-center gap-3 text-sm">
          <FileText className="w-4 h-4" />
          ASML Services
        </button>
        <button className="w-full text-left px-3 py-2 rounded-lg text-white/70 hover:bg-white/10 transition-colors flex items-center gap-3 text-sm">
          <Settings className="w-4 h-4" />
          Settings
        </button>
      </div>
    </aside>
  );
};

export default ChatSidebar;
