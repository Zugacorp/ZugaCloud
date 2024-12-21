export interface S3Object {
  Key: string;
  Type: 'prefix' | 'object';
  Size?: number;
  LastModified?: string;
  thumbnailUrl?: string;
  previewUrl?: string;
  TotalSize?: number;
  FileCount?: number;
}

export interface FileItem {
  name: string;
  type: 'folder' | 'file';
  size?: number;
  lastModified?: string;
  path: string;
  extension?: string;
  isVideo?: boolean;
  thumbnailUrl?: string;
  previewUrl?: string;
  totalSize?: number;
  fileCount?: number;
}

export interface FileWithPath extends File {
  path: string;
  webkitdirectory?: boolean;
}

export interface S3ListResponse {
  files: S3Object[];
  continuationToken?: string;
}
