import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../api/projects';
import { ProjectDetailsHeader } from '../components/ProjectDetailsHeader';
import { InvitationPanel } from '../components/InvitationPanel';

export const ProjectSettingsPage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    const [editingMember, setEditingMember] = useState<string | null>(null);

    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    const { data: members, isLoading } = useQuery({
        queryKey: ['projectMembers', projectId],
        queryFn: () => projectsApi.getProjectMembers(projectId!),
        enabled: !!projectId,
    });

    const updateMemberMutation = useMutation({
        mutationFn: ({ userId, role, defaultStaffRole, displayName }: { userId: string; role: string; defaultStaffRole?: string | null, displayName?: string | null }) =>
            projectsApi.updateMemberRole(projectId!, userId, role, defaultStaffRole, displayName),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projectMembers', projectId] });
            setEditingMember(null);
        },
    });

    const deleteMemberMutation = useMutation({
        mutationFn: (userId: string) => projectsApi.deleteMember(projectId!, userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projectMembers', projectId] });
            alert('Member removed successfully.');
        },
        onError: (error: any) => {
            alert(`Failed to remove member: ${error.message || 'Unknown error'}`);
        }
    });

    if (isLoading || !project) return <div>Loading...</div>;

    const isOwner = project.role === 'owner';

    return (
        <div className="space-y-6">
            <ProjectDetailsHeader project={project} />

            <div className="bg-white shadow sm:rounded-lg mb-6">
                <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">General Settings</h3>
                    <div className="mt-5 max-w-xl">
                        {isOwner ? (
                            <ProjectUpdateForm project={project} projectId={projectId!} queryClient={queryClient} />
                        ) : (
                            <div className="space-y-4">
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Project Name</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{project.name}</dd>
                                </div>
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Description</dt>
                                    <dd className="mt-1 text-sm text-gray-900">{project.description || 'No description'}</dd>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="bg-white shadow sm:rounded-lg mb-6">
                <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Project Members & Staff Roles</h3>
                    <div className="mt-5">
                        <div className="flex flex-col">
                            <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                                <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                                    <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        User
                                                    </th>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        Screen Name
                                                    </th>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        Access Role
                                                    </th>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        Default Staff Role (Position)
                                                    </th>
                                                    <th scope="col" className="relative px-6 py-3">
                                                        <span className="sr-only">Edit</span>
                                                    </th>
                                                    <th scope="col" className="relative px-6 py-3">
                                                        <span className="sr-only">Delete</span>
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {members?.map((member) => (
                                                    <tr key={member.user_id}>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            <div className="flex items-center">
                                                                <div className="text-sm font-medium text-gray-900">
                                                                    {member.discord_username}
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            {editingMember === member.user_id ? (
                                                                <input
                                                                    type="text"
                                                                    defaultValue={member.display_name || ''}
                                                                    id={`display-name-${member.user_id}`}
                                                                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                                                    placeholder="Display Name"
                                                                />
                                                            ) : (
                                                                <div className="text-sm text-gray-900">
                                                                    {member.display_name || <span className="text-gray-400 italic">None</span>}
                                                                </div>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            {editingMember === member.user_id ? (
                                                                <select
                                                                    defaultValue={member.role}
                                                                    id={`role-${member.user_id}`}
                                                                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                                                                >
                                                                    <option value="owner">Owner</option>
                                                                    <option value="editor">Editor</option>
                                                                    <option value="viewer">Viewer</option>
                                                                </select>
                                                            ) : (
                                                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${member.role === 'owner' ? 'bg-purple-100 text-purple-800' :
                                                                    member.role === 'editor' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                                                    }`}>
                                                                    {member.role}
                                                                </span>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                            {editingMember === member.user_id ? (
                                                                <input
                                                                    type="text"
                                                                    defaultValue={member.default_staff_role || ''}
                                                                    id={`staff-role-${member.user_id}`}
                                                                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                                                    placeholder="e.g. Director, Lighting"
                                                                />
                                                            ) : (
                                                                member.default_staff_role || <span className="text-gray-400 italic">None</span>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                            {isOwner && (
                                                                editingMember === member.user_id ? (
                                                                    <div className="space-x-2">
                                                                        <button
                                                                            onClick={() => {
                                                                                const roleSelect = document.getElementById(`role-${member.user_id}`) as HTMLSelectElement;
                                                                                const staffInput = document.getElementById(`staff-role-${member.user_id}`) as HTMLInputElement;
                                                                                const displayNameInput = document.getElementById(`display-name-${member.user_id}`) as HTMLInputElement;
                                                                                updateMemberMutation.mutate({
                                                                                    userId: member.user_id,
                                                                                    role: roleSelect.value,
                                                                                    defaultStaffRole: staffInput.value || null,
                                                                                    displayName: displayNameInput.value || null
                                                                                });
                                                                            }}
                                                                            className="text-indigo-600 hover:text-indigo-900"
                                                                        >
                                                                            Save
                                                                        </button>
                                                                        <button
                                                                            onClick={() => setEditingMember(null)}
                                                                            className="text-gray-600 hover:text-gray-900"
                                                                        >
                                                                            Cancel
                                                                        </button>
                                                                    </div>
                                                                ) : (
                                                                    <button
                                                                        onClick={() => setEditingMember(member.user_id)}
                                                                        className="text-indigo-600 hover:text-indigo-900"
                                                                    >
                                                                        Edit
                                                                    </button>
                                                                )
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                            {isOwner && member.role !== 'owner' && (
                                                                <button
                                                                    onClick={() => {
                                                                        if (window.confirm(`Are you sure you want to remove ${member.discord_username}?`)) {
                                                                            deleteMemberMutation.mutate(member.user_id);
                                                                        }
                                                                    }}
                                                                    className="text-red-600 hover:text-red-900 ml-4"
                                                                >
                                                                    Remove
                                                                </button>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {isOwner && (
                <InvitationPanel projectId={projectId!} />
            )}
        </div>
    );
};

const ProjectUpdateForm: React.FC<{ project: any, projectId: string, queryClient: any }> = ({ project, projectId, queryClient }) => {
    const [name, setName] = useState(project.name);
    const [description, setDescription] = useState(project.description || '');
    const [webhookUrl, setWebhookUrl] = useState(project.discord_webhook_url || '');
    const [channelId, setChannelId] = useState(project.discord_channel_id || '');

    const updateProjectMutation = useMutation({
        mutationFn: (data: any) => projectsApi.updateProject(projectId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['project', projectId] });
            alert('Project settings updated.');
        },
        onError: (error: any) => {
            alert(`Failed to update settings: ${error.message || 'Unknown error'}`);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        updateProjectMutation.mutate({
            name,
            description,
            discord_webhook_url: webhookUrl,
            discord_channel_id: channelId
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">Project Name</label>
                <input
                    type="text"
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                />
            </div>
            <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                />
            </div>

            <div className="pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Discord Integration</h4>
                <div className="space-y-4">
                    <div>
                        <label htmlFor="webhookUrl" className="block text-sm font-medium text-gray-700">Webhook URL</label>
                        <div className="mt-1 flex rounded-md shadow-sm">
                            <input
                                type="text"
                                id="webhookUrl"
                                value={webhookUrl}
                                onChange={(e) => setWebhookUrl(e.target.value)}
                                className="flex-1 block w-full min-w-0 sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                                placeholder="https://discord.com/api/webhooks/..."
                            />
                        </div>
                        <p className="mt-1 text-xs text-gray-500">For sending notifications (script uploads, milestones)</p>
                    </div>
                    <div>
                        <label htmlFor="channelId" className="block text-sm font-medium text-gray-700">Channel ID</label>
                        <input
                            type="text"
                            id="channelId"
                            value={channelId}
                            onChange={(e) => setChannelId(e.target.value)}
                            className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="123456789012345678"
                        />
                        <p className="mt-1 text-xs text-gray-500">For attendance check mentions and event linking</p>
                    </div>
                </div>
            </div>

            <div className="pt-4">
                <button
                    type="submit"
                    className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    disabled={updateProjectMutation.isPending}
                >
                    {updateProjectMutation.isPending ? 'Saving...' : 'Save Settings'}
                </button>
            </div>
        </form>
    );
};
