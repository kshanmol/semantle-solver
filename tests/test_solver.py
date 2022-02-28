from solver import Solver

def test_init(model):
    solver = Solver(model, 1, 50)
    assert(solver.puzzle_num == 1)
    assert(solver.tries == 50)
    assert(len(solver.seed_words) == 10)

def test_init_sw(model):
    solver = Solver(model, 5, 150, ["hello", "world"])
    assert(solver.puzzle_num == 5)
    assert(solver.tries == 150)
    assert(len(solver.seed_words) == 2)

def test_run_solve_success(model):
    solver = Solver(model, 1, 10, ["hello", "first", "forever"])
    result = solver.solve()
    assert(result)

def test_run_solve_failure(model):
    solver = Solver(model, 18, 10)
    result = solver.solve()
    assert(not result)

def test_empty():
    try:
        solver = Solver()
    except Exception as e:
        assert(isinstance(e, TypeError))
