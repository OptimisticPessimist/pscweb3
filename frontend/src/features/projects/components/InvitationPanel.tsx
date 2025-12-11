import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { invitationsApi } from '../api/invitations';
import type { InvitationResponse } from '@/types';

interface InvitationPanelProps {
    projectId: string;
}

export const InvitationPanel: React.FC<InvitationPanelProps> = ({ projectId }) => {
    const [expiresInHours, setExpiresInHours] = useState<number>(24 * 7); // Default 1 week
    const [maxUses, setMaxUses] = useState<string>(''); // Empty for unlimited, parse to number or null
    const [invitation, setInvitation] = useState<InvitationResponse | null>(null);
    const [copied, setCopied] = useState(false);

    const createMutation = useMutation({
        mutationFn: () => invitationsApi.createInvitation(projectId, {
            expires_in_hours: expiresInHours,
            max_uses: maxUses ? parseInt(maxUses) : null,
        }),
        onSuccess: (data) => {
            setInvitation(data);
            setCopied(false);
        },
        onError: (error: Error) => {
            console.error('Failed to create invitation:', error);
            alert('Failed to generate invitation link.');
        }
    });

    const inviteUrl = invitation ? `${window.location.origin}/invitations/${invitation.token}` : '';

    const handleCopy = () => {
        if (inviteUrl) {
            navigator.clipboard.writeText(inviteUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="bg-white shadow sm:rounded-lg mt-6">
            <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">Invite New Members</h3>
                <div className="mt-2 max-w-xl text-sm text-gray-500">
                    <p>Generate a link to invite people to this project.</p>
                </div>
                <form className="mt-5 space-y-4" onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }}>
                    <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                        <div className="sm:col-span-3">
                            <label htmlFor="expires" className="block text-sm font-medium text-gray-700">Expires In</label>
                            <select
                                id="expires"
                                value={expiresInHours}
                                onChange={(e) => setExpiresInHours(Number(e.target.value))}
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                            >
                                <option value={24}>1 Day</option>
                                <option value={24 * 3}>3 Days</option>
                                <option value={24 * 7}>1 Week</option>
                                <option value={24 * 30}>30 Days</option>
                            </select>
                        </div>

                        <div className="sm:col-span-3">
                            <label htmlFor="maxUses" className="block text-sm font-medium text-gray-700">Max Uses (Optional)</label>
                            <input
                                type="number"
                                id="maxUses"
                                value={maxUses}
                                onChange={(e) => setMaxUses(e.target.value)}
                                placeholder="Unlimited"
                                min={1}
                                className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={createMutation.isPending}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {createMutation.isPending ? 'Generating...' : 'Generate New Link'}
                    </button>
                </form>

                {invitation && (
                    <div className="mt-6 rounded-md bg-gray-50 p-4 border border-gray-200">
                        <div className="flex justify-between items-center">
                            <div className="flex-1 mr-4">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Invitation Link</label>
                                <div className="flex rounded-md shadow-sm">
                                    <input
                                        type="text"
                                        readOnly
                                        value={inviteUrl}
                                        className="focus:ring-indigo-500 focus:border-indigo-500 flex-1 block w-full rounded-none rounded-l-md sm:text-sm border-gray-300 bg-white"
                                    />
                                    <button
                                        type="button"
                                        onClick={handleCopy}
                                        className={`-ml-px relative inline-flex items-center space-x-2 px-4 py-2 border border-gray-300 text-sm font-medium rounded-r-md 
                                            test-gray-700 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500
                                            ${copied ? 'text-green-600' : 'text-gray-700'}`}
                                    >
                                        {copied ? 'Copied!' : 'Copy'}
                                    </button>
                                </div>
                                <p className="mt-2 text-xs text-gray-500">
                                    Expires at: {new Date(invitation.expires_at).toLocaleString()}
                                </p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
