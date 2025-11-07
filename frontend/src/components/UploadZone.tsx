import { Upload } from "lucide-react";
import { useCallback } from "react";

interface UploadZoneProps {
  title: string;
  description: string;
  accept?: string;
  onFileSelect: (file: File) => void;
  hint?: string;
}

export const UploadZone = ({
  title,
  description,
  accept,
  onFileSelect,
  hint,
}: UploadZoneProps) => {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  }, []);

  const handleClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    if (accept) {
      input.accept = accept;
    }
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        onFileSelect(file);
      }
    };
    input.click();
  };

  return (
    <div
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="border-2 border-dashed border-upload-border bg-upload-bg rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer hover:border-primary/50 transition-colors min-h-[240px]"
    >
      <div className="bg-primary/10 rounded-full p-4 mb-4">
        <Upload className="h-8 w-8 text-primary" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground text-center mb-2">
        {description}
      </p>
      {hint && (
        <p className="text-xs text-muted-foreground text-center">{hint}</p>
      )}
    </div>
  );
};
