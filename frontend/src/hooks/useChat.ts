import { useState, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
  messages: Message[];
}

// Configure your backend API URL here
const API_BASE_URL = "http://localhost:8000";

export const useChat = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const getCurrentSession = useCallback(() => {
    return sessions.find((s) => s.id === currentSessionId);
  }, [sessions, currentSessionId]);

  const createNewSession = useCallback(() => {
    const newSession: ChatSession = {
      id: uuidv4(),
      title: "New Chat",
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    return newSession.id;
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      let sessionId = currentSessionId;

      // Create new session if none exists
      if (!sessionId) {
        sessionId = createNewSession();
      }

      // Add user message
      const userMessage: Message = { role: "user", content };
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sessionId
            ? {
                ...s,
                messages: [...s.messages, userMessage],
                title:
                  s.messages.length === 0
                    ? content.slice(0, 30) + (content.length > 30 ? "..." : "")
                    : s.title,
              }
            : s
        )
      );

      setIsLoading(true);

      try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: content,
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to get response from server");
        }

        const data = await response.json();

        // Add assistant message
        const assistantMessage: Message = {
          role: "assistant",
          content: data.reply,
        };

        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [...s.messages, assistantMessage] }
              : s
          )
        );
      } catch (error) {
        console.error("Chat error:", error);

        // Add error message
        const errorMessage: Message = {
          role: "assistant",
          content:
            "Sorry, I'm having trouble connecting to the server. Please make sure the backend is running and try again.",
        };

        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [...s.messages, errorMessage] }
              : s
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [currentSessionId, createNewSession]
  );

  return {
    sessions,
    currentSessionId,
    currentSession: getCurrentSession(),
    isLoading,
    sendMessage,
    createNewSession,
    selectSession: setCurrentSessionId,
  };
};
