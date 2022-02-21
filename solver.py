import requests
import json
import base64
import numpy as np
import random

def decode(word):
    b64_bytes = word.encode("ascii")
    word_bytes = base64.b64decode(b64_bytes)
    word = word_bytes.decode("ascii")
    return word

def cos_sim(guess_vec, secret_vec):
    return np.dot(guess_vec, secret_vec) / ( np.linalg.norm(guess_vec) * np.linalg.norm(secret_vec) )

secrets_base64 = []
with open("secrets_enc.txt") as secrets_enc:
    for line in secrets_enc:
        secrets_base64.append(line.strip())

def get_secret(puzzle_number):
    return secrets_base64[puzzle_number-1]
            
def get_secret_vec(puzzle_number):
    model_url = "https://semantle.novalis.org/model2/{}/{}".format(decode(get_secret(puzzle_number)), decode(get_secret(puzzle_number)))
    response = requests.get(model_url)
    data = json.loads(response.text)
    return data['vec']

def make_guess(guess, puzzle_number, secret_vec):
    model_url = "https://semantle.novalis.org/model2/{}/{}".format(decode(get_secret(puzzle_number)), guess)
    try:
        response = requests.get(model_url)
        data = json.loads(response.text)
    except:
        print("Oops, request failed or word not found")
        return -100, -1, guess

    guess_vec = data['vec']
    
    score = cos_sim(guess_vec, secret_vec) * 100.0
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

WORDS = []
with open("common.txt") as com:
    for line in com:
        WORDS.append(line.strip())

def print_win(guess_log):
    guess = guess_log[-1][2]
    num_guesses = len(guess_log)
    print("The word was {}. You win after {} guesses!".format(guess, num_guesses))

def solve(model, puzzle_number, tries=150, seed_words=[]):

    print("Attempting puzzle number {} in {} tries".format(puzzle_number, tries))

    candidates = []
    guesses_log = []
    visited = set()

    try:
        secret_vec = get_secret_vec(puzzle_number)
    except:
        print("Failed to get the secret word for this puzzle number, quitting")
        return
        
    if not seed_words:
        # 10 initial guesses from common English words
        seed_words = [random.choice(WORDS) for i in range(10)]

    for random_word in seed_words:
        if random_word not in visited:
            visited.add(random_word)
            result = make_guess(random_word, puzzle_number, secret_vec)
            guesses_log.append(result)
            if(result[1] == 1000):
                print_win(guesses_log)
                return
            if(result[0] > -100):
                candidates.append(result)
                if(result[1] > -1):
                    copies = result[1]//200 + 1   # Multiple copies of hot candidates
                    for i in range(copies):
                        candidates.append(result)
            
    guesses_log.append(result)
    candidates.append(result)

    candidates = sorted(candidates)

    while len(guesses_log) < tries:
        next_cand = candidates.pop()
        print("Looking for neighbours of ({}, {})".format(next_cand[2], f'{next_cand[0]:.2f}'))
        random_nbrs = []

        if(next_cand[1] == -1): # cold word
            exact_neighbors = model.most_similar(next_cand[2], topn=1500)
            for i in range(7):
                pick = random.choice(exact_neighbors[750:])[0]
                if pick not in visited:
                    visited.add(pick)
                    random_nbrs.append(pick)
            for i in range(3):
                pick = random.choice(WORDS)
                if pick not in visited:
                    visited.add(pick)
                    random_nbrs.append(pick)

        else: # hot hot hot
            radius = 1000 - next_cand[1] + 15
            exact_neighbors = model.most_similar(next_cand[2], topn=min(50, radius))
            for i in range(10):
                pick = random.choice(exact_neighbors)[0]
                if pick not in visited:
                    visited.add(pick)
                    random_nbrs.append(pick)

        for nbr in random_nbrs:
            result = make_guess(nbr, puzzle_number, secret_vec)
            guesses_log.append(result)
            if(result[1] == 1000):
                print_win(guesses_log)
                return
            if(result[0] > -100):
                candidates.append(result)
                if result[1] > -1:
                    copies = result[1]//200+1
                    for i in range(copies):
                        candidates.append(result)

        candidates = sorted(candidates)

    print("Fail! Best 5 guesses (out of {}) were - ".format(tries))
    for guess in sorted(guesses_log)[-5:]:
        print(guess)
    
    return
    
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
    solve(glove_model, puzzle_num, tries, seed_words)
