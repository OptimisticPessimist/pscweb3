import { useState, useMemo, useCallback } from 'react';
import { addMinutes, startOfDay, addDays, parseISO } from 'date-fns';
import type { DateKey, SlotIndex, CandidateSlot } from './types';
import { TOTAL_SLOTS, TIMELINE_START_HOUR } from './types';

interface TimeSlotSelectionReturn {
  selectedDates: DateKey[];
  slotsByDate: Map<DateKey, Set<SlotIndex>>;
  toggleDate: (date: DateKey) => void;
  toggleSlot: (date: DateKey, slot: SlotIndex) => void;
  selectSlotRange: (date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => void;
  deselectSlotRange: (date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => void;
  bulkApply: (startSlot: SlotIndex, endSlot: SlotIndex) => void;
  resetDate: (date: DateKey) => void;
  setAllDay: (date: DateKey) => void;
  resetAll: () => void;
  candidates: CandidateSlot[];
}

/** Slots per day that cross midnight (index 36 = 00:00) */
const MIDNIGHT_SLOT = 36; // (24 - 6) * 2

function slotToDate(dateKey: DateKey, slot: SlotIndex): Date {
  const base = startOfDay(parseISO(dateKey));
  const actualBase = slot >= MIDNIGHT_SLOT ? addDays(base, 1) : base;
  const totalMinutes = TIMELINE_START_HOUR * 60 + slot * 30;
  const minutesFromMidnight = totalMinutes >= 24 * 60 ? totalMinutes - 24 * 60 : totalMinutes;
  return addMinutes(startOfDay(actualBase), minutesFromMidnight);
}

export function useTimeSlotSelection(): TimeSlotSelectionReturn {
  const [selectedDates, setSelectedDates] = useState<DateKey[]>([]);
  const [slotsByDate, setSlotsByDate] = useState<Map<DateKey, Set<SlotIndex>>>(new Map());

  const toggleDate = useCallback((date: DateKey) => {
    setSelectedDates(prev => {
      if (prev.includes(date)) {
        setSlotsByDate(prevSlots => {
          const next = new Map(prevSlots);
          next.delete(date);
          return next;
        });
        return prev.filter(d => d !== date);
      }
      const next = [...prev, date].sort();
      setSlotsByDate(prevSlots => {
        const nextSlots = new Map(prevSlots);
        if (!nextSlots.has(date)) nextSlots.set(date, new Set());
        return nextSlots;
      });
      return next;
    });
  }, []);

  const toggleSlot = useCallback((date: DateKey, slot: SlotIndex) => {
    setSlotsByDate(prev => {
      const next = new Map(prev);
      const slots = new Set(next.get(date) || []);
      if (slots.has(slot)) {
        slots.delete(slot);
      } else {
        slots.add(slot);
      }
      next.set(date, slots);
      return next;
    });
  }, []);

  const selectSlotRange = useCallback((date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => {
    const min = Math.min(startSlot, endSlot);
    const max = Math.max(startSlot, endSlot);
    setSlotsByDate(prev => {
      const next = new Map(prev);
      const slots = new Set(next.get(date) || []);
      for (let i = min; i <= max; i++) {
        slots.add(i);
      }
      next.set(date, slots);
      return next;
    });
  }, []);

  const deselectSlotRange = useCallback((date: DateKey, startSlot: SlotIndex, endSlot: SlotIndex) => {
    const min = Math.min(startSlot, endSlot);
    const max = Math.max(startSlot, endSlot);
    setSlotsByDate(prev => {
      const next = new Map(prev);
      const slots = new Set(next.get(date) || []);
      for (let i = min; i <= max; i++) {
        slots.delete(i);
      }
      next.set(date, slots);
      return next;
    });
  }, []);

  const bulkApply = useCallback((startSlot: SlotIndex, endSlot: SlotIndex) => {
    const min = Math.min(startSlot, endSlot);
    const max = Math.max(startSlot, endSlot);
    setSlotsByDate(prev => {
      const next = new Map(prev);
      for (const [date, existingSlots] of next.entries()) {
        const slots = new Set(existingSlots);
        for (let i = min; i <= max; i++) {
          slots.add(i);
        }
        next.set(date, slots);
      }
      return next;
    });
  }, []);

  const resetDate = useCallback((date: DateKey) => {
    setSlotsByDate(prev => {
      const next = new Map(prev);
      next.set(date, new Set());
      return next;
    });
  }, []);

  const setAllDay = useCallback((date: DateKey) => {
    setSlotsByDate(prev => {
      const next = new Map(prev);
      const slots = new Set<SlotIndex>();
      for (let i = 0; i < TOTAL_SLOTS; i++) slots.add(i);
      next.set(date, slots);
      return next;
    });
  }, []);

  const resetAll = useCallback(() => {
    setSlotsByDate(prev => {
      const next = new Map(prev);
      for (const date of next.keys()) {
        next.set(date, new Set());
      }
      return next;
    });
  }, []);

  const candidates = useMemo<CandidateSlot[]>(() => {
    const result: CandidateSlot[] = [];
    for (const date of selectedDates) {
      const slots = slotsByDate.get(date);
      if (!slots || slots.size === 0) continue;

      const sorted = Array.from(slots).sort((a, b) => a - b);

      // Merge contiguous slots into ranges
      let rangeStart = sorted[0];
      let rangeEnd = sorted[0];

      for (let i = 1; i < sorted.length; i++) {
        if (sorted[i] === rangeEnd + 1) {
          rangeEnd = sorted[i];
        } else {
          result.push({
            start_datetime: slotToDate(date, rangeStart).toISOString(),
            end_datetime: addMinutes(slotToDate(date, rangeEnd), 30).toISOString(),
          });
          rangeStart = sorted[i];
          rangeEnd = sorted[i];
        }
      }
      // Push final range
      result.push({
        start_datetime: slotToDate(date, rangeStart).toISOString(),
        end_datetime: addMinutes(slotToDate(date, rangeEnd), 30).toISOString(),
      });
    }
    return result;
  }, [selectedDates, slotsByDate]);

  return {
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
  };
}
