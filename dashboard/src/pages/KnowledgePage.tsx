import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Trash2, FileText, Loader2 } from 'lucide-react';
import { useRef, useState } from 'react';
import { knowledgeApi } from '../api';

export function KnowledgePage() {
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isUploading, setIsUploading] = useState(false);

    const { data, isLoading } = useQuery({
        queryKey: ['knowledge'],
        queryFn: knowledgeApi.list,
    });

    const deleteMutation = useMutation({
        mutationFn: knowledgeApi.delete,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledge'] }),
    });

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        try {
            await knowledgeApi.upload(file);
            queryClient.invalidateQueries({ queryKey: ['knowledge'] });
        } catch (error) {
            alert('Upload failed. Please try again.');
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Knowledge Base</h1>
                    <p className="text-slate-500">Upload documents to train your AI assistant</p>
                </div>
                <div>
                    <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleUpload}
                        accept=".pdf,.docx,.txt,.csv,.json"
                        className="hidden"
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors disabled:opacity-50"
                    >
                        {isUploading ? (
                            <Loader2 size={20} className="animate-spin" />
                        ) : (
                            <Upload size={20} />
                        )}
                        {isUploading ? 'Uploading...' : 'Upload Document'}
                    </button>
                </div>
            </div>

            {/* Upload hint */}
            <div className="bg-violet-50 border border-violet-100 rounded-xl p-4 text-sm text-violet-700">
                <strong>Supported formats:</strong> PDF, DOCX, TXT, CSV, JSON. Max file size: 10MB.
            </div>

            {/* Documents table */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <table className="w-full">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Document</th>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Type</th>
                            <th className="text-right py-3 px-6 text-sm font-medium text-slate-500">Size</th>
                            <th className="text-right py-3 px-6 text-sm font-medium text-slate-500">Chunks</th>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Status</th>
                            <th className="text-left py-3 px-6 text-sm font-medium text-slate-500">Uploaded</th>
                            <th className="py-3 px-6"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {data?.documents.map((doc) => (
                            <tr key={doc.id} className="border-t border-slate-100 hover:bg-slate-50">
                                <td className="py-4 px-6">
                                    <div className="flex items-center gap-3">
                                        <FileText className="text-slate-400" size={20} />
                                        <span className="font-medium text-slate-900">{doc.filename}</span>
                                    </div>
                                </td>
                                <td className="py-4 px-6 text-slate-600">{doc.file_type}</td>
                                <td className="py-4 px-6 text-right text-slate-600">
                                    {(doc.file_size / 1024).toFixed(1)} KB
                                </td>
                                <td className="py-4 px-6 text-right text-slate-600">{doc.chunk_count}</td>
                                <td className="py-4 px-6">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${doc.status === 'processed'
                                            ? 'bg-emerald-100 text-emerald-800'
                                            : doc.status === 'processing'
                                                ? 'bg-amber-100 text-amber-800'
                                                : 'bg-slate-100 text-slate-800'
                                        }`}>
                                        {doc.status}
                                    </span>
                                </td>
                                <td className="py-4 px-6 text-slate-500 text-sm">
                                    {new Date(doc.uploaded_at).toLocaleDateString()}
                                </td>
                                <td className="py-4 px-6">
                                    <button
                                        onClick={() => {
                                            if (confirm('Delete this document? This cannot be undone.')) {
                                                deleteMutation.mutate(doc.id);
                                            }
                                        }}
                                        className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {(data?.documents.length ?? 0) === 0 && (
                            <tr>
                                <td colSpan={7} className="py-12 text-center text-slate-500">
                                    No documents uploaded yet. Upload your first document to get started.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
