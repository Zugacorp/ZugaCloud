/// <reference types="react" />
/// <reference types="react-dom" />
/// <reference types="vite/client" />

declare namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }

declare module '*.svg' {
  const content: any;
  export default content;
}

declare module '*.png' {
  const content: any;
  export default content;
}

interface FileSystemHandle {
  kind: 'file' | 'directory';
  name: string;
}

interface FileSystemFileHandle extends FileSystemHandle {
  kind: 'file';
  getFile(): Promise<File>;
}

interface FileSystemDirectoryHandle extends FileSystemHandle {
  kind: 'directory';
  entries(): AsyncIterableIterator<[string, FileSystemHandle]>;
}

interface File {
  webkitRelativePath?: string;
  path?: string;
}