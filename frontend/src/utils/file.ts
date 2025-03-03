export const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const handleVideoPlay = async (url: string): Promise<void> => {
    try {
        const videoElement = document.createElement('video');
        videoElement.src = url;
        videoElement.controls = true;
        videoElement.style.width = '100%';
        videoElement.style.maxHeight = '80vh';
        
        const dialog = document.createElement('dialog');
        dialog.style.padding = '0';
        dialog.style.border = 'none';
        dialog.style.borderRadius = '8px';
        dialog.style.backgroundColor = '#1a1a1a';
        dialog.style.maxWidth = '90vw';
        dialog.style.maxHeight = '90vh';
        
        dialog.appendChild(videoElement);
        document.body.appendChild(dialog);
        
        dialog.showModal();
        
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.close();
            }
        });
        
        dialog.addEventListener('close', () => {
            document.body.removeChild(dialog);
        });
        
        await videoElement.play();
    } catch (error) {
        console.error('Error playing video:', error);
    }
};

export const getFileTypeIcon = (file: { type: string; isVideo?: boolean }): string => {
    if (file.type === 'folder') return 'folder';
    if (file.isVideo) return 'video';
    return 'file';
};

export const calculateFolderStats = (files: { size?: number }[]): { totalSize: number; fileCount: number } => {
    return files.reduce((acc, file) => {
        if (file.size) {
            acc.totalSize += file.size;
            acc.fileCount += 1;
        }
        return acc;
    }, { totalSize: 0, fileCount: 0 });
}; 