'use client';

import { useState, useCallback, ChangeEvent, DragEvent, useEffect, useRef } from 'react';
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
  const inputRef = useRef<HTMLInputElement | null>(null);
  const dirInputRef = useRef<HTMLInputElement | null>(null);
  // Stable IDs for label/htmlFor wiring without relying on useId (which may include colons)
  const fileInputIdRef = useRef<string>(() => `fd-files-${Math.random().toString(36).slice(2)}`);
  const dirInputIdRef = useRef<string>(() => `fd-dirs-${Math.random().toString(36).slice(2)}`);
  const fileInputId = (typeof fileInputIdRef.current === 'function' ? (fileInputIdRef.current as any)() : fileInputIdRef.current) as string;
  const dirInputId = (typeof dirInputIdRef.current === 'function' ? (dirInputIdRef.current as any)() : dirInputIdRef.current) as string;

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

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const items = e.dataTransfer.items;
    if (items && items.length && (items as any)[0]?.webkitGetAsEntry) {
      const filesFromDirs: File[] = [];
      const traverse = async (entry: any, path='') => {
        return new Promise<void>((resolve) => {
          try {
            if (entry.isFile) {
              entry.file((file: File) => { filesFromDirs.push(file); resolve(); });
            } else if (entry.isDirectory) {
              const reader = entry.createReader();
              reader.readEntries(async (entries: any[]) => {
                for (const ent of entries) { await traverse(ent, path + entry.name + '/'); }
                resolve();
              });
            } else { resolve(); }
          } catch { resolve(); }
        })
      };
      const tasks: Promise<void>[] = [];
      for (let i = 0; i < items.length; i++) {
        const entry = (items[i] as any).webkitGetAsEntry?.();
        if (entry) tasks.push(traverse(entry));
      }
      await Promise.all(tasks);
      if (filesFromDirs.length) {
        const all = new DataTransfer();
        filesFromDirs.forEach(f => all.items.add(f));
        handleFileChange(all.files);
        return;
      }
    }
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
        onClick={() => inputRef.current?.click()}
      >
        {/* Keep the input present in the accessibility tree for reliable triggering */}
        <input
          type="file"
          multiple
          id={fileInputId}
          className="sr-only"
          ref={inputRef}
          onChange={(e: ChangeEvent<HTMLInputElement>) => e.target.files && handleFileChange(e.target.files)}
          accept={acceptedFormats}
        />
        {/* Hidden directory input to select folders */}
        <input
          type="file"
          multiple
          className="sr-only"
          ref={dirInputRef}
          onChange={(e: ChangeEvent<HTMLInputElement>) => e.target.files && handleFileChange(e.target.files)}
          // @ts-ignore - nonstandard attributes for folder selection
          webkitdirectory=""
          // @ts-ignore
          directory=""
          id={dirInputId}
        />
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <UploadCloud className="w-12 h-12 text-primary/60" />
          <p className="font-headline font-semibold text-foreground">Drag & drop files here, or click to select</p>
          <p className="text-xs font-body text-muted-foreground/80">{acceptedFormats}</p>
          <div className="mt-1">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" type="button" onClick={(e)=>{ e.stopPropagation(); try { inputRef.current?.click() } catch {} }}>
                Select Files
              </Button>
              {/* Provide label/htmlFor as a robust fallback in addition to programmatic click */}
              <label htmlFor={dirInputId} onClick={(e)=> e.stopPropagation()} className="cursor-pointer">
                <Button variant="outline" size="sm" type="button">Select Folder</Button>
              </label>
            </div>
          </div>
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
