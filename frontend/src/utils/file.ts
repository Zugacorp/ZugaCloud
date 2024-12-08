export const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const handleVideoPlay = async (url: string): Promise<void> => {
    try {
        if (window.electron?.shell?.openExternal) {
            await window.electron.shell.openExternal(url);
        } else {
            window.open(url, '_blank');
        }
    } catch (error) {
        console.error('Error playing video:', error);
    }
}; 