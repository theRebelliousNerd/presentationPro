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

      validFiles.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataUrl = e.target?.result as string;
          if (dataUrl) {
            const updatedFiles = [...allFiles, { name: file.name, dataUrl }];
            setFiles(updatedFiles);
            onFilesChange(updatedFiles);
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
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-300",
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
          <UploadCloud className="w-12 h-12" />
          <p className="font-semibold">Drag & drop files here, or click to select</p>
          <p className="text-xs">{acceptedFormats}</p>
        </div>
      </div>
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="font-semibold">Uploaded Files:</h4>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li key={index} className="flex items-center justify-between bg-secondary p-2 rounded-md text-sm">
                <div className="flex items-center gap-2">
                  <FileIcon className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono">{file.name}</span>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleRemoveFile(index)}>
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
