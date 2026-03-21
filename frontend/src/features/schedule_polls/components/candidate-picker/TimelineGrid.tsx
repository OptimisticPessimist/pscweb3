import React from 'react';
import type { DateKey, SlotIndex } from './types';
import { TOTAL_SLOTS, TIMELINE_START_HOUR } from './types';
import { TimelineRow } from './TimelineRow';
import { BulkTimeSelector } from './BulkTimeSelector';

interface TimelineGridProps {
  selectedDates: DateKey[];
  slotsByDate: Map<DateKey, Set<SlotIndex>>;
  toggleSlot: (date: DateKey, slot: SlotIndex) => void;
  selectSlotRange: (date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => void;
  deselectSlotRange: (date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => void;
  bulkApply: (startSlot: SlotIndex, endSlot: SlotIndex) => void;
  resetDate: (date: DateKey) => void;
  setAllDay: (date: DateKey) => void;
  resetAll: () => void;
}

function generateHourLabels(): string[] {
  const labels: string[] = [];
  for (let i = 0; i < TOTAL_SLOTS; i += 2) {
    const hour = (TIMELINE_START_HOUR + i / 2) % 24;
    labels.push(hour.toString().padStart(2, '0'));
  }
  return labels;
}

const HOUR_LABELS = generateHourLabels();

export const TimelineGrid: React.FC<TimelineGridProps> = ({
  selectedDates,
  slotsByDate,
  toggleSlot,
  selectSlotRange,
  deselectSlotRange,
  bulkApply,
  resetDate,
  setAllDay,
  resetAll,
}) => {
  if (selectedDates.length === 0) return null;

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs text-gray-500 mb-2">
          タイムラインのホワイト部分をクリックまたはドラッグで時間の選択・取り消しができます。
        </p>
        <p className="text-xs text-gray-500 mb-3">
          すべての日付を一括で選択したい場合は一括設定が便利です。
        </p>

        <BulkTimeSelector
          onBulkApply={bulkApply}
          onResetAll={resetAll}
          disabled={selectedDates.length === 0}
        />
      </div>

      <div className="overflow-x-auto border border-gray-200 rounded-xl">
        {/* Hour labels header */}
        <div className="flex">
          <div className="sticky left-0 z-10 bg-white min-w-[120px]" />
          <div className="flex">
            {HOUR_LABELS.map((label, i) => (
              <div
                key={i}
                className="text-xs text-gray-400 text-center border-l border-gray-300"
                style={{ width: '28px' }}
              >
                {label}
              </div>
            ))}
          </div>
        </div>

        {/* Timeline rows */}
        {selectedDates.map(date => (
          <TimelineRow
            key={date}
            date={date}
            selectedSlots={slotsByDate.get(date) || new Set()}
            onToggleSlot={toggleSlot}
            onSelectRange={selectSlotRange}
            onDeselectRange={deselectSlotRange}
            onReset={resetDate}
            onSetAllDay={setAllDay}
          />
        ))}
      </div>
    </div>
  );
};
