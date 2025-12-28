import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../api/projects';
import type { MilestoneCreate } from '@/types';

interface MilestoneSettingsProps {
    projectId: string;
    canManage: boolean;
}

export const MilestoneSettings: React.FC<MilestoneSettingsProps> = ({ projectId, canManage }) => {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [isAdding, setIsAdding] = useState(false);

    // Form State
    const [title, setTitle] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [color, setColor] = useState('#3B82F6'); // Default Blue
    const [location, setLocation] = useState('');
    const [description, setDescription] = useState('');
    const [createAttendance, setCreateAttendance] = useState(false);
    const [attendanceDeadline, setAttendanceDeadline] = useState('');
    const [reservationCapacity, setReservationCapacity] = useState('');

    const { data: milestones, isLoading } = useQuery({
        queryKey: ['milestones', projectId],
        queryFn: () => projectsApi.getMilestones(projectId),
    });

    const createMutation = useMutation({
        mutationFn: (data: MilestoneCreate) => projectsApi.createMilestone(projectId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
            resetForm();
            alert(t('project.settings.milestones.messages.addSuccess'));
        },
        onError: (error: any) => {
            alert(`${t('common.error')}: ${error.message || t('common.unknown')}`);
        }
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => projectsApi.deleteMilestone(projectId, id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
            alert(t('project.settings.milestones.messages.deleteSuccess'));
        },
        onError: (error: any) => {
            alert(`${t('common.error')}: ${error.message || t('common.unknown')}`);
        }
    });

    const resetForm = () => {
        setTitle('');
        setStartDate('');
        setEndDate('');
        setColor('#3B82F6');
        setLocation('');
        setDescription('');
        setCreateAttendance(false);
        setAttendanceDeadline('');
        setReservationCapacity('');
        setIsAdding(false);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        createMutation.mutate({
            title,
            start_date: new Date(startDate).toISOString(),
            end_date: endDate ? new Date(endDate).toISOString() : null,
            color,
            location: location || null,
            description: description || null,
            create_attendance_check: createAttendance,
            attendance_deadline: attendanceDeadline ? new Date(attendanceDeadline).toISOString() : null,
            reservation_capacity: reservationCapacity ? parseInt(reservationCapacity) : null
        });
    };

    if (isLoading) return <div>{t('common.loading')}</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-lg leading-6 font-medium text-gray-900">{t('project.settings.milestones.title')}</h3>
                {canManage && !isAdding && (
                    <button
                        onClick={() => setIsAdding(true)}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        {t('project.settings.milestones.add')}
                    </button>
                )}
            </div>

            {/* List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                    {milestones?.length === 0 && !isAdding && (
                        <li className="px-4 py-4 sm:px-6 text-gray-500 text-sm text-center">
                            {t('project.settings.milestones.list')} ({t('dashboard.noProjectsMessage')})
                            {/* "No milestones" message is missing, reusing a placeholder or just generic list header */}
                            No Milestones
                        </li>
                    )}
                    {milestones?.map((milestone) => (
                        <li key={milestone.id}>
                            <div className="px-4 py-4 sm:px-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center">
                                        <span
                                            className="h-4 w-4 rounded-full mr-3"
                                            style={{ backgroundColor: milestone.color }}
                                        />
                                        <p className="text-sm font-medium text-indigo-600 truncate">{milestone.title}</p>
                                    </div>
                                    <div className="ml-2 flex-shrink-0 flex">
                                        <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                            {new Date(milestone.start_date).toLocaleDateString()}
                                            {milestone.end_date && ` - ${new Date(milestone.end_date).toLocaleDateString()}`}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-2 sm:flex sm:justify-between">
                                    <div className="sm:flex">
                                        {milestone.location && (
                                            <p className="flex items-center text-sm text-gray-500 mr-6">
                                                📍 {milestone.location}
                                            </p>
                                        )}
                                        {milestone.description && (
                                            <p className="flex items-center text-sm text-gray-500">
                                                📝 {milestone.description}
                                            </p>
                                        )}
                                    </div>
                                    {milestone.reservation_capacity && (
                                        <div className="mt-2 text-sm text-gray-500">
                                            🎫 予約定員: {milestone.reservation_capacity}名
                                        </div>
                                    )}
                                    <div className="mt-2 text-sm text-gray-500">
                                        🔗 <a href={`/reservations/${milestone.id}`} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                                            予約ページ
                                        </a>
                                    </div>
                                    {canManage && (
                                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                                            <button
                                                onClick={() => {
                                                    if (window.confirm(t('project.settings.milestones.messages.deleteConfirm', { title: milestone.title }))) {
                                                        deleteMutation.mutate(milestone.id);
                                                    }
                                                }}
                                                className="text-red-600 hover:text-red-900 font-medium"
                                            >
                                                {t('common.delete')}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Add Form */}
            {isAdding && (
                <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                            <div className="sm:col-span-3">
                                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.title')}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="text"
                                        name="title"
                                        id="title"
                                        required
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-3">
                                <label htmlFor="color" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.color')}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="color"
                                        name="color"
                                        id="color"
                                        value={color}
                                        onChange={(e) => setColor(e.target.value)}
                                        className="h-9 w-full rounded-md border border-gray-300 cursor-pointer"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-3">
                                <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.startDate')}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="date"
                                        name="start_date"
                                        id="start_date"
                                        required
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-3">
                                <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.endDate')}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="date"
                                        name="end_date"
                                        id="end_date"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-6">
                                <label htmlFor="location" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.location')}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="text"
                                        name="location"
                                        id="location"
                                        value={location}
                                        onChange={(e) => setLocation(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-6">
                                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.description')}
                                </label>
                                <div className="mt-1">
                                    <textarea
                                        id="description"
                                        name="description"
                                        rows={3}
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-3">
                                <label htmlFor="reservation_capacity" className="block text-sm font-medium text-gray-700">
                                    {t('project.settings.milestones.form.reservationCapacity')}
                                </label>
                                <div className="mt-1">
                                    <input
                                        type="number"
                                        name="reservation_capacity"
                                        id="reservation_capacity"
                                        min="0"
                                        value={reservationCapacity}
                                        onChange={(e) => setReservationCapacity(e.target.value)}
                                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                    />
                                </div>
                            </div>

                            <div className="sm:col-span-6">
                                <div className="flex items-start">
                                    <div className="flex items-center h-5">
                                        <input
                                            id="create_attendance"
                                            name="create_attendance"
                                            type="checkbox"
                                            checked={createAttendance}
                                            onChange={(e) => setCreateAttendance(e.target.checked)}
                                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                    </div>
                                    <div className="ml-3 text-sm">
                                        <label htmlFor="create_attendance" className="font-medium text-gray-700">
                                            {t('project.settings.milestones.form.attendanceCheck')}
                                        </label>
                                    </div>
                                </div>
                            </div>

                            {createAttendance && (
                                <div className="sm:col-span-3">
                                    <label htmlFor="attendance_deadline" className="block text-sm font-medium text-gray-700">
                                        {t('project.settings.milestones.form.attendanceDeadline')}
                                    </label>
                                    <div className="mt-1">
                                        <input
                                            type="datetime-local"
                                            name="attendance_deadline"
                                            id="attendance_deadline"
                                            value={attendanceDeadline}
                                            onChange={(e) => setAttendanceDeadline(e.target.value)}
                                            className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={resetForm}
                                className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                {t('project.settings.milestones.form.cancel')}
                            </button>
                            <button
                                type="submit"
                                disabled={createMutation.isPending}
                                className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                {createMutation.isPending ? t('project.settings.milestones.form.adding') : t('project.settings.milestones.form.add')}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
};
