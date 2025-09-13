'use client';

import { useState, useCallback, ChangeEvent, DragEvent } from 'react';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type FileDropzoneProps = {
  onFilesChange: (files: File[]) => void;
  acceptedFormats: string;
};

export default function FileDropzone({ onFilesChange, acceptedFormats }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

  const handleFileChange = useCallback(
    (newFiles: FileList) => {
      const allFiles = [...files, ...Array.from(newFiles)];
      setFiles(allFiles);
      onFilesChange(allFiles);
    },
    [files, onFilesChange]
  );
  
  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files);
    }
  };
  
  const handleRemoveFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onFilesChange(newFiles);
  };

  return (
    <div className="w-full">
      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-300 hover:shadow-md",
          isDragging ? "border-primary bg-primary/10 shadow-lg scale-[1.02]" : "border-border hover:border-primary/50 hover:bg-muted/10"
        )}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput')?.click()}
      >
        <input
          id="fileInput"
          type="file"
          multiple
          className="hidden"
          onChange={(e: ChangeEvent<HTMLInputElement>) => e.target.files && handleFileChange(e.target.files)}
          accept={acceptedFormats}
        />
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <UploadCloud className="w-12 h-12 text-primary/60" />
          <p className="font-headline font-semibold text-foreground">Drag & drop files here, or click to select</p>
          <p className="text-xs font-body text-muted-foreground/80">{acceptedFormats}</p>
        </div>
      </div>
      {files.length > 0 && (
        <div className="mt-4 space-y-3">
          <h4 className="font-headline font-semibold text-sm text-foreground">Files to upload:</h4>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li key={index} className="flex items-center justify-between bg-muted/30 border border-border/50 p-3 rounded-lg text-xs hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-2">
                  <FileIcon className="h-4 w-4 text-primary" />
                  <span className="font-body font-medium">{file.name}</span>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-destructive/20 hover:text-destructive" onClick={(e) => { e.stopPropagation(); handleRemoveFile(index); }}>
                  <X className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
