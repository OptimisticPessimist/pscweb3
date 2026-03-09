import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { invitationsApi } from '../api/invitations';

interface InvitationPanelProps {
    projectId: string;
}

export const InvitationPanel: React.FC<InvitationPanelProps> = ({ projectId }) => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [expiresInHours, setExpiresInHours] = useState<number>(24 * 7); // Default 1 week
    const [maxUses, setMaxUses] = useState<string>(''); // Empty for unlimited
    const [copiedToken, setCopiedToken] = useState<string | null>(null);

    // 有効な招待リンク一覧を取得
    const { data: invitations, isLoading } = useQuery({
        queryKey: ['projects', projectId, 'invitations'],
        queryFn: () => invitationsApi.getProjectInvitations(projectId),
    });

    const createMutation = useMutation({
        mutationFn: () => invitationsApi.createInvitation(projectId, {
            expires_in_hours: expiresInHours,
            max_uses: maxUses ? parseInt(maxUses) : null,
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'invitations'] });
            setMaxUses('');
        },
        onError: (error: Error) => {
            console.error('Failed to create invitation:', error);
            alert(t('invitation.panel.messages.generateError'));
        }
    });

    const handleCopy = (token: string) => {
        const url = `${window.location.origin}/invitations/${token}`;
        navigator.clipboard.writeText(url);
        setCopiedToken(token);
        setTimeout(() => setCopiedToken(null), 2000);
    };

    return (
        <div className="bg-white shadow sm:rounded-lg mt-6">
            <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">{t('invitation.panel.title')}</h3>
                <div className="mt-2 max-w-xl text-sm text-gray-500">
                    <p>{t('invitation.panel.description')}</p>
                </div>

                <form className="mt-5 space-y-4" onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }}>
                    <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                        <div className="sm:col-span-3">
                            <label htmlFor="expires" className="block text-sm font-medium text-gray-700">{t('invitation.panel.form.expiresIn')}</label>
                            <select
                                id="expires"
                                value={expiresInHours}
                                onChange={(e) => setExpiresInHours(Number(e.target.value))}
                                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                            >
                                <option value={24}>{t('invitation.panel.form.expiresOptions.1day')}</option>
                                <option value={24 * 3}>{t('invitation.panel.form.expiresOptions.3days')}</option>
                                <option value={24 * 7}>{t('invitation.panel.form.expiresOptions.1week')}</option>
                                <option value={24 * 30}>{t('invitation.panel.form.expiresOptions.30days')}</option>
                            </select>
                        </div>

                        <div className="sm:col-span-3">
                            <label htmlFor="maxUses" className="block text-sm font-medium text-gray-700">{t('invitation.panel.form.maxUses')}</label>
                            <input
                                type="number"
                                id="maxUses"
                                value={maxUses}
                                onChange={(e) => setMaxUses(e.target.value)}
                                placeholder={t('invitation.panel.form.maxUsesPlaceholder')}
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
                        {createMutation.isPending ? t('common.loading') : t('invitation.panel.form.generate')}
                    </button>
                </form>

                {isLoading ? (
                    <p className="mt-6 text-sm text-gray-500">{t('common.loading')}</p>
                ) : invitations && invitations.length > 0 ? (
                    <div className="mt-8">
                        <h4 className="text-sm font-medium text-gray-900 mb-4">有効な招待リンク</h4>
                        <div className="flex flex-col">
                            <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                                <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                                    <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('invitation.panel.generatedLink')}</th>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('invitation.expiresAt')}</th>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('invitation.uses')}</th>
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {invitations.map((inv) => (
                                                    <tr key={inv.token}>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                            <div className="flex items-center space-x-2">
                                                                <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                                                                    ...{inv.token.slice(-8)}
                                                                </code>
                                                                <button
                                                                    onClick={() => handleCopy(inv.token)}
                                                                    className={`text-xs font-medium ${copiedToken === inv.token ? 'text-green-600' : 'text-indigo-600 hover:text-indigo-900'}`}
                                                                >
                                                                    {copiedToken === inv.token ? t('invitation.panel.copied') : t('invitation.panel.copy')}
                                                                </button>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                            {new Date(inv.expires_at).toLocaleString()}
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                            {inv.max_uses ? `${inv.used_count} / ${inv.max_uses}` : t('invitation.panel.form.maxUsesPlaceholder')}
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
                ) : null}
            </div>
        </div>
    );
};
