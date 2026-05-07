from __future__ import annotations

import json

from lib.premortemx_registry import advisory_delegation_plan


def main() -> None:
    print(json.dumps(advisory_delegation_plan(), indent=4))


if __name__ == "__main__":
    main()
