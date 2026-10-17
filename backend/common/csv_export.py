import csv
import io
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from fastapi.responses import Response

from backend.models.run_record import RunRecord


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def create_csv(records: Iterable[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> bytes:
    """Encode tabular data as a UTF-8 CSV that opens cleanly in spreadsheet apps."""
    rows = list(records)
    columns = list(fieldnames or dict.fromkeys(key for row in rows for key in row))
    if not columns:
        return b""

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="raise")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_value(row.get(key, "")) for key in columns})
    return output.getvalue().encode("utf-8-sig")


def run_csv_rows(run: RunRecord) -> list[dict[str, Any]]:
    """Convert a stored run into CSV rows without assuming a project's result schema."""
    results = run.result_data
    if isinstance(results, list) and not results:
        result_rows = [{}]
    elif isinstance(results, list) and all(isinstance(item, Mapping) for item in results):
        result_rows = [dict(item) for item in results]
    elif isinstance(results, Mapping):
        result_rows = [dict(results)]
    else:
        result_rows = [{"result": results}]

    metadata = {
        "run_id": run.id,
        "project": run.project_key,
        "created_at": run.created_at.isoformat(),
        "seed": run.seed,
        "algorithm_version": run.algorithm_version,
        "parameters": run.parameters,
    }
    return [{**row, **metadata} for row in result_rows]


def create_run_csv_response(run: RunRecord) -> Response:
    rows = run_csv_rows(run)
    filename = (
        f"{run.project_key}_{datetime.now(timezone.utc):%Y-%m-%d_%H%M%S}_"
        f"{run.id}.csv"
    )
    filename = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
    return Response(
        content=create_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
