import { CheckCircle, Copy, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

interface ResultsDisplayProps {
  data: Record<string, any>;
  metadata?: {
    method: string;
    processing_time: number;
    cache_level?: string;
  };
}

export const ResultsDisplay = ({ data, metadata }: ResultsDisplayProps) => {
  const { toast } = useToast();

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    toast({
      title: "Copiado!",
      description: "Resultado copiado para a área de transferência",
    });
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "extracted-data.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: "Download iniciado",
      description: "Arquivo JSON baixado com sucesso",
    });
  };

  return (
    <Card className="p-6 mt-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold">Dados Extraídos</h2>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-2" />
            Copiar
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4 mr-2" />
            Baixar JSON
          </Button>
        </div>
      </div>

      {metadata && (
        <div className="bg-muted rounded-md p-3 mb-4 text-sm">
          <div className="flex flex-wrap gap-4">
            <span>
              <strong>Método:</strong> {metadata.method}
            </span>
            <span>
              <strong>Tempo:</strong> {metadata.processing_time.toFixed(2)}s
            </span>
            {metadata.cache_level && (
              <span>
                <strong>Cache:</strong> {metadata.cache_level}
              </span>
            )}
          </div>
        </div>
      )}

      <pre className="bg-secondary p-4 rounded-md overflow-auto max-h-[500px] text-sm">
        {JSON.stringify(data, null, 2)}
      </pre>
    </Card>
  );
};
