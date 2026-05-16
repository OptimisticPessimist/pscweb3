import React, { useMemo, useState } from 'react';
import {
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  getDay,
  addMonths,
  subMonths,
  format,
  isToday,
  isBefore,
  startOfDay,
} from 'date-fns';
import { useTranslation } from 'react-i18next';
import type { DateKey } from './types';

interface MonthCalendarProps {
  selectedDates: DateKey[];
  onToggleDate: (date: DateKey) => void;
}

function SingleMonth({
  month,
  selectedDates,
  weekdayLabels,
  monthFormatter,
  onToggleDate,
}: {
  month: Date;
  selectedDates: DateKey[];
  weekdayLabels: string[];
  monthFormatter: Intl.DateTimeFormat;
  onToggleDate: (date: DateKey) => void;
}) {
  const monthStart = startOfMonth(month);
  const monthEnd = endOfMonth(month);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });
  const startDow = getDay(monthStart);
  const today = startOfDay(new Date());

  // Pad the beginning with empty cells
  const paddedDays: (Date | null)[] = [
    ...Array.from({ length: startDow }, () => null),
    ...days,
  ];

  return (
    <div className="flex-1 min-w-[280px]">
      <h3 className="text-center font-bold text-gray-700 mb-2">
        {monthFormatter.format(month)}
      </h3>
      <div className="grid grid-cols-7 gap-0">
        {/* Weekday headers */}
        {weekdayLabels.map((label, i) => (
          <div
            key={label}
            className={`text-center text-xs font-bold py-1 ${
              i === 0 ? 'text-red-500' : i === 6 ? 'text-blue-500' : 'text-gray-500'
            }`}
          >
            {label}
          </div>
        ))}
        {/* Day cells */}
        {paddedDays.map((day, i) => {
          if (!day) {
            return <div key={`empty-${i}`} className="p-1" />;
          }
          const dateKey = format(day, 'yyyy-MM-dd');
          const isSelected = selectedDates.includes(dateKey);
          const isPast = isBefore(day, today);
          const isTodayDate = isToday(day);
          const dow = getDay(day);

          return (
            <button
              key={dateKey}
              type="button"
              disabled={isPast}
              onClick={() => onToggleDate(dateKey)}
              className={`
                p-1 text-sm text-center rounded-lg transition-all
                ${isPast ? 'text-gray-300 cursor-not-allowed' : 'cursor-pointer hover:bg-indigo-50'}
                ${isSelected ? 'bg-indigo-600 text-white hover:bg-indigo-700' : ''}
                ${!isSelected && !isPast && dow === 0 ? 'text-red-500' : ''}
                ${!isSelected && !isPast && dow === 6 ? 'text-blue-500' : ''}
                ${isTodayDate && !isSelected ? 'ring-1 ring-indigo-400' : ''}
              `}
            >
              {format(day, 'd')}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export const MonthCalendar: React.FC<MonthCalendarProps> = ({ selectedDates, onToggleDate }) => {
  const { t, i18n } = useTranslation();
  const [currentMonth, setCurrentMonth] = useState(() => startOfMonth(new Date()));

  const monthFormatter = useMemo(
    () => new Intl.DateTimeFormat(i18n.language, { year: 'numeric', month: 'long' }),
    [i18n.language]
  );
  const weekdayLabels = useMemo(() => {
    const formatter = new Intl.DateTimeFormat(i18n.language, { weekday: 'short' });
    const sunday = new Date(Date.UTC(2024, 0, 7));
    return Array.from({ length: 7 }, (_, i) =>
      formatter.format(new Date(sunday.getTime() + i * 24 * 60 * 60 * 1000))
    );
  }, [i18n.language]);

  const nextMonth = addMonths(currentMonth, 1);

  return (
    <div>
      {/* Navigation */}
      <div className="flex justify-between items-center mb-4">
        <button
          type="button"
          onClick={() => setCurrentMonth(prev => subMonths(prev, 1))}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          {t('schedulePoll.candidatePicker.previousMonth')}
        </button>
        <button
          type="button"
          onClick={() => setCurrentMonth(startOfMonth(new Date()))}
          className="text-sm text-gray-600 hover:text-gray-800 font-medium px-3 py-1 border border-gray-200 rounded-lg"
        >
          {t('schedulePoll.candidatePicker.today')}
        </button>
        <button
          type="button"
          onClick={() => setCurrentMonth(prev => addMonths(prev, 1))}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          {t('schedulePoll.candidatePicker.nextMonth')}
        </button>
      </div>

      {/* Two months side by side */}
      <div className="flex gap-6 flex-wrap">
        <SingleMonth
          month={currentMonth}
          selectedDates={selectedDates}
          weekdayLabels={weekdayLabels}
          monthFormatter={monthFormatter}
          onToggleDate={onToggleDate}
        />
        <SingleMonth
          month={nextMonth}
          selectedDates={selectedDates}
          weekdayLabels={weekdayLabels}
          monthFormatter={monthFormatter}
          onToggleDate={onToggleDate}
        />
      </div>

      {selectedDates.length > 0 && (
        <p className="text-xs text-gray-400 mt-3">
          {t('schedulePoll.candidatePicker.selectedDays', { count: selectedDates.length })}
        </p>
      )}
    </div>
  );
};
