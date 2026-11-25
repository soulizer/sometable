"""Preview and execute row deduplication for a table."""

import json

from baserow.contrib.database.rows.actions import DeleteRowsActionType
from baserow.core.action.registries import action_type_registry

MAX_SCAN_ROWS = 50000
MAX_PREVIEW_GROUPS = 100
MAX_PREVIEW_ROWS_PER_GROUP = 10


class InvalidDedupeFields(Exception):
    pass


class InvalidDedupeRule(Exception):
    pass


class ManualKeepMissing(Exception):
    pass


def _get_key_columns(table, field_ids):
    if not field_ids or len(field_ids) > 10:
        raise InvalidDedupeFields()

    model = table.get_model()
    columns = []
    for field_id in field_ids:
        field = table.field_set.filter(id=field_id).first()
        if field is None:
            raise InvalidDedupeFields()
        try:
            model_field = model._meta.get_field(field.db_column)
        except Exception:  # noqa: BLE001 - invalid column for this model
            raise InvalidDedupeFields() from None
        if getattr(model_field, "many_to_many", False):
            # Link row / multiple collaborators have no single column value.
            raise InvalidDedupeFields()
        columns.append(field.db_column)
    return columns


def _normalize(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def get_duplicate_groups(table, field_ids, limit=MAX_PREVIEW_GROUPS, offset=0):
    """Returns duplicate groups plus the total number of duplicate groups."""

    columns = _get_key_columns(table, field_ids)
    model = table.get_model()
    rows = model.objects.values("id", *columns).order_by("id")[:MAX_SCAN_ROWS]

    groups = {}
    for row in rows:
        key = tuple(_normalize(row[column]) for column in columns)
        # Rows with every key field empty are not considered duplicates.
        if all(value == "" for value in key):
            continue
        group = groups.setdefault(
            key, {"key": key, "row_count": 0, "ids": [], "sample_rows": []}
        )
        group["row_count"] += 1
        group["ids"].append(row["id"])
        if len(group["sample_rows"]) < MAX_PREVIEW_ROWS_PER_GROUP:
            group["sample_rows"].append(
                {"id": row["id"], "values": list(key)}
            )

    duplicates = [
        group for group in groups.values() if group["row_count"] > 1
    ]
    duplicates.sort(key=lambda group: (-group["row_count"], group["ids"][0]))
    return duplicates[offset : offset + limit], len(duplicates)


def serialize_groups(groups, columns):
    result = []
    for group in groups:
        result.append(
            {
                "key": "||".join(group["key"]),
                "values": list(group["key"]),
                "row_count": group["row_count"],
                "rows": group["sample_rows"],
                "keep_id": group["ids"][0],
            }
        )
    return result


def plan_deletions(table, field_ids, rule, keep_row_ids=None):
    if rule not in ("oldest", "newest", "manual"):
        raise InvalidDedupeRule()

    groups, total = get_duplicate_groups(
        table, field_ids, limit=MAX_SCAN_ROWS
    )
    to_delete = []
    for group in groups:
        ids = group["ids"]
        if rule == "oldest":
            keep = ids[0]
        elif rule == "newest":
            keep = ids[-1]
        else:
            key = "||".join(group["key"])
            keep = (keep_row_ids or {}).get(key)
            if keep is None or int(keep) not in ids:
                raise ManualKeepMissing()

        to_delete.extend(row_id for row_id in ids if row_id != keep)

    return to_delete, total


def delete_duplicate_rows(user, table, row_ids, view=None) -> int:
    """Deletes the selected rows through the regular undoable action."""

    if not row_ids:
        return 0
    action_type_registry.get_by_type(DeleteRowsActionType).do(
        user, table, row_ids, view=view
    )
    return len(row_ids)
