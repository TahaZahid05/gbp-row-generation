from pyscipopt import Model, Conshdlr, SCIP_RESULT
from gbp.graph import Graph
from gbp.separation import SeparationProcedure

class CoveringConshdlr(Conshdlr):
    def __init__(self, scip_model, graph: Graph, x_vars: list, B: int, sep: SeparationProcedure):
        self.scip_model = scip_model  # Store strong reference
        self.graph = graph
        self.x_vars = x_vars
        self.B = B
        self.sep = sep
        self.n_lazy_conss = 0

    def _extract_sequence(self, solution=None) -> list[int]:
        sequence = [0] * self.B
        # Optimized: check only turn variables
        for i in range(1, self.B + 1):
            for v in range(self.graph.n_vertices):
                var = self.x_vars[v][i - 1]
                val = self.scip_model.getSolVal(solution, var)
                if val > 0.5:
                    sequence[i - 1] = v
                    break 
        return sequence

    def _add_covering_constraint(self, w: int):
        from pyscipopt import quicksum
        vars_in_cons = []
        for u, i in self.sep.get_covering_variables(w):
            vars_in_cons.append(self.x_vars[u][i - 1])
        
        self.scip_model.addCons(quicksum(vars_in_cons) >= 1, name=f"cov_{w}")
        self.n_lazy_conss += 1

    def conscheck(self, _constraints, solution, _checkintegrality, _checklprows, _printreason, _completely):
        sequence = self._extract_sequence(solution)
        is_valid, _, _ = self.sep.check_and_separate(sequence, max_cuts=1)
        if is_valid:
            return {"result": SCIP_RESULT.FEASIBLE}
        else:
            return {"result": SCIP_RESULT.INFEASIBLE}

    def consenfolp(self, _constraints, _nusefulconss, solinfeasible):
        # LP-level separation: tighten relaxation early for aggressive pruning
        
        if solinfeasible:
            return {"result": SCIP_RESULT.FEASIBLE}
        
        # Extract sequence and check coverage
        sequence = self._extract_sequence(None)
        is_valid, violations, max_v = self.sep.check_and_separate(sequence, max_cuts=None)
        
        if is_valid:
            return {"result": SCIP_RESULT.FEASIBLE}
        else:
            # Add covering constraints for all violations to tighten LP
            for w in violations:
                self._add_covering_constraint(w)
            return {"result": SCIP_RESULT.CONSADDED}

    def consenfops(self, _constraints, _nusefulconss, _solinfeasible, _objinfeasible):
        sequence = self._extract_sequence(None)
        is_valid, violations, max_v = self.sep.check_and_separate(sequence)
        if is_valid:
            print("[Handler] Feasible integral sequence found.", flush=True)
            return {"result": SCIP_RESULT.FEASIBLE}
        else:
            print(f"[Handler] Violations (integral): {len(violations)}, MaxViolation: {max_v:.2f}. Adding all as labels.", flush=True)
            for w in violations:
                self._add_covering_constraint(w)
            return {"result": SCIP_RESULT.CONSADDED}

    def conscopy(self, _sourcecons, _name, _sourcescip, _varmap, _consmap, _initial, _separate,
                 _enforce, _check, _propagate, _local, _modifiable, _dynamic, _removable, _stickingatnode):
        return {"constraint": None}

    def conslock(self, _constraint, _locktype, nlockspos, nlocksneg):
        for row in self.x_vars:
            for var in row:
                self.scip_model.addVarLocks(var, nlocksneg, nlockspos)


class GBPModel:
    def __init__(self, graph: Graph, B: int, S_init: list[int]):
        self.graph = graph
        self.B = B
        self.S_init = S_init
        self.scip = Model("GBP-IP")
        # Removing hideOutput so user can see standard SCIP progress logs
        # self.scip.hideOutput()
        
        # Set SCIP solver parameters for performance
        self.scip.setParam("limits/time", 300)
        self.scip.setParam("heuristics/feaspump/freq", -1)
        self.scip.setParam("separating/maxroundsroot", 0)

        # Decision variables: x[v][i-1] where i is turn 1..B
        from pyscipopt import quicksum
        self.x_vars = [([None] * B) for _ in range(graph.n_vertices)]
        for v in range(graph.n_vertices):
            for i in range(1, B + 1):
                var = self.scip.addVar(vtype="B", name=f"x_{v}_{i}")
                self.x_vars[v][i - 1] = var
                self.scip.chgVarBranchPriority(var, B - i + 1)
        
        # Constraint (6): each vertex at most once
        for v in range(graph.n_vertices):
            self.scip.addCons(quicksum(self.x_vars[v]) <= 1, name=f"c6_{v}")
            
        # Constraint (7): exactly one fire source per position
        for i in range(1, B + 1):
            vars_at_i = [self.x_vars[v][i - 1] for v in range(graph.n_vertices)]
            self.scip.addCons(quicksum(vars_at_i) == 1, name=f"c7_{i}")
            
        self.sep = SeparationProcedure(graph, B)
        self.conshdlr = CoveringConshdlr(self.scip, graph, self.x_vars, B, self.sep)
        self.scip.includeConshdlr(self.conshdlr, "CoveringConshdlr", "Adds covering constraints lazily",
                                  needscons=False)
        self.n_initial_conss = 0

        # Preseed initial covering constraints bounds leveraging S_init sequence
        for w in S_init:
            vars_in_cons = []
            for u, i in self.sep.get_covering_variables(w):
                vars_in_cons.append(self.x_vars[u][i - 1])
            
            if vars_in_cons:
                self.scip.addCons(quicksum(vars_in_cons) >= 1, name=f"init_cov_{w}")
                self.n_initial_conss += 1
        
        # Warm-start with BFF-d solution
        self._inject_warm_start()

    def _inject_warm_start(self):
        """
        Inject the BFF-d solution as a warm start.
        This allows SCIP to start branch-and-bound with a known feasible sequence,
        enabling immediate pruning instead of wasting time in the feasibility phase.
        """
        # Guard: ensure S_init has exactly B elements
        if len(self.S_init) != self.B:
            return
        
        sol = self.scip.createSol()
        
        for i, v in enumerate(self.S_init):
            self.scip.setSolVal(sol, self.x_vars[v][i], 1.0)
        
        self.scip.addSol(sol)

    def solve(self) -> tuple[str, list[int] | None]:
        self.scip.optimize()
        status = self.scip.getStatus()
        
        ret_val = (status, None, self.n_initial_conss, self.conshdlr.n_lazy_conss)
        
        if status == "infeasible":
            return ret_val
            
        if self.scip.getNSols() > 0:
            sol = self.scip.getBestSol()
            sequence = [0] * self.B
            for i in range(1, self.B + 1):
                for v in range(self.graph.n_vertices):
                    var = self.x_vars[v][i - 1]
                    if self.scip.getSolVal(sol, var) > 0.5:
                        sequence[i - 1] = v
                        break
            return "feasible", sequence, self.n_initial_conss, self.conshdlr.n_lazy_conss
            
        # If not feasible and not infeasible, it's likely unknown/limit reached
        return ret_val
