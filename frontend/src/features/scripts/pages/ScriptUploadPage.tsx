import React, { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { scriptsApi } from '../api/scripts';
import { Upload, X, FileText } from 'lucide-react';

export const ScriptUploadPage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [title, setTitle] = useState('');
    const [isPublic, setIsPublic] = useState(false);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const uploadedFile = acceptedFiles[0];
            setFile(uploadedFile);
            // Auto-fill title from filename if empty
            if (!title) {
                setTitle(uploadedFile.name.replace('.fountain', ''));
            }
        }
    }, [title]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/plain': ['.fountain'],
        },
        maxFiles: 1,
    });

    const uploadMutation = useMutation({
        mutationFn: (formData: FormData) => scriptsApi.uploadScript(projectId!, formData),
        onSuccess: () => {
            navigate(`/projects/${projectId}/scripts`);
        },
        onError: (error: any) => {
            alert(`Upload failed: ${error.message || 'Unknown error'}`);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', title);
        formData.append('is_public', String(isPublic));

        uploadMutation.mutate(formData);
    };

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Upload Script</h2>
                <p className="mt-1 text-sm text-gray-500">
                    Upload a .fountain file to add a new script or update an existing one.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 shadow sm:rounded-md">
                <div>
                    <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                        Script Title
                    </label>
                    <div className="mt-1">
                        <input
                            type="text"
                            id="title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                            placeholder="e.g. My Great Play"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700">Script File (.fountain)</label>
                    <div
                        {...getRootProps()}
                        className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md transition-colors ${isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400'
                            }`}
                    >
                        <input {...getInputProps()} />
                        <div className="space-y-1 text-center">
                            {file ? (
                                <div className="flex flex-col items-center">
                                    <FileText className="h-12 w-12 text-indigo-500" />
                                    <div className="flex items-center text-sm text-gray-600 mt-2">
                                        <span className="font-medium">{file.name}</span>
                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setFile(null);
                                            }}
                                            className="ml-2 text-red-500 hover:text-red-700"
                                        >
                                            <X className="h-4 w-4" />
                                        </button>
                                    </div>
                                    <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                            ) : (
                                <>
                                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                                    <div className="flex text-sm text-gray-600 justify-center">
                                        <span className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                                            <span>Upload a file</span>
                                        </span>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs text-gray-500">.fountain files only</p>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex items-start">
                    <div className="flex items-center h-5">
                        <input
                            id="is_public"
                            type="checkbox"
                            checked={isPublic}
                            onChange={(e) => setIsPublic(e.target.checked)}
                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                        />
                    </div>
                    <div className="ml-3 text-sm">
                        <label htmlFor="is_public" className="font-medium text-gray-700">
                            Public
                        </label>
                        <p className="text-gray-500">Allow members to view even if not authenticated (if enabled globally).</p>
                    </div>
                </div>

                <div className="flex justify-end space-x-3">
                    <button
                        type="button"
                        onClick={() => navigate(`/projects/${projectId}/scripts`)}
                        className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={!file || !title || uploadMutation.isPending}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {uploadMutation.isPending ? 'Uploading...' : 'Upload Script'}
                    </button>
                </div>
            </form>
        </div>
    );
};
