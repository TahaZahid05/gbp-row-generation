#include <scip/scip.h>
#include <scip/scipdefplugins.h>
#include <scip/cons_linear.h>

#include <vector>
#include <queue>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>

/* ================= BFS / DISTANCE ================= */

static void bfs_from_source(int source, int n,
    const int* adj_data, const int* adj_offsets,
    std::vector<int>& dist)
{
    dist.assign(n, -1);
    dist[source] = 0;
    std::queue<int> q;
    q.push(source);
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int idx = adj_offsets[u]; idx < adj_offsets[u + 1]; idx++) {
            int v = adj_data[idx];
            if (v >= 0 && v < n && dist[v] == -1) {
                dist[v] = dist[u] + 1;
                q.push(v);
            }
        }
    }
}

static int get_dist(int u, int v, int n,
    const int* adj_data, const int* adj_offsets,
    std::vector<std::vector<int>>* cache)
{
    if (u < 0 || v < 0 || u >= n || v >= n) return -1;
    if ((*cache)[u].empty())
        bfs_from_source(u, n, adj_data, adj_offsets, (*cache)[u]);
    return (*cache)[u][v];
}

/* ================= CONSTRAINT HANDLER DATA ================= */

struct ConshdlrData {
    int n_vertices;
    int B;
    SCIP_VAR*** x_vars;
    const int* adj_data;
    const int* adj_offsets;
    std::vector<std::vector<int>>* dist_cache;
    int* n_lazy_conss;
};

/* ================= COVERAGE ================= */

static bool check_and_get_violations(
    SCIP* scip, SCIP_SOL* sol,
    ConshdlrData* data,
    std::vector<int>& violations)
{
    violations.clear();
    int B = data->B;
    int n = data->n_vertices;

    std::vector<int> sequence(B, -1);
    for (int i = 0; i < B; i++)
        for (int v = 0; v < n; v++)
            if (SCIPgetSolVal(scip, sol, data->x_vars[v][i]) > 0.5) {
                sequence[i] = v;
                break;
            }

    for (int u = 0; u < n; u++) {
        double min_cov = 1e18;
        for (int i = 0; i < B; i++) {
            int vi = sequence[i];
            if (vi < 0) continue;
            int d = get_dist(vi, u, n,
                data->adj_data, data->adj_offsets, data->dist_cache);
            if (d >= 0) {
                double c = (double)d - (double)(B - (i + 1));
                if (c < min_cov) min_cov = c;
            }
        }
        if (min_cov > 1e-6)
            violations.push_back(u);
    }
    return violations.empty();
}

static SCIP_RETCODE add_cover_row(
    SCIP* scip, SCIP_CONSHDLR* conshdlr,
    ConshdlrData* data, int w,
    SCIP_Bool* infeasible_out)
{
    int B = data->B;
    int n = data->n_vertices;

    std::vector<SCIP_VAR*> vars;
    std::vector<SCIP_Real> coefs;

    for (int u = 0; u < n; u++) {
        int d = get_dist(u, w, n,
            data->adj_data, data->adj_offsets, data->dist_cache);
        if (d < 0 || d > B - 1) continue;
        for (int i = 1; i <= B; i++) {
            if (d <= B - i) {
                vars.push_back(data->x_vars[u][i - 1]);
                coefs.push_back(1.0);
            }
        }
    }

    if (vars.empty()) return SCIP_OKAY;

    SCIP_ROW* row;
    SCIP_CALL(SCIPcreateEmptyRowConshdlr(
        scip, &row, conshdlr, "cover",
        1.0, SCIPinfinity(scip),
        FALSE, FALSE, TRUE));
    SCIP_CALL(SCIPaddVarsToRow(scip, row,
        (int)vars.size(), vars.data(), coefs.data()));
    SCIP_Bool inf = FALSE;
    SCIP_CALL(SCIPaddRow(scip, row, TRUE, &inf));
    SCIP_CALL(SCIPreleaseRow(scip, &row));

    if (infeasible_out) *infeasible_out = inf;
    if (data->n_lazy_conss) (*data->n_lazy_conss)++;

    return SCIP_OKAY;
}

/* ================= CALLBACKS ================= */

static SCIP_DECL_CONSCHECK(consCheck)
{
    ConshdlrData* data = (ConshdlrData*)SCIPconshdlrGetData(conshdlr);
    if (!data || !data->x_vars) { *result = SCIP_FEASIBLE; return SCIP_OKAY; }
    std::vector<int> violations;
    bool ok = check_and_get_violations(scip, sol, data, violations);
    *result = ok ? SCIP_FEASIBLE : SCIP_INFEASIBLE;
    return SCIP_OKAY;
}

static SCIP_DECL_CONSENFOLP(consEnfolp)
{
    ConshdlrData* data = (ConshdlrData*)SCIPconshdlrGetData(conshdlr);
    if (!data || !data->x_vars) { *result = SCIP_FEASIBLE; return SCIP_OKAY; }
    std::vector<int> violations;
    bool ok = check_and_get_violations(scip, NULL, data, violations);
    if (ok) { *result = SCIP_FEASIBLE; return SCIP_OKAY; }
    SCIP_Bool any_inf = FALSE;
    for (int w : violations) {
        SCIP_Bool inf = FALSE;
        SCIP_CALL(add_cover_row(scip, conshdlr, data, w, &inf));
        if (inf) any_inf = TRUE;
    }
    *result = any_inf ? SCIP_CUTOFF : SCIP_SEPARATED;
    return SCIP_OKAY;
}

static SCIP_DECL_CONSENFOPS(consEnfops)
{
    ConshdlrData* data = (ConshdlrData*)SCIPconshdlrGetData(conshdlr);
    if (!data || !data->x_vars) { *result = SCIP_FEASIBLE; return SCIP_OKAY; }
    std::vector<int> violations;
    bool ok = check_and_get_violations(scip, NULL, data, violations);
    *result = ok ? SCIP_FEASIBLE : SCIP_INFEASIBLE;
    return SCIP_OKAY;
}

static SCIP_DECL_CONSLOCK(consLock)
{
    ConshdlrData* data = (ConshdlrData*)SCIPconshdlrGetData(conshdlr);
    if (!data || !data->x_vars) return SCIP_OKAY;
    for (int v = 0; v < data->n_vertices; v++)
        for (int i = 0; i < data->B; i++)
            SCIPaddVarLocks(scip, data->x_vars[v][i], nlockspos, nlocksneg);
    return SCIP_OKAY;
}

/* ================= MAIN ================= */

extern "C" __declspec(dllexport) int solve_gbp(
    int n_vertices, int B,
    const int* adj_data, const int* adj_offsets,
    const int* s_init, int s_init_len,
    int* result_sequence,
    int* n_initial_conss_out,
    int* n_lazy_conss_out)
{
    for (int i = 0; i < B; i++) result_sequence[i] = -1;

    int n_init_conss = 0;
    int n_lazy_conss = 0;
    int ret = -1;

    auto* dist_cache = new std::vector<std::vector<int>>(n_vertices);
    auto* chdata = new ConshdlrData();
    chdata->n_lazy_conss = &n_lazy_conss;
    chdata->x_vars = NULL;

    SCIP* scip = NULL;
    SCIP_VAR*** x_vars = NULL;

    SCIP_RETCODE rc = SCIPcreate(&scip);
    if (rc != SCIP_OKAY) goto cleanup;

    SCIPsetMessagehdlrQuiet(scip, TRUE);

    rc = SCIPincludeDefaultPlugins(scip);
    if (rc != SCIP_OKAY) goto cleanup;

    rc = SCIPcreateProbBasic(scip, "GBP");
    if (rc != SCIP_OKAY) goto cleanup;

    SCIPsetObjsense(scip, SCIP_OBJSENSE_MINIMIZE);
    SCIPsetRealParam(scip, "limits/time", 300.0);
    SCIPsetIntParam(scip, "heuristics/feaspump/freq", -1);
    SCIPsetIntParam(scip, "separating/maxroundsroot", 0);
    SCIPsetIntParam(scip, "presolving/maxrounds", 5);
    SCIPsetIntParam(scip, "presolving/maxrestarts", 0);
    SCIPsetIntParam(scip, "propagating/maxroundsroot", 3);
    SCIPsetIntParam(scip, "misc/usesymmetry", 0);
    SCIPsetIntParam(scip, "separating/maxrounds", 0);

    x_vars = (SCIP_VAR***)calloc(n_vertices, sizeof(SCIP_VAR**));
    for (int v = 0; v < n_vertices; v++) {
        x_vars[v] = (SCIP_VAR**)calloc(B, sizeof(SCIP_VAR*));
        for (int i = 0; i < B; i++) {
            char name[64];
            snprintf(name, sizeof(name), "x_%d_%d", v, i + 1);
            rc = SCIPcreateVarBasic(scip, &x_vars[v][i], name,
                    0.0, 1.0, 0.0, SCIP_VARTYPE_BINARY);
            if (rc != SCIP_OKAY) goto cleanup;
            SCIPaddVar(scip, x_vars[v][i]);
            SCIPchgVarBranchPriority(scip, x_vars[v][i], B - i);
        }
    }

    {
        std::vector<SCIP_Real> ones(B, 1.0);
        for (int v = 0; v < n_vertices; v++) {
            SCIP_CONS* cons;
            rc = SCIPcreateConsBasicLinear(scip, &cons, "",
                    B, x_vars[v], ones.data(), -SCIPinfinity(scip), 1.0);
            if (rc != SCIP_OKAY) goto cleanup;
            SCIPaddCons(scip, cons);
            SCIPreleaseCons(scip, &cons);
        }
    }

    {
        std::vector<SCIP_Real> ones_n(n_vertices, 1.0);
        for (int i = 0; i < B; i++) {
            std::vector<SCIP_VAR*> col(n_vertices);
            for (int v = 0; v < n_vertices; v++) col[v] = x_vars[v][i];
            SCIP_CONS* cons;
            rc = SCIPcreateConsBasicLinear(scip, &cons, "",
                n_vertices, col.data(), ones_n.data(), 1.0, 1.0);
            if (rc != SCIP_OKAY) goto cleanup;
            SCIPaddCons(scip, cons);
            SCIPreleaseCons(scip, &cons);
        }
    }

    chdata->n_vertices = n_vertices;
    chdata->B = B;
    chdata->x_vars = x_vars;
    chdata->adj_data = adj_data;
    chdata->adj_offsets = adj_offsets;
    chdata->dist_cache = dist_cache;

    {
        SCIP_CONSHDLR* conshdlr = NULL;
        rc = SCIPincludeConshdlrBasic(scip, &conshdlr,
                "covering", "Covering constraints",
                100, 100, -1, FALSE,
                consEnfolp, consEnfops,
                consCheck, consLock,
                (SCIP_CONSHDLRDATA*)chdata);
        if (rc != SCIP_OKAY) goto cleanup;
    }

    for (int idx = 0; idx < s_init_len && idx < B; idx++) {
        int w = s_init[idx];
        if (w < 0 || w >= n_vertices) continue;
        std::vector<SCIP_VAR*> vars;
        std::vector<SCIP_Real> coefs;
        for (int u = 0; u < n_vertices; u++) {
            int d = get_dist(u, w, n_vertices, adj_data, adj_offsets, dist_cache);
            if (d < 0 || d > B - 1) continue;
            for (int i = 1; i <= B; i++) {
                if (d <= B - i) {
                    vars.push_back(x_vars[u][i - 1]);
                    coefs.push_back(1.0);
                }
            }
        }
        if (!vars.empty()) {
            SCIP_CONS* cons;
            if (SCIPcreateConsBasicLinear(scip, &cons, "",
                    (int)vars.size(), vars.data(), coefs.data(),
                    1.0, SCIPinfinity(scip)) == SCIP_OKAY) {
                SCIPaddCons(scip, cons);
                SCIPreleaseCons(scip, &cons);
                n_init_conss++;
            }
        }
    }

    if (s_init_len == B) {
        SCIP_SOL* sol;
        if (SCIPcreatePartialSol(scip, &sol, NULL) == SCIP_OKAY) {
            for (int i = 0; i < B; i++) {
                int v = s_init[i];
                if (v >= 0 && v < n_vertices)
                    SCIPsetSolVal(scip, sol, x_vars[v][i], 1.0);
            }
            SCIP_Bool stored;
            SCIPaddSol(scip, sol, &stored);
            SCIPfreeSol(scip, &sol);
        }
    }

    rc = SCIPsolve(scip);
    if (rc != SCIP_OKAY) goto cleanup;

    {
        SCIP_STATUS status = SCIPgetStatus(scip);
        if (status == SCIP_STATUS_INFEASIBLE) {
            ret = 0;
        } else if (SCIPgetNSols(scip) > 0) {
            SCIP_SOL* sol = SCIPgetBestSol(scip);
            for (int i = 0; i < B; i++)
                for (int v = 0; v < n_vertices; v++)
                    if (SCIPgetSolVal(scip, sol, x_vars[v][i]) > 0.5) {
                        result_sequence[i] = v;
                        break;
                    }
            ret = 1;
        }
    }

cleanup:
    if (n_initial_conss_out) *n_initial_conss_out = n_init_conss;
    if (n_lazy_conss_out) *n_lazy_conss_out = n_lazy_conss;

    // Null out chdata before SCIPfree to prevent callbacks accessing freed memory
    if (chdata) {
        chdata->x_vars = NULL;
        chdata->adj_data = NULL;
        chdata->adj_offsets = NULL;
        chdata->dist_cache = NULL;
        chdata->n_lazy_conss = NULL;
        chdata->n_vertices = 0;
        chdata->B = 0;
    }

    // SCIP 10 owns vars after SCIPaddVar — do NOT call SCIPreleaseVar
    if (x_vars) {
        for (int v = 0; v < n_vertices; v++)
            if (x_vars[v]) free(x_vars[v]);
        free(x_vars);
    }

    if (scip) SCIPfree(&scip);

    delete chdata;
    delete dist_cache;

    return ret;
}