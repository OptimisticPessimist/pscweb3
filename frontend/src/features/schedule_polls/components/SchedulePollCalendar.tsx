import React, { useRef, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { PollCandidateAnalysis, SchedulePollCalendarAnalysis } from '../api/schedulePoll';
import { useTranslation } from 'react-i18next';
import { Clock, Users, Sparkles, CheckCircle2, AlertCircle, X, ArrowRight } from 'lucide-react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';

interface SchedulePollCalendarProps {
    analysis: SchedulePollCalendarAnalysis;
    onFinalize: (candidateId: string, sceneIds: string[]) => void;
}

export const SchedulePollCalendar: React.FC<SchedulePollCalendarProps> = ({ analysis, onFinalize }) => {
    const { t } = useTranslation();
    const calendarRef = useRef<FullCalendar>(null);
    const [selectedAnalysis, setSelectedAnalysis] = useState<PollCandidateAnalysis | null>(null);
    const [isPanelOpen, setIsPanelOpen] = useState(false);

    // Convert analyses to FullCalendar events
    const events = analysis.analyses.map((a) => {
        const hasPossible = a.possible_scenes.length > 0;
        const hasReach = a.reach_scenes.length > 0;

        let color = '#94a3b8'; // slate-400 (default)
        if (hasPossible) {
            color = '#10b981'; // emerald-500
        } else if (hasReach) {
            color = '#f59e0b'; // amber-500
        }

        return {
            id: a.candidate_id,
            title: hasPossible
                ? `🟢 ${a.possible_scenes.length} Scenes`
                : (hasReach ? `🟡 ${a.reach_scenes.length} Reach` : '⚪ No matching scenes'),
            start: a.start_datetime,
            end: a.end_datetime,
            backgroundColor: color,
            borderColor: color,
            extendedProps: a
        };
    });

    const handleEventClick = (info: any) => {
        setSelectedAnalysis(info.event.extendedProps as PollCandidateAnalysis);
        setIsPanelOpen(true);
    };

    return (
        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                <div>
                    <h2 className="text-2xl font-black text-gray-900 tracking-tight flex items-center">
                        <Clock className="h-6 w-6 mr-2 text-indigo-600" />
                        {t('schedulePoll.calendarView') || '日程調整カレンダー'}
                    </h2>
                    <p className="text-gray-500 text-sm mt-1">
                        {t('schedulePoll.calendarHint') || '候補日程をクリックして詳細と稽古可能シーンを確認できます'}
                    </p>
                </div>
                <div className="flex items-center space-x-4 text-xs font-bold uppercase tracking-widest">
                    <div className="flex items-center">
                        <div className="w-3 h-3 rounded-full bg-emerald-500 mr-2 shadow-sm shadow-emerald-200"></div>
                        <span className="text-emerald-700">{t('schedulePoll.statusPossible') || '稽古可能'}</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-3 h-3 rounded-full bg-amber-500 mr-2 shadow-sm shadow-amber-200"></div>
                        <span className="text-amber-700">{t('schedulePoll.statusReach') || 'あと1人で可能'}</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-3 h-3 rounded-full bg-slate-400 mr-2"></div>
                        <span className="text-slate-500">{t('schedulePoll.statusNone') || '予定なし'}</span>
                    </div>
                </div>
            </div>

            <div className="calendar-container premium-calendar">
                <FullCalendar
                    ref={calendarRef}
                    plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                    initialView="timeGridWeek"
                    headerToolbar={{
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek,timeGridDay'
                    }}
                    events={events}
                    eventClick={handleEventClick}
                    height="auto"
                    locale="ja"
                    allDaySlot={false}
                    slotMinTime="08:00:00"
                    slotMaxTime="23:00:00"
                    nowIndicator={true}
                    slotEventOverlap={false}
                    eventClassNames="cursor-pointer hover:scale-[1.02] transition-transform duration-200 shadow-sm rounded-lg"
                    eventContent={(eventInfo) => (
                        <div className="p-1 px-2 h-full flex flex-col justify-center">
                            <div className="text-[10px] font-black leading-tight truncate">
                                {eventInfo.event.title}
                            </div>
                        </div>
                    )}
                />
            </div>

            {/* Side Panel (Slide-over) */}
            <Transition.Root show={isPanelOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50" onClose={setIsPanelOpen}>
                    <Transition.Child
                        as={Fragment}
                        enter="ease-in-out duration-500"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in-out duration-500"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-gray-900/40 backdrop-blur-sm transition-opacity" />
                    </Transition.Child>

                    <div className="fixed inset-0 overflow-hidden">
                        <div className="absolute inset-0 overflow-hidden">
                            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
                                <Transition.Child
                                    as={Fragment}
                                    enter="transform transition ease-in-out duration-500 sm:duration-700"
                                    enterFrom="translate-x-full"
                                    enterTo="translate-x-0"
                                    leave="transform transition ease-in-out duration-500 sm:duration-700"
                                    leaveFrom="translate-x-0"
                                    leaveTo="translate-x-full"
                                >
                                    <Dialog.Panel className="pointer-events-auto w-screen max-w-md">
                                        <div className="flex h-full flex-col overflow-y-auto bg-white shadow-2xl">
                                            <div className="p-8">
                                                <div className="flex items-start justify-between">
                                                    <Dialog.Title className="text-2xl font-black text-gray-900 tracking-tight">
                                                        {t('schedulePoll.candidateDetails') || '候補日程の詳細'}
                                                    </Dialog.Title>
                                                    <div className="ml-3 flex h-7 items-center">
                                                        <button
                                                            type="button"
                                                            className="rounded-full bg-gray-100 p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-200 transition-all"
                                                            onClick={() => setIsPanelOpen(false)}
                                                        >
                                                            <X className="h-6 w-6" aria-hidden="true" />
                                                        </button>
                                                    </div>
                                                </div>

                                                {selectedAnalysis && (
                                                    <div className="mt-8 space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                                                        {/* Time Info */}
                                                        <div className="bg-gradient-to-br from-indigo-50 to-violet-50 rounded-3xl p-6 border border-indigo-100/50 relative overflow-hidden">
                                                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                                                <Clock className="h-16 w-16 text-indigo-600" />
                                                            </div>
                                                            <div className="text-sm font-bold text-indigo-600 uppercase tracking-widest mb-2">Selected Time</div>
                                                            <div className="text-xl font-black text-gray-900 font-mono">
                                                                {new Date(selectedAnalysis.start_datetime).toLocaleDateString(undefined, { month: 'long', day: 'numeric', weekday: 'long' })}
                                                            </div>
                                                            <div className="text-lg font-bold text-indigo-600/80 mt-1">
                                                                {new Date(selectedAnalysis.start_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                                                {' - '}
                                                                {new Date(selectedAnalysis.end_datetime).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                                                            </div>
                                                        </div>

                                                        {/* Member summary */}
                                                        <div>
                                                            <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center">
                                                                <Users className="h-4 w-4 mr-2" />
                                                                {t('schedulePoll.availableMembers') || '参加可能メンバー'}
                                                                <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-[10px]">{selectedAnalysis.available_user_names.length}名</span>
                                                            </h3>
                                                            <div className="flex flex-wrap gap-2">
                                                                {selectedAnalysis.available_user_names.map((name, i) => {
                                                                    const isMaybe = selectedAnalysis.maybe_user_names.includes(name);
                                                                    return (
                                                                        <span
                                                                            key={i}
                                                                            className={`text-[11px] font-bold px-3 py-1 rounded-full shadow-sm border ${isMaybe
                                                                                    ? 'bg-amber-50 text-amber-700 border-amber-100'
                                                                                    : 'bg-white text-gray-700 border-gray-100'
                                                                                }`}
                                                                        >
                                                                            {name}{isMaybe ? ' (△)' : ''}
                                                                        </span>
                                                                    );
                                                                })}
                                                            </div>
                                                            {selectedAnalysis.available_user_names.length === 0 && (
                                                                <p className="text-xs text-gray-400 italic">参加可能なメンバーはいません</p>
                                                            )}
                                                        </div>

                                                        {/* Section: Possible Scenes */}
                                                        <div>
                                                            <h3 className="text-sm font-black text-emerald-600 uppercase tracking-widest mb-4 flex items-center">
                                                                <CheckCircle2 className="h-4 w-4 mr-2" />
                                                                {t('schedulePoll.possibleScenes') || '稽古可能なシーン'}
                                                                <span className="ml-2 bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded text-[10px]">{selectedAnalysis.possible_scenes.length}</span>
                                                            </h3>
                                                            {selectedAnalysis.possible_scenes.length > 0 ? (
                                                                <div className="space-y-3">
                                                                    {selectedAnalysis.possible_scenes.map((scene) => (
                                                                        <div key={scene.scene_id} className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-4 flex items-center justify-between group hover:bg-emerald-50 transition-colors">
                                                                            <div className="flex items-center space-x-3">
                                                                                <div className="w-10 h-10 bg-white rounded-xl shadow-sm border border-emerald-100 flex items-center justify-center font-black text-emerald-600">
                                                                                    {scene.scene_number}
                                                                                </div>
                                                                                <div className="font-bold text-gray-900">{scene.heading}</div>
                                                                            </div>
                                                                            <Sparkles className="h-4 w-4 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            ) : (
                                                                <p className="text-sm text-gray-400 text-center py-4">{t('schedulePoll.noPossibleScenes') || '稽古可能なシーンはありません'}</p>
                                                            )}
                                                        </div>

                                                        {/* Section: Reach Scenes */}
                                                        <div>
                                                            <h3 className="text-sm font-black text-amber-600 uppercase tracking-widest mb-4 flex items-center">
                                                                <AlertCircle className="h-4 w-4 mr-2" />
                                                                {t('schedulePoll.reachScenes') || 'あと1人で可能なシーン'}
                                                                <span className="ml-2 bg-amber-100 text-amber-600 px-2 py-0.5 rounded text-[10px]">{selectedAnalysis.reach_scenes.length}</span>
                                                            </h3>
                                                            {selectedAnalysis.reach_scenes.length > 0 ? (
                                                                <div className="space-y-3">
                                                                    {selectedAnalysis.reach_scenes.map((scene) => (
                                                                        <div key={scene.scene_id} className="bg-amber-50/50 border border-amber-100 rounded-2xl p-4 hover:bg-amber-50 transition-colors">
                                                                            <div className="flex items-center justify-between mb-2">
                                                                                <div className="flex items-center space-x-3">
                                                                                    <div className="w-10 h-10 bg-white rounded-xl shadow-sm border border-amber-100 flex items-center justify-center font-black text-amber-600">
                                                                                        {scene.scene_number}
                                                                                    </div>
                                                                                    <div className="font-bold text-gray-900">{scene.heading}</div>
                                                                                </div>
                                                                            </div>
                                                                            <div className="flex items-center space-x-2 pl-13">
                                                                                <span className="text-[10px] font-black uppercase text-amber-500 tracking-tighter">Missing:</span>
                                                                                <div className="flex flex-wrap gap-1">
                                                                                    {scene.missing_user_names.map((name, i) => (
                                                                                        <span key={i} className="text-[11px] font-bold text-amber-900 px-2 py-0.5 bg-white border border-amber-200 rounded-full shadow-sm">
                                                                                            {name}
                                                                                        </span>
                                                                                    ))}
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            ) : (
                                                                <p className="text-sm text-gray-400 text-center py-4">{t('schedulePoll.noReachScenes') || 'リーチ状態のシーンはありません'}</p>
                                                            )}
                                                        </div>

                                                        {/* Finalize Button */}
                                                        <div className="pt-4 border-t border-gray-100">
                                                            <button
                                                                onClick={() => {
                                                                    onFinalize(
                                                                        selectedAnalysis.candidate_id,
                                                                        selectedAnalysis.possible_scenes.map(s => s.scene_id)
                                                                    );
                                                                    setIsPanelOpen(false);
                                                                }}
                                                                className="w-full py-5 bg-indigo-600 text-white rounded-2xl font-black shadow-xl shadow-indigo-100 flex items-center justify-center space-x-3 hover:bg-indigo-700 hover:-translate-y-1 active:translate-y-0 transition-all"
                                                            >
                                                                <span>{t('schedulePoll.finalizeThis') || 'この日程で確定する'}</span>
                                                                <ArrowRight className="h-5 w-5" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </Dialog.Panel>
                                </Transition.Child>
                            </div>
                        </div>
                    </div>
                </Dialog>
            </Transition.Root>
        </div>
    );
};
