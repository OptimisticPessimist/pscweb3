import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { scriptsApi } from '../api/scripts';
import { ArrowLeft, Download } from 'lucide-react';

export const ScriptDetailPage = () => {
    const { projectId, scriptId } = useParams<{ projectId: string; scriptId: string }>();

    const { data: script, isLoading } = useQuery({
        queryKey: ['script', scriptId],
        queryFn: () => scriptsApi.getScript(projectId!, scriptId!),
        enabled: !!scriptId,
    });

    const handleDownloadPdf = async () => {
        if (!script) return;
        try {
            const blob = await scriptsApi.downloadScriptPdf(projectId!, scriptId!);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${script.title}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Failed to download PDF', error);
            alert('Failed to download PDF');
        }
    };

    if (isLoading) return <div>Loading script...</div>;
    if (!script) return <div>Script not found</div>;

    return (
        <div className="space-y-6">
            <div className="md:flex md:items-center md:justify-between">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                        <Link to={`/projects/${projectId}/scripts`} className="mr-4 text-gray-500 hover:text-gray-700">
                            <ArrowLeft className="h-6 w-6" />
                        </Link>
                        <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                            {script.title}
                        </h2>
                    </div>
                </div>
                <div className="mt-4 flex md:mt-0 md:ml-4">
                    <button
                        onClick={handleDownloadPdf}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        <Download className="-ml-1 mr-2 h-5 w-5 text-gray-400" />
                        Download PDF
                    </button>
                </div>
            </div>

            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">Script Content</h3>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                        Uploaded by {script.uploaded_at ? new Date(script.uploaded_at).toLocaleString() : 'Unknown'}
                    </p>
                </div>
                <div className="bg-gray-50 px-4 py-5 sm:p-6 font-mono text-sm whitespace-pre-wrap overflow-x-auto">
                    {script.scenes.length > 0 ? (
                        <div className="space-y-4">
                            {script.scenes.map((scene) => (
                                <div key={scene.id} className="space-y-2">
                                    <h4 className="font-bold text-gray-800 uppercase">
                                        {scene.scene_number}. {scene.heading}
                                    </h4>
                                    {scene.description && (
                                        <p className="text-gray-600 italic whitespace-pre-wrap">{scene.description}</p>
                                    )}
                                    <div className="space-y-1 pl-4 border-l-2 border-gray-200">
                                        {scene.lines.map((line) => (
                                            <div key={line.id} className="grid grid-cols-12 gap-2">
                                                <div className="col-span-3 sm:col-span-2 font-bold text-gray-700 text-right pr-2">
                                                    {line.character.name}
                                                </div>
                                                <div className="col-span-9 sm:col-span-10 text-gray-900">
                                                    {line.content}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-500 italic">No parsed content available.</p>
                    )}
                </div>
            </div>
        </div>
    );
};
