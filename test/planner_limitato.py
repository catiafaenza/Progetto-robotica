from planning.pddl_planner import PDDLPlanner


class LimiteChiamatePlanner(Exception):
    pass


class PlannerLimitato:

    def __init__(
        self,
        planner: PDDLPlanner,
        max_chiamate: int,
    ) -> None:

        self.planner = planner
        self.max_chiamate = max_chiamate
        self.chiamate = 0

        self.nome_planner = (
            planner.nome_planner
        )

    def solve(
        self,
        problema,
    ):

        if (
            self.chiamate
            >= self.max_chiamate
        ):
            raise LimiteChiamatePlanner(
                f"Raggiunto limite di "
                f"{self.max_chiamate} chiamate."
            )

        self.chiamate += 1

        return self.planner.solve(
            problema
        )