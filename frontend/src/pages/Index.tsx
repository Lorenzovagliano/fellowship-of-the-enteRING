import { useState } from "react";
import { UploadZone } from "@/components/UploadZone";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [jsonText, setJsonText] = useState("");
  const [label, setLabel] = useState("");
  const [useCache, setUseCache] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const { toast } = useToast();

  const handlePdfFile = (file: File) => {
    setPdfFile(file);
    toast({
      title: "Arquivo PDF carregado",
      description: file.name,
    });
  };

  const handleExtract = async () => {
    if (!pdfFile) {
      toast({
        title: "Erro",
        description: "Por favor, faça upload de um arquivo PDF",
        variant: "destructive",
      });
      return;
    }

    if (!jsonText) {
      toast({
        title: "Erro",
        description: "Por favor, forneça um schema JSON",
        variant: "destructive",
      });
      return;
    }

    if (!label) {
      toast({
        title: "Erro",
        description: "Por favor, forneça um label para o documento",
        variant: "destructive",
      });
      return;
    }

    try {
      JSON.parse(jsonText);
    } catch (e) {
      toast({
        title: "Erro no JSON",
        description: "O schema JSON fornecido não é válido",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append("pdf", pdfFile);
      formData.append("label", label);
      formData.append("schema", jsonText);
      formData.append("use_cache", useCache.toString());

      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      
      const response = await fetch(`${apiUrl}/extract`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);

      toast({
        title: "Extração concluída!",
        description: "Os dados foram extraídos com sucesso",
      });
    } catch (error) {
      toast({
        title: "Erro na extração",
        description:
          error instanceof Error ? error.message : "Ocorreu um erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-6 py-12">
        <div className="flex items-center justify-center gap-4 mb-12">
          <div className="bg-primary w-12 h-12 rounded-lg" />
          <h1 className="text-3xl font-bold text-foreground">ENTER - EXTRATOR DE PDF</h1>
        </div>
        <section className="mb-12">
          <div className="bg-card rounded-lg shadow-md p-8">
            <div className="flex items-center space-x-2 mb-6">
              <Switch
                id="cache"
                checked={useCache}
                onCheckedChange={setUseCache}
              />
              <Label htmlFor="cache" className="cursor-pointer">
                Usar Cache
              </Label>
            </div>

            <div className="mb-6">
              <Label htmlFor="label" className="text-base mb-2 block">
                Label do Documento
              </Label>
              <Input
                id="label"
                placeholder="Ex: invoice, contract, receipt"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="max-w-md"
              />
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div>
                <Label className="text-base mb-3 block">Schema JSON</Label>
                <Textarea
                  value={jsonText}
                  onChange={(e) => setJsonText(e.target.value)}
                  placeholder="Cole seu schema JSON aqui..."
                  className="min-h-[240px] font-mono text-sm"
                />
              </div>

              <div>
                <Label className="text-base mb-3 block">Documento PDF</Label>
                <UploadZone
                  title="Documento PDF"
                  description="Faça upload do seu arquivo PDF"
                  accept=".pdf"
                  onFileSelect={handlePdfFile}
                  hint={pdfFile ? `Selecionado: ${pdfFile.name}` : "ou clique para navegar"}
                />
              </div>
            </div>

            <div className="flex justify-center">
              <Button
                size="lg"
                onClick={handleExtract}
                disabled={isLoading || !pdfFile || !jsonText || !label}
                className="min-w-[200px]"
              >
                {isLoading ? "Extraindo..." : "EXTRAIR DADOS"}
              </Button>
            </div>
          </div>
        </section>

        {results && (
          <section>
            <ResultsDisplay data={results.data} metadata={results.metadata} />
          </section>
        )}
      </main>
    </div>
  );
};

export default Index;
