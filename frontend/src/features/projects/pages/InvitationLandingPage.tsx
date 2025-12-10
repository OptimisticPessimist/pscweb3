import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { invitationsApi } from '../api/invitations';
import { useAuth } from '@/features/auth/hooks/useAuth';

export const InvitationLandingPage: React.FC = () => {
    const { token } = useParams<{ token: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuth();

    const { data: invitation, isLoading, error } = useQuery({
        queryKey: ['invitation', token],
        queryFn: () => invitationsApi.getInvitation(token!),
        enabled: !!token,
        retry: false,
    });

    const acceptMutation = useMutation({
        mutationFn: () => invitationsApi.acceptInvitation(token!),
        onSuccess: (data) => {
            navigate(`/projects/${data.project_id}`);
        },
        onError: (err: Error) => {
            alert(`Failed to join project: ${err.message || 'Unknown error'}`);
        }
    });

    // Handle login redirection if needed
    const handleLogin = () => {
        // Redirect to login page, preserving return url
        // Assuming LoginPage handles ?redirect= or similar, or we can just go to /login
        // Since login logic might be complex with Discord, checking how to trigger it.
        // If useAuth has login, maybe it redirects?
        // Checking existing LoginPage, it likely just shows a button to backend auth.
        // Simplest: Navigate to /login and hope AuthProvider preserves state or we pass state.
        // For now, simple navigation.
        navigate('/login', { state: { from: location } });
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-md">
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Loading Invitation...</h2>
                </div>
            </div>
        );
    }

    if (error || !invitation) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-md">
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-red-600">Invitation Invalid</h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        This invitation link may have expired or is invalid.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                    Join {invitation.project_name}
                </h2>
                <p className="mt-2 text-center text-sm text-gray-600">
                    You have been invited by {invitation.created_by}
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    <div className="space-y-6">
                        <div>
                            <p className="text-center text-sm text-gray-500 mb-4">
                                Expires at: {new Date(invitation.expires_at).toLocaleString()}
                            </p>

                            {user ? (
                                <button
                                    onClick={() => acceptMutation.mutate()}
                                    disabled={acceptMutation.isPending}
                                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                >
                                    {acceptMutation.isPending ? 'Joining...' : 'Accept Invitation'}
                                </button>
                            ) : (
                                <div className="text-center">
                                    <p className="text-sm text-gray-700 mb-4">You need to sign in to join.</p>
                                    <button
                                        onClick={handleLogin}
                                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                    >
                                        Sign in with Discord
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
