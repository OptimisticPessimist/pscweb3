"""Repair consistency between schedule polls, rehearsals, and attendance targets.

Usage:
    python scripts/repair_schedule_poll_consistency.py --dry-run
    python scripts/repair_schedule_poll_consistency.py --apply
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import async_session_maker
from src.db.models import (
    AttendanceEvent,
    AttendanceTarget,
    Character,
    Line,
    ProjectMember,
    Rehearsal,
    RehearsalCast,
    RehearsalParticipant,
    RehearsalSchedule,
    Scene,
    SchedulePoll,
    SchedulePollAnswer,
    SchedulePollCandidate,
    SchedulePollTarget,
)


@dataclass(frozen=True)
class DesiredRehearsalState:
    participant_roles: dict[UUID, str | None]
    cast_assignments: dict[UUID, UUID]
    attendance_target_ids: set[UUID]
    attendance_statuses: dict[UUID, str]


def _poll_answer_to_attendance_status(status: str | None) -> str:
    if status == "ok":
        return "ok"
    if status == "ng":
        return "ng"
    return "pending"


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _same_datetime(left: datetime, right: datetime, tolerance_seconds: int = 60) -> bool:
    delta = abs((_to_naive_utc(left) - _to_naive_utc(right)).total_seconds())
    return delta <= tolerance_seconds


async def _get_project_member_map(
    db: AsyncSession, project_id: UUID
) -> dict[UUID, ProjectMember]:
    result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    return {member.user_id: member for member in result.scalars().all()}


async def _backfill_poll_targets(
    db: AsyncSession,
    poll: SchedulePoll,
    member_map: dict[UUID, ProjectMember],
    apply: bool,
) -> int:
    if poll.targets:
        return 0

    if apply:
        for user_id in member_map:
            db.add(SchedulePollTarget(poll_id=poll.id, user_id=user_id))

    return len(member_map)


async def _build_desired_state(
    db: AsyncSession,
    *,
    project_id: UUID,
    scene_ids: list[UUID],
    answers: list[SchedulePollAnswer],
    attendance_policy: str,
) -> DesiredRehearsalState:
    answer_statuses = {answer.user_id: answer.status for answer in answers}
    attendee_statuses = {
        user_id: status for user_id, status in answer_statuses.items() if status in ("ok", "maybe")
    }
    attendee_ids = set(attendee_statuses)
    member_map = await _get_project_member_map(db, project_id)

    cast_assignments: dict[UUID, UUID] = {}
    cast_user_ids: set[UUID] = set()

    if scene_ids and attendee_ids:
        scene_result = await db.execute(
            select(Scene)
            .where(Scene.id.in_(scene_ids))
            .options(
                selectinload(Scene.lines).options(
                    selectinload(Line.character).options(selectinload(Character.castings))
                )
            )
        )
        scenes = scene_result.scalars().all()
        characters: dict[UUID, Character] = {}
        for scene in scenes:
            for line in scene.lines:
                if line.character_id and line.character:
                    characters[line.character_id] = line.character

        for character_id, character in characters.items():
            candidate_castings = [
                casting for casting in character.castings if casting.user_id in attendee_ids
            ]
            if not candidate_castings:
                continue
            candidate_castings.sort(
                key=lambda casting: (
                    0 if attendee_statuses.get(casting.user_id) == "ok" else 1,
                    str(casting.user_id),
                )
            )
            selected_casting = candidate_castings[0]
            cast_assignments[character_id] = selected_casting.user_id
            cast_user_ids.add(selected_casting.user_id)

    participant_roles: dict[UUID, str | None] = {}
    for user_id in attendee_ids:
        member = member_map.get(user_id)
        staff_role = member.default_staff_role if member else None
        if staff_role or user_id not in cast_user_ids:
            participant_roles[user_id] = staff_role

    attendance_target_ids = attendee_ids
    if attendance_policy == "all-poll-targets":
        attendance_target_ids = set(member_map)
    attendance_statuses = {
        user_id: _poll_answer_to_attendance_status(answer_statuses.get(user_id))
        for user_id in attendance_target_ids
    }

    return DesiredRehearsalState(
        participant_roles=participant_roles,
        cast_assignments=cast_assignments,
        attendance_target_ids=attendance_target_ids,
        attendance_statuses=attendance_statuses,
    )


async def _find_matching_rehearsals(
    db: AsyncSession,
    *,
    project_id: UUID,
    poll_id: UUID,
    candidate: SchedulePollCandidate,
) -> list[Rehearsal]:
    duration_minutes = int(
        (candidate.end_datetime - candidate.start_datetime).total_seconds() / 60
    )
    result = await db.execute(
        select(Rehearsal)
        .join(RehearsalSchedule)
        .where(RehearsalSchedule.project_id == project_id)
        .options(
            selectinload(Rehearsal.scenes),
            selectinload(Rehearsal.participants),
            selectinload(Rehearsal.casts),
        )
    )
    rehearsals = result.scalars().all()

    matches = []
    for rehearsal in rehearsals:
        if not _same_datetime(rehearsal.date, candidate.start_datetime):
            continue
        if rehearsal.duration_minutes != duration_minutes:
            continue
        if rehearsal.notes and f"日程調整({poll_id})" in rehearsal.notes:
            matches.append(rehearsal)
            continue
        matches.append(rehearsal)

    return matches


async def _find_matching_attendance_events(
    db: AsyncSession, *, project_id: UUID, rehearsal: Rehearsal
) -> list[AttendanceEvent]:
    result = await db.execute(
        select(AttendanceEvent)
        .where(AttendanceEvent.project_id == project_id)
        .options(selectinload(AttendanceEvent.targets))
    )
    events = result.scalars().all()
    return [
        event
        for event in events
        if event.schedule_date and _same_datetime(event.schedule_date, rehearsal.date)
    ]


def _diff_rehearsal(
    rehearsal: Rehearsal, desired: DesiredRehearsalState
) -> tuple[set[UUID], set[UUID], set[UUID], set[UUID]]:
    current_participants = {participant.user_id for participant in rehearsal.participants}
    desired_participants = set(desired.participant_roles)
    current_cast_users = {cast.user_id for cast in rehearsal.casts}
    desired_cast_users = set(desired.cast_assignments.values())
    return (
        desired_participants - current_participants,
        current_participants - desired_participants,
        desired_cast_users - current_cast_users,
        current_cast_users - desired_cast_users,
    )


async def _apply_rehearsal_state(
    db: AsyncSession, rehearsal: Rehearsal, desired: DesiredRehearsalState
) -> None:
    await db.execute(
        delete(RehearsalParticipant).where(RehearsalParticipant.rehearsal_id == rehearsal.id)
    )
    await db.execute(delete(RehearsalCast).where(RehearsalCast.rehearsal_id == rehearsal.id))

    for user_id, staff_role in desired.participant_roles.items():
        db.add(
            RehearsalParticipant(
                rehearsal_id=rehearsal.id,
                user_id=user_id,
                staff_role=staff_role,
            )
        )

    for character_id, user_id in desired.cast_assignments.items():
        db.add(
            RehearsalCast(
                rehearsal_id=rehearsal.id,
                character_id=character_id,
                user_id=user_id,
            )
        )


async def _apply_attendance_state(
    db: AsyncSession, event: AttendanceEvent, desired: DesiredRehearsalState
) -> None:
    current_targets = {target.user_id: target for target in event.targets}

    for user_id, target in current_targets.items():
        if user_id not in desired.attendance_target_ids:
            await db.delete(target)

    for user_id in desired.attendance_target_ids:
        desired_status = desired.attendance_statuses.get(user_id, "pending")
        target = current_targets.get(user_id)
        if target is None:
            db.add(AttendanceTarget(event_id=event.id, user_id=user_id, status=desired_status))
        elif target.status == "pending" and desired_status != "pending":
            target.status = desired_status


async def repair(args: argparse.Namespace) -> int:
    apply = bool(args.apply)
    changed = 0
    skipped = 0

    async with async_session_maker() as db:
        poll_stmt = select(SchedulePoll).options(
            selectinload(SchedulePoll.targets),
            selectinload(SchedulePoll.candidates)
            .selectinload(SchedulePollCandidate.answers)
            .selectinload(SchedulePollAnswer.user),
        )
        if args.project_id:
            poll_stmt = poll_stmt.where(SchedulePoll.project_id == UUID(args.project_id))

        polls = (await db.execute(poll_stmt)).scalars().all()
        print(f"polls_checked={len(polls)} apply={apply}")

        for poll in polls:
            member_map = await _get_project_member_map(db, poll.project_id)
            target_backfill_count = await _backfill_poll_targets(db, poll, member_map, apply)
            if target_backfill_count:
                changed += target_backfill_count
                print(f"poll={poll.id} target_backfill={target_backfill_count}")

            for candidate in poll.candidates:
                rehearsals = await _find_matching_rehearsals(
                    db,
                    project_id=poll.project_id,
                    poll_id=poll.id,
                    candidate=candidate,
                )
                if len(rehearsals) != 1:
                    skipped += 1
                    print(
                        f"skip candidate={candidate.id} reason=ambiguous_rehearsal "
                        f"matches={len(rehearsals)}"
                    )
                    continue

                rehearsal = rehearsals[0]
                desired = await _build_desired_state(
                    db,
                    project_id=poll.project_id,
                    scene_ids=[scene.id for scene in rehearsal.scenes],
                    answers=candidate.answers,
                    attendance_policy=args.attendance_policy,
                )
                participant_add, participant_remove, cast_add, cast_remove = _diff_rehearsal(
                    rehearsal, desired
                )
                if participant_add or participant_remove or cast_add or cast_remove:
                    changed += 1
                    print(
                        f"rehearsal={rehearsal.id} candidate={candidate.id} "
                        f"participants +{len(participant_add)} -{len(participant_remove)} "
                        f"casts +{len(cast_add)} -{len(cast_remove)}"
                    )
                    if apply:
                        await _apply_rehearsal_state(db, rehearsal, desired)

                events = await _find_matching_attendance_events(
                    db, project_id=poll.project_id, rehearsal=rehearsal
                )
                if len(events) != 1:
                    skipped += 1
                    print(
                        f"skip rehearsal={rehearsal.id} reason=ambiguous_attendance "
                        f"matches={len(events)}"
                    )
                    continue

                event = events[0]
                current_statuses = {target.user_id: target.status for target in event.targets}
                current_target_ids = set(current_statuses)
                add_targets = desired.attendance_target_ids - current_target_ids
                remove_targets = current_target_ids - desired.attendance_target_ids
                update_statuses = {
                    user_id
                    for user_id in desired.attendance_target_ids & current_target_ids
                    if current_statuses[user_id] == "pending"
                    and desired.attendance_statuses.get(user_id, "pending") != "pending"
                }
                if add_targets or remove_targets or update_statuses:
                    changed += 1
                    print(
                        f"attendance_event={event.id} rehearsal={rehearsal.id} "
                        f"targets +{len(add_targets)} -{len(remove_targets)} "
                        f"status_updates={len(update_statuses)}"
                    )
                    if apply:
                        await _apply_attendance_state(db, event, desired)

        if apply:
            await db.commit()

    print(f"done changed_items={changed} skipped_items={skipped}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--project-id")
    parser.add_argument(
        "--attendance-policy",
        choices=["voters-only", "all-poll-targets"],
        default="voters-only",
        help="How to derive AttendanceTarget rows from a matched poll candidate.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(repair(parse_args())))
