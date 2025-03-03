export interface FileInfo {
  name: string;
  type: 'file' | 'folder';
  size?: number;
  lastModified?: string;
  path: string;
  extension?: string;
  isVideo?: boolean;
  thumbnailUrl?: string;
  previewUrl?: string;
  totalSize?: number;  // Total size for folders
  fileCount?: number;  // Number of files in folder
  isProcessing?: boolean;
  error?: string;
}

export interface S3Object {
  Key: string;
  Size?: number;
  LastModified?: string;
  Type?: 'prefix' | 'object';
  FileCount?: number;
  TotalSize?: number;
  thumbnailUrl?: string;
  previewUrl?: string;
  isProcessing?: boolean;
  error?: string;
}

export interface FileWithPath extends File {
  path: string;
  webkitdirectory?: boolean;
}

export interface S3ListResponse {
  files: S3Object[];
  continuationToken?: string;
}
