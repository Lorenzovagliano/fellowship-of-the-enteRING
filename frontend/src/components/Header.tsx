import { Sparkles } from "lucide-react";

export const Header = () => {
  return (
    <header className="bg-header text-header-foreground py-4 px-6">
      <div className="container mx-auto flex items-center gap-3">
        <div className="bg-primary rounded-lg p-2">
          <Sparkles className="h-6 w-6 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-xl font-bold">EXTRATOR DE PDF</h1>
          <p className="text-sm text-header-foreground/80">
            Extraia e processe documentos PDF com facilidade
          </p>
        </div>
      </div>
    </header>
  );
};
