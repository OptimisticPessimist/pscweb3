import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi } from './api/dashboard';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

export const DashboardPage = () => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { data: projects, isLoading, isError, error } = useQuery({
        queryKey: ['projects'],
        queryFn: dashboardApi.getProjects,
    });

    // 公開プロジェクトは制限（2つまで）のカウントに含めない
    const ownedProjectCount = projects?.filter(p => p.role === 'owner' && !p.is_public).length || 0;
    const isProjectLimitReached = ownedProjectCount >= 2;
    const projectLimitMessage = isProjectLimitReached ? t('dashboard.projectLimit') : undefined;

    const [createError, setCreateError] = useState<string | null>(null);

    const createProjectMutation = useMutation({
        mutationFn: (data: { name: string; description: string; is_public?: boolean }) => {
            console.log("MutationFn called with:", data);
            return dashboardApi.createProject(data);
        },
        onMutate: () => console.log("onMutate fired"),
        onSuccess: (data) => {
            console.log("onSuccess fired:", data);
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            setIsModalOpen(false);
            reset(); // Form reset
            setCreateError(null);
        },
        onError: (error) => {
            console.error("onError fired:", error);
            setCreateError(error instanceof Error ? error.message : t('dashboard.failedToDeleteProject'));
        }
    });

    // Delete Mutation State
    const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);

    const deleteProjectMutation = useMutation({
        mutationFn: (id: string) => dashboardApi.deleteProject(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            setDeleteProjectId(null);
        },
        onError: (error) => {
            console.error("Delete failed:", error);
            alert(t('dashboard.failedToDeleteProject'));
        }
    });

    const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<{ name: string; description: string; is_public: boolean }>();

    const onSubmit = (data: { name: string; description: string; is_public: boolean }) => {
        if (isProjectLimitReached && !data.is_public) {
            setCreateError(t('dashboard.projectLimit'));
            return;
        }
        setCreateError(null);
        createProjectMutation.mutate(data);
    };

    const handleDeleteClick = (e: React.MouseEvent, id: string) => {
        e.preventDefault(); // Prevent Link navigation
        e.stopPropagation();
        setDeleteProjectId(id);
    };

    const confirmDelete = () => {
        if (deleteProjectId) {
            deleteProjectMutation.mutate(deleteProjectId);
        }
    };

    return (
        <div className="min-h-full">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.projects')}</h1>
                <button
                    onClick={() => {
                        if (!isProjectLimitReached) {
                            setIsModalOpen(true);
                            setCreateError(null);
                        }
                    }}
                    disabled={isProjectLimitReached}
                    title={projectLimitMessage}
                    className={`flex items-center px-4 py-2 text-white rounded-md shadow-sm transition-colors ${isProjectLimitReached
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-indigo-600 hover:bg-indigo-700'
                        }`}
                >
                    <span className="mr-2">+</span> {t('dashboard.newProject')}
                </button>
            </div>

            {isError && (
                <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
                    <p className="font-bold">{t('dashboard.errorLoadingProjects')}</p>
                    <p>{error instanceof Error ? error.message : t('dashboard.unknownError')}</p>
                </div>
            )}

            {/* Project List */}
            {isLoading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
                </div>
            ) : projects && projects.length > 0 ? (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {projects.map((project) => (
                        <Link
                            key={project.id}
                            to={`/projects/${project.id}`}
                            className="block bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-200 cursor-pointer group relative"
                        >
                            <div className="px-4 py-5 sm:p-6 group-hover:bg-gray-50">
                                <div className="flex justify-between items-start">
                                    <h3 className="text-lg leading-6 font-medium text-gray-900 truncate flex-1">
                                        {project.name}
                                    </h3>
                                    {project.role === 'owner' && (
                                        <button
                                            onClick={(e) => handleDeleteClick(e, project.id)}
                                            className="text-gray-400 hover:text-red-600 p-1 z-10"
                                            title="Delete Project"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    )}
                                </div>
                                <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                                    {project.description || t('dashboard.noDescription')}
                                </p>
                                <div className="mt-4 flex items-center justify-between">
                                    <div className="flex space-x-2">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${project.role === 'owner' ? 'bg-indigo-100 text-indigo-800' : 'bg-green-100 text-green-800'
                                            }`}>
                                            {project.role}
                                        </span>
                                        {project.is_public && (
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                {t('common.public') || 'Public'}
                                            </span>
                                        )}
                                    </div>
                                    <span className="text-xs text-gray-400">
                                        {new Date(project.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            ) : !isError && (
                <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
                    <svg
                        className="mx-auto h-12 w-12 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                    >
                        <path
                            vectorEffect="non-scaling-stroke"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                        />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">{t('dashboard.noProjects')}</h3>
                    <p className="mt-1 text-sm text-gray-500">{t('dashboard.noProjectsMessage')}</p>
                    <div className="mt-6">
                        <button
                            onClick={() => {
                                setIsModalOpen(true);
                                setCreateError(null);
                            }}
                            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                        >
                            {t('dashboard.createNewProject')}
                        </button>
                        {isProjectLimitReached && (
                            <p className="mt-2 text-sm text-red-500">{projectLimitMessage}</p>
                        )}
                    </div>
                </div>
            )}

            {/* Create Project Modal */}
            {isModalOpen && (
                <div className="fixed z-50 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setIsModalOpen(false)}></div>

                        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6 relative z-10">
                            <div>
                                <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                                    {t('dashboard.createNewProject')}
                                </h3>
                                <div className="mt-2">
                                    {createError && (
                                        <div className="mb-4 p-2 bg-red-50 text-red-700 rounded text-sm">
                                            {createError}
                                        </div>
                                    )}
                                    <form onSubmit={handleSubmit(onSubmit)}>
                                        <div className="space-y-4">
                                            <div>
                                                <label htmlFor="name" className="block text-sm font-medium text-gray-700">{t('project.name')}</label>
                                                <input
                                                    type="text"
                                                    id="name"
                                                    {...register('name', { required: t('project.nameRequired') })}
                                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                    placeholder={t('project.enterProjectName')}
                                                />
                                                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
                                            </div>
                                            <div>
                                                <label htmlFor="description" className="block text-sm font-medium text-gray-700">{t('project.description')}</label>
                                                <textarea
                                                    id="description"
                                                    rows={3}
                                                    {...register('description')}
                                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                                />
                                            </div>
                                            <div className="flex items-start">
                                                <div className="flex items-center h-5">
                                                    <input
                                                        id="is_public"
                                                        type="checkbox"
                                                        {...register('is_public')}
                                                        className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                                    />
                                                </div>
                                                <div className="ml-3 text-sm">
                                                    <label htmlFor="is_public" className="font-medium text-gray-700">{t('dashboard.isPublic')}</label>
                                                    <p className="text-gray-500">{t('script.form.publicDescription')}</p>
                                                    {isProjectLimitReached && (
                                                        <p className="text-red-500 mt-1">{t('dashboard.projectLimit')}</p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                                            <button
                                                type="submit"
                                                disabled={createProjectMutation.isPending}
                                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm disabled:opacity-50"
                                            >
                                                {createProjectMutation.isPending ? t('dashboard.creating') : t('dashboard.create')}
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setIsModalOpen(false)}
                                                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                                            >
                                                {t('common.cancel')}
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteProjectId && (
                <div className="fixed z-50 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setDeleteProjectId(null)}></div>
                        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6 relative z-10">
                            <div className="sm:flex sm:items-start">
                                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                                    <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                </div>
                                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                                    <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">{t('dashboard.deleteProject')}</h3>
                                    <div className="mt-2">
                                        <p className="text-sm text-gray-500">
                                            {t('dashboard.deleteConfirmMessage')}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                                <button
                                    type="button"
                                    onClick={confirmDelete}
                                    disabled={deleteProjectMutation.isPending}
                                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    {deleteProjectMutation.isPending ? t('dashboard.deleting') : t('common.delete')}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setDeleteProjectId(null)}
                                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm"
                                >
                                    {t('common.cancel')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
