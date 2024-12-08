export interface S3Object {
  Key: string;
  Type: 'prefix' | 'object';
  Size?: number;
  LastModified?: string;
  thumbnailUrl?: string;
  previewUrl?: string;
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
}

export interface FileWithPath extends File {
  path: string;
  webkitdirectory?: boolean;
}

export interface S3ListResponse {
  files: S3Object[];
  continuationToken?: string;
}
