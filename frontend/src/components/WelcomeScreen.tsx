import { Bot } from "lucide-react";

const WelcomeScreen = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      {/* Bot Avatar */}
      <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center mb-6 shadow-lg shadow-primary/20">
        <Bot className="w-8 h-8 text-primary-foreground" />
      </div>

      {/* Greeting */}
      <h1 className="text-xl font-semibold text-foreground mb-1">
        Hey, <span className="inline-block animate-bounce">👋</span> I'm Q,
      </h1>
      <p className="text-lg text-muted-foreground">How can I help you?</p>
    </div>
  );
};

export default WelcomeScreen;
