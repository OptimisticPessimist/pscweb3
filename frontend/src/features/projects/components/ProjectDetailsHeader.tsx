import React from 'react';
import type { Project } from '@/types';

interface ProjectDetailsHeaderProps {
    project: Project;
}

export const ProjectDetailsHeader: React.FC<ProjectDetailsHeaderProps> = ({ project }) => {
    return (
        <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{project.name}</h2>
            <div className="text-sm text-gray-500 space-y-1">
                <p>Created: {new Date(project.created_at).toLocaleDateString()}</p>
                <p>Role: <span className="capitalize">{project.role}</span></p>
            </div>
            <div className="mt-4">
                <p className="text-gray-700 whitespace-pre-wrap">
                    {project.description || 'No description provided.'}
                </p>
            </div>
        </div>
    );
};
