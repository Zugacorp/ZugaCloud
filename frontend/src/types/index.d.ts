export {};

declare global {
  interface FileWithPath extends File {
    path: string;
    webkitdirectory?: boolean;
  }
} 