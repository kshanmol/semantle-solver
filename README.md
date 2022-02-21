# semantle-solver
Dumb nearest-neighbours guided search to attempt Semantle puzzles. Succeeds sometimes.

Spoiler warning - Contains the secret words (in base64). Don't run the solver for future puzzles if you want to attempt them.

Running the solver
1. Clone the project and cd into the project root
2. Create a Python 3 virtual environment (https://virtualenv.pypa.io/en/latest/) and activate it
3. pip3 install -r requirements.txt
4. python3 solver.py puzzle_number attempts seed_words

puzzle_number - DO NOT put a future puzzle number it MIGHT accidently get solved

attempts - number of guesses

seed_words - comma separated initial guesses (e.g. "hello,hi"). if left empty, solver picks 10 common words at random instead.

