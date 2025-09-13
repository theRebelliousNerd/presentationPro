'use client';

import { useState, useCallback, ChangeEvent, DragEvent } from 'react';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type FileDropzoneProps = {
  onFilesChange: (files: { name: string; dataUrl: string }[]) => void;
  acceptedFormats: string;
};

export default function FileDropzone({ onFilesChange, acceptedFormats }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<{ name: string; dataUrl: string }[]>([]);

  const handleFileChange = useCallback(
    (newFiles: FileList) => {
      const validFiles = Array.from(newFiles);
      const allFiles = [...files];

      let processedCount = 0;
      validFiles.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataUrl = e.target?.result as string;
          if (dataUrl) {
            allFiles.push({ name: file.name, dataUrl });
          }
          processedCount++;
          if (processedCount === validFiles.length) {
             setFiles(allFiles);
             onFilesChange(allFiles);
          }
        };
        reader.readAsDataURL(file);
      });
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
          "border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors duration-300",
          isDragging ? "border-primary bg-accent" : "border-border hover:border-primary/50"
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
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <UploadCloud className="w-10 h-10" />
          <p className="font-semibold">Drag & drop files here, or click to select</p>
          <p className="text-xs">{acceptedFormats}</p>
        </div>
      </div>
      {files.length > 0 && (
        <div className="mt-3 space-y-2">
          <h4 className="font-semibold text-sm">New files to upload:</h4>
          <ul className="space-y-1">
            {files.map((file, index) => (
              <li key={index} className="flex items-center justify-between bg-secondary p-1.5 rounded-md text-xs">
                <div className="flex items-center gap-2">
                  <FileIcon className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono">{file.name}</span>
                </div>
                <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => handleRemoveFile(index)}>
                  <X className="h-3 w-3" />
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
