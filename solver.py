import requests
import json
import base64
import numpy as np
import random

class Solver:

    def __init__(self, model, puzzle_num, tries=150, seed_words=None):
        self.model = model
        self.puzzle_num = puzzle_num
        self.secret_vector = None
        self.tries = tries
        self.WORDS = []
        with open("common.txt") as com:
            for line in com:
                self.WORDS.append(line.strip())
        if seed_words:
            self.seed_words = seed_words
        else:
            self.seed_words = [random.choice(self.WORDS) for i in range(10)]

        self.secrets_base64 = []
        with open("secrets_enc.txt") as secrets_enc:
            for line in secrets_enc:
                self.secrets_base64.append(line.strip())

    @staticmethod
    def decode(word):
        b64_bytes = word.encode("ascii")
        word_bytes = base64.b64decode(b64_bytes)
        word = word_bytes.decode("ascii")
        return word

    @staticmethod
    def cos_sim(guess_vec, secret_vec):
        return np.dot(guess_vec, secret_vec) / ( np.linalg.norm(guess_vec) * np.linalg.norm(secret_vec) )

    def get_secret(self):
        return self.secrets_base64[self.puzzle_num-1]

    def get_secret_vec(self):
        if self.secret_vector is None:
            model_url = "https://semantle.novalis.org/model2/{}/{}".format(Solver.decode(self.get_secret()), Solver.decode(self.get_secret()))
            try:
                response = requests.get(model_url)
                data = json.loads(response.text)
                self.secret_vector = data['vec']
            except:
                print("Oops, failed to get vector for the secret word")
        return self.secret_vector

    def make_guess(self, guess):
        model_url = "https://semantle.novalis.org/model2/{}/{}".format(Solver.decode(self.get_secret()), guess)
        try:
            response = requests.get(model_url)
            data = json.loads(response.text)
        except:
            print("Oops, request failed or word not found")
            return -100, -1, guess

        guess_vec = data['vec']
        score = Solver.cos_sim(guess_vec, self.get_secret_vec()) * 100.0

        perc = -1 # for cold guesses
        if 'percentile' in data.keys():
            perc = data['percentile']
            if perc == 1000:
                print("You win! The word is {}".format(guess))
            else:
                print("{}\n{} | (Getting close - {}/1000)".format(guess, f'{score:.2f}', perc))
        else:
            print("{}\n{} | (Cold)".format(guess, f'{score:.2f}'))
        return score, perc, guess

    def win_condition(self, guess_log):
        return guess_log[-1][1] == 1000

    def print_end_state(self, guess_log):
        num_guesses = len(guess_log)
        if self.win_condition(guess_log):
            guess = guess_log[-1][2]
            print("The word was {}. You win after {} guesses!".format(guess, num_guesses))
        else:
            print("Fail! Best 5 guesses (out of {}) were - ".format(num_guesses))
            for guess in sorted(guess_log)[-5:]: print(guess)

    @staticmethod
    def add_candidate(candidates, guess_result):
        if guess_result[0] > -100: # Don't add failed guesses
            candidates.append(guess_result)
            if(guess_result[1] > -1):
                copies = guess_result[1]//200 + 1 # Add multiple copies of hot candidates
                candidates.extend([guess_result] * copies)
        return candidates

    def solve(self, tries=None, seed_words=None):

        if tries:
            self.tries = tries
        if seed_words:
            self.seed_words = seed_words

        print("Attempting puzzle number {} in {} tries".format(self.puzzle_num, self.tries))

        candidates = []
        guesses_log = []
        visited = set()

        for random_word in self.seed_words:
            if random_word not in visited:
                visited.add(random_word)
                result = self.make_guess(random_word)
                guesses_log.append(result)
                if self.win_condition(guesses_log):
                    self.print_end_state(guesses_log)
                    return True
                candidates = Solver.add_candidate(candidates, result)
               
        candidates = sorted(candidates)

        while len(guesses_log) < self.tries:
            next_cand = candidates.pop()
            print("Looking for neighbours of ({}, {})".format(next_cand[2], f'{next_cand[0]:.2f}'))
            random_nbrs = []
            if(next_cand[1] == -1): # cold word
                exact_neighbors = self.model.most_similar(next_cand[2], topn=1500)
                for i in range(7):
                    pick = random.choice(exact_neighbors[750:])[0]
                    if pick not in visited:
                        visited.add(pick)
                        random_nbrs.append(pick)
                for i in range(3):
                    pick = random.choice(self.WORDS)
                    if pick not in visited:
                        visited.add(pick)
                        random_nbrs.append(pick)
            else: # hot hot hot
                radius = 1000 - next_cand[1] + 15
                exact_neighbors = self.model.most_similar(next_cand[2], topn=min(50, radius))
                for i in range(10):
                    pick = random.choice(exact_neighbors)[0]
                    if pick not in visited:
                        visited.add(pick)
                        random_nbrs.append(pick)

            for nbr in random_nbrs:
                result = self.make_guess(nbr)
                guesses_log.append(result)
                if self.win_condition(guesses_log):
                    self.print_end_state(guesses_log)
                    return True
                candidates = Solver.add_candidate(candidates, result)

            candidates = sorted(candidates)

        self.print_end_state(guesses_log)
        return False
    
import sys
import gensim.downloader as api

if __name__ == "__main__":
    puzzle_num, tries, seed_words = 1, 250, []
    if len(sys.argv) == 2:
        puzzle_num = int(sys.argv[1])
    elif len(sys.argv) == 3:
        puzzle_num, tries = int(sys.argv[1]), int(sys.argv[2])
    elif len(sys.argv) == 4:
        puzzle_num, tries = int(sys.argv[1]), int(sys.argv[2])
        seed_words = sys.argv[3].split(',')

    glove_model = api.load('glove-wiki-gigaword-200')
    solver = Solver(glove_model, puzzle_num, tries, seed_words)
    solver.solve()
