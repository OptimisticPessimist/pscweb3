import { useParams, Outlet, Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from './api/projects';

export const ProjectDetailsPage = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const location = useLocation();

    const { data: project, isLoading, error } = useQuery({
        queryKey: ['projects', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    if (isLoading) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error || !project) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-xl font-bold text-gray-900">Project not found</h2>
                    <Link to="/dashboard" className="text-indigo-600 hover:text-indigo-500 mt-4 inline-block">
                        Return to Dashboard
                    </Link>
                </div>
            </div>
        );
    }

    const navigation = [
        { name: 'Scripts', path: `/projects/${projectId}/scripts` },
        { name: 'Scene Charts', path: `/projects/${projectId}/scene-charts` },
        { name: 'Castings', path: `/projects/${projectId}/castings` },
        { name: 'Schedules', path: `/projects/${projectId}/schedules` },
        { name: 'Settings', path: `/projects/${projectId}/settings` },
    ];

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6 md:flex md:items-center md:justify-between">
                        <div className="flex-1 min-w-0">
                            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                                {project.name}
                            </h2>
                            <p className="mt-1 text-sm text-gray-500 truncate">{project.description}</p>
                        </div>
                        <div className="mt-4 flex md:mt-0 md:ml-4">
                            <Link
                                to="/dashboard"
                                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                Back to Dashboard
                            </Link>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="mt-4 -mb-px flex space-x-8 overflow-x-auto">
                        {navigation.map((item) => {
                            const isActive = location.pathname.startsWith(item.path);
                            return (
                                <Link
                                    key={item.name}
                                    to={item.path}
                                    className={`
                                        whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm
                                        ${isActive
                                            ? 'border-indigo-500 text-indigo-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }
                                    `}
                                >
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                {/* Child routes will be rendered here */}
                <div className="px-4 py-6 sm:px-0">
                    <Outlet />

                    {/* Default content if no child route matched (e.g. at /projects/:id) */}
                    {location.pathname === `/projects/${projectId}` && (
                        <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">Welcome to {project.name}</h3>
                            <p className="mt-2 text-gray-500">Select a tab to manage your project resources.</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};
