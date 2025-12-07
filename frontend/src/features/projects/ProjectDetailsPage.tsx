import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from './api/projects';

export const ProjectDetailsPage = () => {
    const { projectId } = useParams<{ projectId: string }>();


    const { data: project, isLoading, error } = useQuery({
        queryKey: ['projects', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error || !project) {
        return (
            <div className="flex flex-col items-center justify-center h-full">
                <h2 className="text-xl font-bold text-gray-900">Project not found</h2>
                <Link to="/dashboard" className="text-indigo-600 hover:text-indigo-500 mt-4">
                    Return to Dashboard
                </Link>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h2>
                <div className="text-sm text-gray-500 space-y-1">
                    <p>Created: {new Date(project.created_at).toLocaleDateString()}</p>
                    <p>Role: <span className="capitalize">{project.role}</span></p>
                </div>
                <div className="mt-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">
                        {project.description || 'No description provided.'}
                    </p>
                </div>
            </div>

            {/* Quick Stats or Activity Stream could go here */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-indigo-500">
                    <h3 className="font-semibold text-gray-900">Scripts</h3>
                    <p className="mt-2 text-3xl font-bold text-gray-700">-</p>
                    <p className="text-sm text-gray-500">Uploaded scripts</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-green-500">
                    <h3 className="font-semibold text-gray-900">Cast</h3>
                    <p className="mt-2 text-3xl font-bold text-gray-700">-</p>
                    <p className="text-sm text-gray-500">Members & Characters</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow border-t-4 border-purple-500">
                    <h3 className="font-semibold text-gray-900">Schedule</h3>
                    <p className="mt-2 text-3xl font-bold text-gray-700">-</p>
                    <p className="text-sm text-gray-500">Upcoming rehearsals</p>
                </div>
            </div>
        </div>
    );
};
