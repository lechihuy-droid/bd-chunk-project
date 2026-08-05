from dataclasses import dataclass


@dataclass(frozen=True)
class DiffSide:
    run_id: str | None = None
    revision_id: str | None = None

    def validate(self) -> None:
        if (self.run_id is None) == (self.revision_id is None):
            raise ValueError("EXACTLY_ONE_OF_RUN_ID_OR_REVISION_ID")


@dataclass(frozen=True)
class DifferenceRequest:
    left: DiffSide
    right: DiffSide
