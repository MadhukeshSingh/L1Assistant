import { useState } from "react";
import ChatHeader from "@/components/ChatHeader";
import ChatSidebar from "@/components/ChatSidebar";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import { useChat } from "@/hooks/useChat";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const Index = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const {
    sessions,
    currentSessionId,
    currentSession,
    isLoading,
    sendMessage,
    createNewSession,
    selectSession,
  } = useChat();

  const handleNewChat = () => {
    createNewSession();
    setSidebarOpen(false);
  };

  const handleSelectSession = (id: string) => {
    selectSession(id);
    setSidebarOpen(false);
  };

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      {/* Mobile Sidebar Toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </Button>

      {/* Sidebar - Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed lg:static inset-y-0 left-0 z-40 transform transition-transform duration-200 lg:transform-none ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <ChatSidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatHeader onNewChat={handleNewChat} />

        <ChatWindow
          messages={currentSession?.messages || []}
          isLoading={isLoading}
        />

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>
    </div>
  );
};

export default Index;
