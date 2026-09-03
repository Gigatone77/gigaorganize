import os
import shutil
from pathlib import Path

from gigaorganize.models import OrganizeAction, OrganizePlan, OrganizeResult
from gigaorganize.constants import EXT_TO_CATEGORY, HOME


def plan_organize(
    source_dir: Path,
    target_base: Path = HOME / "Documents" / "GigaOrganize",
    sort_by_type: bool = True,
    sort_by_date: bool = False,
) -> OrganizePlan:
    actions: list[OrganizeAction] = []
    conflicts: list[OrganizeAction] = []
    file_count = 0

    if not source_dir.is_dir():
        return OrganizePlan(actions=[], source_dir=source_dir, file_count=0)

    for entry in os.scandir(source_dir):
        if not entry.is_file():
            continue
        fp = Path(entry.path)
        file_count += 1
        ext = fp.suffix.lower()
        category = EXT_TO_CATEGORY.get(ext, "Other")

        if sort_by_type:
            dest_dir = target_base / category
        elif sort_by_date:
            import time
            t = time.localtime(fp.stat().st_mtime)
            dest_dir = target_base / f"{t.tm_year}" / f"{t.tm_mon:02d}"
        else:
            dest_dir = target_base

        dest = dest_dir / fp.name
        dest_dir.mkdir(parents=True, exist_ok=True)

        action = OrganizeAction(
            source=fp,
            destination=dest,
            rule_name=category,
            action_type="move",
            reason=f"Move to {category}",
        )

        if dest.exists() and dest != fp:
            conflicts.append(action)
        else:
            actions.append(action)

    return OrganizePlan(
        actions=actions,
        source_dir=source_dir,
        file_count=file_count,
        conflicts=conflicts,
    )


def apply_plan(plan: OrganizePlan) -> OrganizeResult:
    moved = 0
    skipped = 0
    errors: list[tuple[Path, str]] = []
    taken: list[OrganizeAction] = []

    for action in plan.actions:
        try:
            action.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(action.source), str(action.destination))
            moved += 1
            taken.append(action)
        except Exception as e:
            errors.append((action.source, str(e)))
            skipped += 1

    for action in plan.conflicts:
        skipped += 1

    return OrganizeResult(
        moved=moved,
        skipped=skipped,
        errors=errors,
        actions_taken=taken,
    )


def undo_plan(result: OrganizeResult) -> int:
    undone = 0
    for action in reversed(result.actions_taken):
        try:
            original_dir = action.destination.parent
            shutil.move(str(action.destination), str(action.source))
            undone += 1
        except Exception:
            pass
    return undone
