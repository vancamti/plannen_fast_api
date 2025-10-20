import enum

# from app import schemas


class Status(enum.Enum):
    KLAD = 10, "Klad"
    KLAAR_VOOR_ACTIVATIE = 25, "Klaar voor activatie"
    ACTIEF = "75", "Actief"

    def __init__(self, id_, naam):
        self.id = id_
        self.naam = naam

    # def to_model(self) -> schemas.StatusType:
    #     return schemas.StatusType(
    #         id=self.id,
    #         naam=self.naam,
    #     )

    @classmethod
    def from_id(cls, type_id):
        for status in Status:
            if status.id == type_id:
                return status
        raise ValueError(f"ID '{type_id}' is geen status type.")


class Bestandssoort(enum.Enum):
    BEHEERSPLAN = 1, "Beheersplan"
    PLAN = 2, "Plan"
    SAMENSTELLING_BEHEERSCOMMISSIE = 3, "Samenstelling beheerscommissie"
    BIJLAGE = 4, "Bijlage"
    PRVIATE_BIJLAGE = 5, "Private bijlage"
    ONOERENDERFGOEDRICHTPLAN = 6, "Onroerenderfgoedrichtplan"
    ACTIEPROGRAMMA = 7, "Actieprogramma"
    EINDRAPPORT = 8, "Eindrapport"
    MB = 9, "MB"

    def __init__(self, id_, naam):
        self.id = id_
        self.naam = naam

    @classmethod
    def from_id(cls, type_id):
        for status in Status:
            if status.id == type_id:
                return status
        raise ValueError(f"ID '{type_id}' is geen status type.")
