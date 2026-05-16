import React, { useEffect } from 'react';
import { MonthCalendar } from './MonthCalendar';
import { TimelineGrid } from './TimelineGrid';
import { useTimeSlotSelection } from './useTimeSlotSelection';
import type { CandidateSlot } from './types';

interface CandidatePickerProps {
  onChange: (candidates: CandidateSlot[]) => void;
}

export const CandidatePicker: React.FC<CandidatePickerProps> = ({ onChange }) => {
  const {
    selectedDates,
    slotsByDate,
    toggleDate,
    toggleSlot,
    selectSlotRange,
    deselectSlotRange,
    bulkApply,
    resetDate,
    setAllDay,
    resetAll,
    candidates,
  } = useTimeSlotSelection();

  useEffect(() => {
    onChange(candidates);
  }, [candidates, onChange]);

  return (
    <div className="space-y-6">
      {/* STEP 1: Date Selection */}
      <div className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-8">
        <h2 className="text-sm font-bold text-gray-700 mb-4">
          STEP 1 → 日付を選択
        </h2>
        <MonthCalendar selectedDates={selectedDates} onToggleDate={toggleDate} />
      </div>

      {/* STEP 2: Time Selection */}
      {selectedDates.length > 0 && (
        <div className="bg-white shadow-xl shadow-gray-200/50 rounded-2xl border border-gray-100 p-8">
          <h2 className="text-sm font-bold text-gray-700 mb-4">
            STEP 2 → 時間を選択
          </h2>
          <TimelineGrid
            selectedDates={selectedDates}
            slotsByDate={slotsByDate}
            toggleSlot={toggleSlot}
            selectSlotRange={selectSlotRange}
            deselectSlotRange={deselectSlotRange}
            bulkApply={bulkApply}
            resetDate={resetDate}
            setAllDay={setAllDay}
            resetAll={resetAll}
          />
        </div>
      )}
    </div>
  );
};
