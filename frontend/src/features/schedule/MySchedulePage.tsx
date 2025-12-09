
import { useQuery } from '@tanstack/react-query';
import { dashboardApi, type ScheduleItem } from '../dashboard/api/dashboard';
import { format, parseISO } from 'date-fns';

const ScheduleCard = ({ item }: { item: ScheduleItem }) => {
    const isMilestone = item.type === 'milestone';
    const startDate = parseISO(item.date);
    const endDate = item.end_date ? parseISO(item.end_date) : null;

    const timeString = format(startDate, 'HH:mm') + (endDate ? ` - ${format(endDate, 'HH:mm')}` : '');

    // Milestone styles
    const bgColor = isMilestone ? (item.color ? item.color + '20' : 'bg-yellow-50') : 'bg-white';
    const borderColor = isMilestone ? (item.color || 'border-yellow-200') : 'border-gray-200';
    const textColor = isMilestone ? 'text-gray-900' : 'text-gray-900';

    return (
        <div className={`flex flex-col sm:flex-row p-4 mb-2 rounded-lg border shadow-sm ${bgColor} ${isMilestone ? 'border-2' : ''} ${borderColor} transition-transform hover:scale-[1.01]`}>
            {/* Time & Project */}
            <div className="sm:w-1/4 flex flex-col justify-center mb-2 sm:mb-0">
                <span className="text-xl font-bold text-gray-700">{timeString}</span>
                <span className="text-xs font-semibold text-indigo-600 uppercase tracking-wide py-1">{item.project_name}</span>
            </div>

            {/* Details */}
            <div className="flex-1 flex flex-col justify-center">
                <div className="flex items-center gap-2">
                    {isMilestone && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                            Milestone
                        </span>
                    )}
                    {!isMilestone && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            Rehearsal
                        </span>
                    )}
                    <h3 className={`text-lg font-medium ${textColor}`}>
                        {item.title}
                    </h3>
                </div>

                <div className="mt-1 text-sm text-gray-600">
                    {isMilestone ? (
                        <span>{item.description}</span>
                    ) : (
                        <div className="flex flex-col gap-1">
                            {item.scene_heading && <span>Scene: {item.scene_heading}</span>}
                            {item.location && <span className="flex items-center gap-1">📍 {item.location}</span>}
                            {item.description && <span className="text-gray-500 italic">{item.description}</span>}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export const MySchedulePage = () => {
    const { data, isLoading, isError, error } = useQuery({
        queryKey: ['mySchedule'],
        queryFn: dashboardApi.getMySchedule,
    });

    if (isLoading) return <div className="p-8 text-center">Loading schedule...</div>;
    if (isError) return <div className="p-8 text-center text-red-600">Error: {error instanceof Error ? error.message : 'Unknown error'}</div>;

    const items = data?.items || [];

    // Group by date string (YYYY-MM-DD)
    const groupedItems: { [key: string]: ScheduleItem[] } = {};
    items.forEach(item => {
        const dateKey = format(parseISO(item.date), 'yyyy-MM-dd');
        if (!groupedItems[dateKey]) {
            groupedItems[dateKey] = [];
        }
        groupedItems[dateKey].push(item);
    });

    const sortedDates = Object.keys(groupedItems).sort();

    return (
        <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-8">My Schedule</h1>

            {items.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
                    <p className="text-gray-500">No upcoming schedule found.</p>
                </div>
            ) : (
                <div className="space-y-8">
                    {sortedDates.map(dateKey => (
                        <div key={dateKey}>
                            <h2 className="text-lg font-semibold text-gray-800 mb-3 border-b pb-1 sticky top-0 bg-gray-50 z-10">
                                {format(parseISO(dateKey), 'yyyy年MM月dd日 (EEE)')}
                            </h2>
                            <div className="space-y-3">
                                {groupedItems[dateKey].map(item => (
                                    <ScheduleCard key={item.id} item={item} />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
