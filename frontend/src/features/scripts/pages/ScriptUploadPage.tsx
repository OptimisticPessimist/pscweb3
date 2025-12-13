import React, { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import { scriptsApi } from '../api/scripts';
import { Upload, X, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ScriptUploadPage: React.FC = () => {
    const { t } = useTranslation();
    const { projectId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [title, setTitle] = useState('');
    const [author, setAuthor] = useState('');
    const [isPublic, setIsPublic] = useState(false);
    const [publicTerms, setPublicTerms] = useState('');
    const [publicContact, setPublicContact] = useState('');

    const extractMetadata = async (file: File) => {
        const text = await file.text();
        const lines = text.split('\n');
        let extractedTitle = '';
        let extractedAuthor = '';

        // Read first 20 lines for metadata
        for (let i = 0; i < Math.min(lines.length, 20); i++) {
            const line = lines[i].trim();
            if (line.startsWith('Title:')) {
                extractedTitle = line.substring(6).trim();
            } else if (line.startsWith('Author:')) {
                extractedAuthor = line.substring(7).trim();
            } else if (line.startsWith('Credit:') && !extractedAuthor) {
                // Fallback if Author not found
            }
        }
        return { extractedTitle, extractedAuthor };
    };

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const uploadedFile = acceptedFiles[0];
            setFile(uploadedFile);

            // Extract metadata
            const { extractedTitle, extractedAuthor } = await extractMetadata(uploadedFile);

            // Auto-fill title from metadata or filename if empty
            if (!title) {
                if (extractedTitle) {
                    setTitle(extractedTitle);
                } else {
                    setTitle(uploadedFile.name.replace('.fountain', ''));
                }
            }

            // Auto-fill author if empty
            if (!author && extractedAuthor) {
                setAuthor(extractedAuthor);
            }
        }
    }, [title, author]);

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
        onError: (error: Error) => {
            alert(`Upload failed: ${error.message || 'Unknown error'}`);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', title);
        if (author) {
            formData.append('author', author);
        }
        formData.append('is_public', String(isPublic));
        if (isPublic) {
            if (publicTerms) formData.append('public_terms', publicTerms);
            if (publicContact) formData.append('public_contact', publicContact);
        }

        uploadMutation.mutate(formData);
    };

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <div>
                <h2 className="text-2xl font-bold text-gray-900">{t('script.uploadTitle')}</h2>
                <p className="mt-1 text-sm text-gray-500">
                    {t('script.uploadDescription')}
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 shadow sm:rounded-md">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <div className="sm:col-span-2">
                        <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                            {t('script.form.titleLabel') || 'Script Title'}
                        </label>
                        <div className="mt-1">
                            <input
                                type="text"
                                id="title"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                placeholder={t('script.form.titlePlaceholder') || 'e.g. My Great Play'}
                            />
                        </div>
                    </div>

                    <div className="sm:col-span-2">
                        <label htmlFor="author" className="block text-sm font-medium text-gray-700">
                            {t('script.form.authorLabel') || 'Author'}
                        </label>
                        <div className="mt-1">
                            <input
                                type="text"
                                id="author"
                                value={author}
                                onChange={(e) => setAuthor(e.target.value)}
                                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                placeholder={t('script.form.authorPlaceholder') || 'e.g. William Shakespeare'}
                            />
                        </div>
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700">{t('script.form.fileLabel') || 'Script File (.fountain)'}</label>
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
                                            <span>{t('script.form.uploadFile') || 'Upload a file'}</span>
                                        </span>
                                        <p className="pl-1">{t('script.form.dragDrop') || 'or drag and drop'}</p>
                                    </div>
                                    <p className="text-xs text-gray-500">{t('script.form.fileType') || '.fountain files only'}</p>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-md space-y-4">
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
                                {t('script.form.publicLabel') || 'Public'}
                            </label>
                            <p className="text-gray-500">{t('script.form.publicDescription') || 'Allow anyone to view this script.'}</p>
                        </div>
                    </div>

                    {isPublic && (
                        <div className="pl-7 grid grid-cols-1 gap-4">
                            <div>
                                <label htmlFor="publicTerms" className="block text-sm font-medium text-gray-700">
                                    {t('script.form.usageTerms') || "Usage Terms"}
                                </label>
                                <div className="mt-1">
                                    <textarea
                                        id="publicTerms"
                                        rows={3}
                                        value={publicTerms}
                                        onChange={(e) => setPublicTerms(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                        placeholder={t('script.form.usageTermsPlaceholder') || "e.g. Please contact for performance rights."}
                                    />
                                </div>
                            </div>
                            <div>
                                <label htmlFor="publicContact" className="block text-sm font-medium text-gray-700">
                                    {t('script.form.contactInfo') || "Contact Info"}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="text"
                                        id="publicContact"
                                        value={publicContact}
                                        onChange={(e) => setPublicContact(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                        placeholder={t('script.form.contactPlaceholder') || "e.g. email@example.com"}
                                    />
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex justify-end space-x-3">
                    <button
                        type="button"
                        onClick={() => navigate(`/projects/${projectId}/scripts`)}
                        className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        {t('common.cancel')}
                    </button>
                    <button
                        type="submit"
                        disabled={!file || !title || uploadMutation.isPending}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {uploadMutation.isPending ? t('script.uploading') : t('script.uploadAction')}
                    </button>
                </div>
            </form>
        </div>
    );
};
