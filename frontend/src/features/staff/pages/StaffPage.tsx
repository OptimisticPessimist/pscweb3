import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/features/projects/api/projects';
import type { ProjectMember } from '@/types';
import { ProjectDetailsHeader } from '@/features/projects/components/ProjectDetailsHeader';

export const StaffPage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();
    const [editingMember, setEditingMember] = useState<string | null>(null);
    const [editRoleValue, setEditRoleValue] = useState<string>('');
    const [editDisplayName, setEditDisplayName] = useState<string>('');

    const { data: project, isLoading: isProjectLoading } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => projectsApi.getProject(projectId!),
        enabled: !!projectId,
    });

    const { data: members, isLoading: isMembersLoading } = useQuery({
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

    if (isProjectLoading || isMembersLoading || !project) return <div>Loading...</div>;

    const isOwner = project.role === 'owner';

    const startEditing = (memberId: string, currentRole?: string | null, currentDisplayName?: string | null) => {
        setEditingMember(memberId);
        setEditRoleValue(currentRole || '');
        setEditDisplayName(currentDisplayName || '');
    };

    const handleSave = (member: ProjectMember) => {
        updateMemberMutation.mutate({
            userId: member.user_id,
            role: member.role, // Keep existing access role
            defaultStaffRole: editRoleValue || null,
            displayName: editDisplayName || null
        });
    };

    return (
        <div className="space-y-6">
            <ProjectDetailsHeader project={project} />

            <div className="bg-white shadow sm:rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Staff List</h3>
                    <div className="mt-5">
                        <div className="flex flex-col">
                            <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                                <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                                    <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        Name
                                                    </th>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        Staff Role
                                                    </th>
                                                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                        Contact (Discord)
                                                    </th>
                                                    {isOwner && (
                                                        <th scope="col" className="relative px-6 py-3">
                                                            <span className="sr-only">Edit</span>
                                                        </th>
                                                    )}
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {members?.map((member) => (
                                                    <tr key={member.user_id}>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            <div className="flex items-center">
                                                                <div className="flex-shrink-0 h-10 w-10">
                                                                    <span className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-800 font-bold">
                                                                        {member.discord_username.charAt(0).toUpperCase()}
                                                                    </span>
                                                                </div>
                                                                <div className="ml-4">
                                                                    {editingMember === member.user_id ? (
                                                                        <input
                                                                            type="text"
                                                                            value={editDisplayName}
                                                                            onChange={(e) => setEditDisplayName(e.target.value)}
                                                                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                                                            placeholder="Display Name"
                                                                        />
                                                                    ) : (
                                                                        <>
                                                                            <div className="text-sm font-medium text-gray-900">
                                                                                {member.display_name || member.discord_username}
                                                                            </div>
                                                                            {member.display_name && (
                                                                                <div className="text-xs text-gray-400">
                                                                                    @{member.discord_username}
                                                                                </div>
                                                                            )}
                                                                        </>
                                                                    )}
                                                                    <div className="text-sm text-gray-500">
                                                                        {member.role === 'owner' ? 'Project Owner' :
                                                                            member.role === 'editor' ? 'Member (Editor)' : 'Member (Viewer)'}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap">
                                                            {editingMember === member.user_id ? (
                                                                <input
                                                                    type="text"
                                                                    value={editRoleValue}
                                                                    onChange={(e) => setEditRoleValue(e.target.value)}
                                                                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                                                    placeholder="e.g. Director"
                                                                />
                                                            ) : (
                                                                member.default_staff_role ? (
                                                                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                                                                        {member.default_staff_role}
                                                                    </span>
                                                                ) : (
                                                                    <span className="text-gray-400 text-sm italic">
                                                                        No specific role
                                                                    </span>
                                                                )
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                            @{member.discord_username}
                                                        </td>
                                                        {isOwner && (
                                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                                {editingMember === member.user_id ? (
                                                                    <div className="flex justify-end space-x-2">
                                                                        <button
                                                                            onClick={() => handleSave(member)}
                                                                            disabled={updateMemberMutation.isPending}
                                                                            className="text-indigo-600 hover:text-indigo-900 disabled:opacity-50"
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
                                                                        onClick={() => startEditing(member.user_id, member.default_staff_role, member.display_name)}
                                                                        className="text-indigo-600 hover:text-indigo-900"
                                                                    >
                                                                        Edit
                                                                    </button>
                                                                )}
                                                            </td>
                                                        )}
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
        </div>
    );
};
