/** Date string in 'yyyy-MM-dd' format */
export type DateKey = string;

/** 30-minute slot index. 0 = 06:00, 1 = 06:30, ..., 47 = 05:30 next day */
export type SlotIndex = number;

/** Total number of 30-min slots in the timeline (06:00 to 05:30 next day) */
export const TOTAL_SLOTS = 48;

/** Hour offset where the timeline starts (06:00) */
export const TIMELINE_START_HOUR = 6;

/** Candidate output matching the existing API format */
export interface CandidateSlot {
  start_datetime: string; // ISO string
  end_datetime: string; // ISO string
}

/** Convert slot index to display time string (e.g. "06:00", "23:30") */
export function slotToTimeLabel(slot: SlotIndex): string {
  const totalMinutes = TIMELINE_START_HOUR * 60 + slot * 30;
  const hours = Math.floor(totalMinutes / 60) % 24;
  const minutes = totalMinutes % 60;
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

/** Convert a time string "HH:MM" to a slot index */
export function timeLabelToSlot(time: string): SlotIndex {
  const [h, m] = time.split(':').map(Number);
  // Adjust for timeline starting at 06:00
  let totalMinutes = h * 60 + m - TIMELINE_START_HOUR * 60;
  if (totalMinutes < 0) totalMinutes += 24 * 60; // wrap for times before 06:00 (next day)
  return Math.floor(totalMinutes / 30);
}
