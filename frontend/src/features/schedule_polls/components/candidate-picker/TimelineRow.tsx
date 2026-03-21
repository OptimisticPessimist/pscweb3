import React, { useRef, useCallback } from 'react';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import type { DateKey, SlotIndex } from './types';
import { TOTAL_SLOTS } from './types';

interface TimelineRowProps {
  date: DateKey;
  selectedSlots: Set<SlotIndex>;
  onToggleSlot: (date: DateKey, slot: SlotIndex) => void;
  onSelectRange: (date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => void;
  onDeselectRange: (date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => void;
  onReset: (date: DateKey) => void;
  onSetAllDay: (date: DateKey) => void;
}

export const TimelineRow: React.FC<TimelineRowProps> = ({
  date,
  selectedSlots,
  onToggleSlot,
  onSelectRange,
  onDeselectRange,
  onReset,
  onSetAllDay,
}) => {
  const isDragging = useRef(false);
  const dragStart = useRef<SlotIndex | null>(null);
  const dragMode = useRef<'select' | 'deselect'>('select');
  const previewSlots = useRef<Set<SlotIndex>>(new Set());
  const rowRef = useRef<HTMLDivElement>(null);

  const dateObj = parseISO(date);
  const dateLabel = format(dateObj, 'M/d (E)', { locale: ja });

  const updatePreview = useCallback((start: SlotIndex, end: SlotIndex) => {
    const min = Math.min(start, end);
    const max = Math.max(start, end);
    previewSlots.current = new Set(
      Array.from({ length: max - min + 1 }, (_, i) => min + i)
    );

    // Update cell styles directly for performance
    if (!rowRef.current) return;
    const cells = rowRef.current.querySelectorAll<HTMLElement>('[data-slot]');
    cells.forEach(cell => {
      const slot = Number(cell.dataset.slot);
      const inPreview = previewSlots.current.has(slot);
      const isSelected = selectedSlots.has(slot);

      if (inPreview) {
        if (dragMode.current === 'select') {
          cell.classList.add('bg-indigo-300');
          cell.classList.remove('bg-indigo-500', 'bg-gray-100');
        } else {
          cell.classList.add('bg-red-200');
          cell.classList.remove('bg-indigo-500', 'bg-gray-100');
        }
      } else if (isSelected) {
        cell.classList.add('bg-indigo-500');
        cell.classList.remove('bg-indigo-300', 'bg-red-200', 'bg-gray-100');
      } else {
        cell.classList.add('bg-gray-100');
        cell.classList.remove('bg-indigo-500', 'bg-indigo-300', 'bg-red-200');
      }
    });
  }, [selectedSlots]);

  const handleMouseDown = useCallback((slot: SlotIndex) => {
    isDragging.current = true;
    dragStart.current = slot;
    dragMode.current = selectedSlots.has(slot) ? 'deselect' : 'select';
    updatePreview(slot, slot);
  }, [selectedSlots, updatePreview]);

  const handleMouseEnter = useCallback((slot: SlotIndex) => {
    if (!isDragging.current || dragStart.current === null) return;
    updatePreview(dragStart.current, slot);
  }, [updatePreview]);

  const handleMouseUp = useCallback((slot: SlotIndex) => {
    if (!isDragging.current || dragStart.current === null) {
      isDragging.current = false;
      return;
    }
    const start = dragStart.current;
    isDragging.current = false;
    dragStart.current = null;
    previewSlots.current = new Set();

    if (start === slot) {
      onToggleSlot(date, slot);
    } else if (dragMode.current === 'select') {
      onSelectRange(date, start, slot);
    } else {
      onDeselectRange(date, start, slot);
    }
  }, [date, onToggleSlot, onSelectRange, onDeselectRange]);

  // Global mouseup handler to handle drag ending outside the row
  React.useEffect(() => {
    const handleGlobalMouseUp = () => {
      if (isDragging.current && dragStart.current !== null) {
        isDragging.current = false;
        dragStart.current = null;
        previewSlots.current = new Set();
        // Reset cell styles
        if (rowRef.current) {
          const cells = rowRef.current.querySelectorAll<HTMLElement>('[data-slot]');
          cells.forEach(cell => {
            const slot = Number(cell.dataset.slot);
            const isSelected = selectedSlots.has(slot);
            cell.classList.remove('bg-indigo-300', 'bg-red-200');
            if (isSelected) {
              cell.classList.add('bg-indigo-500');
              cell.classList.remove('bg-gray-100');
            } else {
              cell.classList.add('bg-gray-100');
              cell.classList.remove('bg-indigo-500');
            }
          });
        }
      }
    };
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, [selectedSlots]);

  return (
    <div className="flex items-center border-b border-gray-100">
      {/* Date label (sticky) */}
      <div className="sticky left-0 z-10 bg-white min-w-[120px] pr-2 py-2 flex flex-col">
        <span className="text-sm font-medium text-gray-700">{dateLabel}</span>
        <div className="flex gap-2 text-xs">
          <button
            type="button"
            onClick={() => onReset(date)}
            className="text-indigo-500 hover:text-indigo-700"
          >
            リセット
          </button>
          <span className="text-gray-300">|</span>
          <button
            type="button"
            onClick={() => onSetAllDay(date)}
            className="text-indigo-500 hover:text-indigo-700"
          >
            終日
          </button>
        </div>
      </div>

      {/* Timeline cells */}
      <div
        ref={rowRef}
        className="flex select-none"
        onMouseLeave={() => {
          // Keep drag active but don't update preview
        }}
      >
        {Array.from({ length: TOTAL_SLOTS }, (_, i) => {
          const isSelected = selectedSlots.has(i);
          // Add a left border at each hour boundary (every 2 slots)
          const isHourBoundary = i % 2 === 0;

          return (
            <div
              key={i}
              data-slot={i}
              onMouseDown={(e) => {
                e.preventDefault();
                handleMouseDown(i);
              }}
              onMouseEnter={() => handleMouseEnter(i)}
              onMouseUp={() => handleMouseUp(i)}
              className={`
                w-[14px] h-8 cursor-pointer transition-colors duration-75
                ${isSelected ? 'bg-indigo-500' : 'bg-gray-100'}
                ${isHourBoundary ? 'border-l border-gray-300' : 'border-l border-gray-200'}
              `}
            />
          );
        })}
      </div>
    </div>
  );
};
