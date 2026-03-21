import React, { useState } from 'react';
import type { SlotIndex } from './types';
import { TOTAL_SLOTS, slotToTimeLabel, timeLabelToSlot } from './types';

interface BulkTimeSelectorProps {
  onBulkApply: (startSlot: SlotIndex, endSlot: SlotIndex) => void;
  onResetAll: () => void;
  disabled: boolean;
}

function generateTimeOptions(): { label: string; slot: SlotIndex }[] {
  const options: { label: string; slot: SlotIndex }[] = [];
  for (let i = 0; i < TOTAL_SLOTS; i++) {
    options.push({ label: slotToTimeLabel(i), slot: i });
  }
  return options;
}

const TIME_OPTIONS = generateTimeOptions();

export const BulkTimeSelector: React.FC<BulkTimeSelectorProps> = ({
  onBulkApply,
  onResetAll,
  disabled,
}) => {
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('19:00');

  const handleApply = () => {
    const startSlot = timeLabelToSlot(startTime);
    // endSlot is the last slot to include (end time - 30min, since each slot is 30min)
    const endSlot = timeLabelToSlot(endTime) - 1;
    if (endSlot >= startSlot) {
      onBulkApply(startSlot, endSlot);
    }
  };

  return (
    <div className="flex items-center gap-3 flex-wrap text-sm">
      <select
        value={startTime}
        onChange={(e) => setStartTime(e.target.value)}
        className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
        disabled={disabled}
      >
        {TIME_OPTIONS.map(({ label }) => (
          <option key={`start-${label}`} value={label}>
            {label}
          </option>
        ))}
      </select>

      <span className="text-gray-400">〜</span>

      <select
        value={endTime}
        onChange={(e) => setEndTime(e.target.value)}
        className="px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
        disabled={disabled}
      >
        {TIME_OPTIONS.map(({ label }) => (
          <option key={`end-${label}`} value={label}>
            {label}
          </option>
        ))}
      </select>

      <span className="text-gray-400">まで</span>

      <button
        type="button"
        onClick={handleApply}
        disabled={disabled}
        className="text-indigo-600 hover:text-indigo-800 font-medium disabled:text-gray-300"
      >
        一括設定する
      </button>

      <span className="text-gray-300">|</span>

      <button
        type="button"
        onClick={onResetAll}
        disabled={disabled}
        className="text-gray-500 hover:text-gray-700 disabled:text-gray-300"
      >
        全てリセット
      </button>
    </div>
  );
};
