import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { scriptsApi } from '../api/scripts';
import type { ApiError } from '@/types';

interface ScriptUploadModalProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    initialTitle?: string;
}

interface UploadFormData {
    title: string;
    file: FileList;
}

export const ScriptUploadModal = ({ projectId, isOpen, onClose, initialTitle }: ScriptUploadModalProps) => {
    const queryClient = useQueryClient();
    const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<UploadFormData>();
    const [uploadError, setUploadError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setValue('title', initialTitle || '');
        } else {
            // モーダルが閉じたらリセット（必要なら）
            // reset(); // フォーム全体のリセットは閉じた時か送信後か
        }
    }, [isOpen, initialTitle, setValue]);

    const uploadMutation = useMutation({
        mutationFn: (data: UploadFormData) => {
            const formData = new FormData();
            formData.append('script_file', data.file[0]);
            formData.append('title', data.title);
            formData.append('is_public', 'false'); // Default to false
            return scriptsApi.uploadScript(projectId, formData);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['scripts', projectId] });
            reset();
            onClose();
        },
        onError: (error: ApiError) => {
            console.error('Upload failed:', error);
            console.error('Error Response Data:', error.response?.data);

            const detail = error.response?.data?.detail;
            let errorMessage = 'Upload failed';

            if (typeof detail === 'string') {
                errorMessage = detail;
            } else if (Array.isArray(detail)) {
                // Pydantic validation error list
                errorMessage = detail.map((err: { loc: (string | number)[]; msg: string }) => `${err.loc.join('.')}: ${err.msg}`).join('\n');
            } else if (typeof detail === 'object') {
                errorMessage = JSON.stringify(detail);
            }

            setUploadError(errorMessage);
        }
    });

    const onSubmit = (data: UploadFormData) => {
        setUploadError(null);
        uploadMutation.mutate(data);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>

                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                <div className="relative z-50 inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                    <div>
                        <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                            Upload Script (.fountain)
                        </h3>
                        {uploadError && (
                            <div className="mt-2 p-2 bg-red-50 text-red-700 text-sm rounded">
                                {uploadError}
                            </div>
                        )}
                        <div className="mt-2">
                            <form onSubmit={handleSubmit(onSubmit)}>
                                <div className="space-y-4">
                                    <div>
                                        <label htmlFor="title" className="block text-sm font-medium text-gray-700">Title</label>
                                        <input
                                            type="text"
                                            id="title"
                                            {...register('title', { required: 'Title is required' })}
                                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                        />
                                        {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
                                    </div>
                                    <div>
                                        <label htmlFor="file" className="block text-sm font-medium text-gray-700">Fountain File</label>
                                        <input
                                            type="file"
                                            id="file"
                                            accept=".fountain"
                                            {...register('file', {
                                                required: 'File is required',
                                                validate: {
                                                    isFountain: files => files?.[0]?.name.endsWith('.fountain') || 'Only .fountain files are allowed'
                                                }
                                            })}
                                            className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                                        />
                                        {errors.file && <p className="mt-1 text-sm text-red-600">{errors.file.message}</p>}
                                    </div>
                                </div>
                                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                                    <button
                                        type="submit"
                                        disabled={uploadMutation.isPending}
                                        className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm disabled:opacity-50"
                                    >
                                        {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={onClose}
                                        className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
