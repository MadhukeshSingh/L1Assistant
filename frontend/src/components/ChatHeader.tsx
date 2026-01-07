import { RefreshCw, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import q3Logo from "@/assets/q3-logo.png";

interface ChatHeaderProps {
  onNewChat: () => void;
}

const ChatHeader = ({ onNewChat }: ChatHeaderProps) => {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-background border-b border-border">
      <div className="flex items-center">
        <img src={q3Logo} alt="Q3 Technologies" className="h-10 object-contain" />
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onNewChat}
          className="text-muted-foreground hover:text-foreground"
        >
          <RefreshCw className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-foreground"
        >
          <User className="w-4 h-4" />
        </Button>
      </div>
    </header>
  );
};

export default ChatHeader;
