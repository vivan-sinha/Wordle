"""Authors v1.0 (Fall 2022): Andy Dong"""
LOAD_FROM_FILE = False
import pickle
import math
import os

"""Importing word files"""
with open('data/possible_words.txt') as file:
    possible_words = [line.rstrip() for line in file]
with open('data/allowed_guesses.txt') as file:
    allowed_guesses = [line.rstrip() for line in file]

"""## Implementing the Game Logic (Read Only)

We then implement the logic of the game by first computing the pattern that we will see for a given pair of guess and secret word. The function `compute_pattern` takes in a guess and a secret word, and returns an integer tuple of length 5 that represents the color pattern, where an entry of 2 represents green in the corresponding position, 1 represents yellow, and 0 represents gray.

There's an edge case that we will need to consider, which is when the guess and/or the secret word contains multiple of the same letter. The rule here is that green (match in the correct spot) always has the highest priority, yellow (match in the wrong spot) prioritizes letters in earlier positions of your guess, and each letter in the secret word can only correspond to one letter in the guess. Take a look at the example below.

- If the secret word is "abide" and the guess is "three", the pattern would be (0, 0, 0, 0, 2). Position 5 is an exact match so it has the highest priority to be green. Position 4 is indeed a match in the wrong spot, but since the "e" in "abide" is already taken, it cannot match to that same "e" again.
"""

def compute_pattern(guess, answer):
    # Returns a length 5 tuple
    
    pattern = [0, 0, 0, 0, 0]
    taken = [False, False, False, False, False]
    
    # Green pass
    for i in range(5):
        if guess[i] == answer[i]:
            # If it's an exact match, color it green, and mark it as taken
            # so that the yellow pass doesn't match to it again
            pattern[i] = 2
            taken[i] = True
    
    # Yellow pass
    for i in range(5):
        if pattern[i] == 2:
            # If a spot is already colored green, we skip it
            continue
        query = guess[i]
        for j in range(5):
            if query == answer[j] and taken[j] is False:
                # If there is a misplaced match that is not taken by the
                # green pass or a previous yellow pass, we color it yellow
                # and mark it as taken
                pattern[i] = 1
                taken[j] = True
                break
    
    return tuple(pattern)

if LOAD_FROM_FILE:
    print("Please wait a moment while the bot loads the word table.")
else:
    print("Please wait a few minutes while the bot writes the word table.")
    print("Next time you run the bot make sure to change LOAD_FROM_FILE to True")

pattern_table = {}

if not LOAD_FROM_FILE:
    for guess in allowed_guesses:
        word_table = {}
        for answer in possible_words:
            word_table[answer] = compute_pattern(guess, answer)
        pattern_table[guess] = word_table

    if not os.path.exists('checkpoint'):
        os.mkdir('checkpoint')
    file = open('checkpoint/pattern_table', 'ab')
    pickle.dump(pattern_table, file)
    file.close()
else:
    file = open('checkpoint/pattern_table', 'rb')
    pattern_table = pickle.load(file)
    file.close()

"""
Takes in a guess and the current alphabet. 
Returns a dictionary that maps each color pattern to a list of possible words
"""
def divide_alphabet(guess, alphabet):
    pattern_to_subgroup = {}
    
    for secret_word in alphabet:
      pattern = pattern_table[guess][secret_word]
      
      if pattern not in pattern_to_subgroup:
        pattern_to_subgroup.update({pattern: []})
        
      pattern_to_subgroup[pattern] += [secret_word]
    
    return pattern_to_subgroup

def prob_dist(pattern_groups):
    # returns a probability distribution in the form of a list
    # for example, if the probability distribution is
    # P(pattern_1) = 0.2, P(pattern_2) = 0.3, P(pattern_3) = 0.5,
    # this function should return [0.2, 0.3, 0.5].
    dist = []
    
    total = 0
    for pattern, group in pattern_groups.items():
      dist += [len(group)]
      total += len(group)
      
    dist = [x/total for x in dist]
    return dist

def entropy(dist):
    ent = 0
    for p in dist:
      ent += p * math.log2(1/p)
    return ent

"""
Takes in the current alphabet and all legal guesses
Returns the guess which provides the most information
"""
def find_best_guess(alphabet, allowed_guesses):
    word, highest = None, 0
    
    for guess in allowed_guesses:
        pattern_groups = divide_alphabet(guess, alphabet)
        ent = entropy(prob_dist(pattern_groups))
        if ent > highest:
          word = guess
          highest = ent
          
    return word

"""
Best Wordle Opener (greedy)
"""

# best_opener = find_best_guess(possible_words, allowed_guesses)
best_opener = 'soare'

def find_best_guess_optimized(alphabet, hard=False):
    if len(alphabet) == 2315:
        # if it's the opening guess, we directly output
        return best_opener
    if len(alphabet) == 1:
        # if we are certain what the secret word is, directly guess it
        return alphabet[0]
    if len(alphabet) <= 3 or hard:
        # if the alphabet is small, limit our guess to within the alphabet
        return find_best_guess(alphabet, alphabet)
    # otherwise, we apply no optimization
    return find_best_guess(alphabet, allowed_guesses)

def create_wordle_game(true_answer):
    def wordle_game(guess):
        # takes in a guess and outputs the pattern
        return pattern_table[guess][true_answer]
    
    return wordle_game

def play_wordle(wordle_game, print_guesses=False):
    alphabet = possible_words
    num_guesses = 0
    while True:
        num_guesses += 1
        guess = find_best_guess_optimized(alphabet)
        color_pattern = wordle_game(guess)
        if print_guesses:
            print(f'Guess {num_guesses}: {guess}  |  Pattern: {color_pattern}')
        if color_pattern == (2, 2, 2, 2, 2):
            # correct answer!
            break
        alphabet = divide_alphabet(guess, alphabet)[color_pattern]

    return num_guesses

class WordleBot:
    def __init__(self, hard=False):
        # initialize for a new game
        self.alphabet = possible_words
        self.next = None
        self.counter = 1
        self.hard = hard
        self.suggest()
    
    def suggest(self):
        self.next = find_best_guess_optimized(self.alphabet, self.hard)
        print('Next word to guess:', self.next)
    
    def observe(self, pattern):
        # after a guess, feed the pattern to the bot to update
        # then, the bot suggests a word to guess
        if pattern == (2,2,2,2,2):
            print("We got it in", self.counter, 'tries!')
            return True
            
        assert len(self.next) == len(pattern) == 5
        self.alphabet = divide_alphabet(self.next, self.alphabet)[pattern]
        self.suggest()
        self.counter += 1
        return False
    
    def restart(self):
        self.alphabet = possible_words
        self.next = None
        self.counter = 1
        self.suggest()
        return
    
    def take_input(self):
        while True:
            try:
                user_input = input("What was the pattern? ")
                input_as_list = user_input.split(',')
                
                # If they want to input their own guess
                if len(input_as_list) == 6 or len(input_as_list) == 2:
                    if len(input_as_list[0]) == 5:
                        self.next = input_as_list[0]
                        input_as_list = input_as_list[1:]
                
                previous_pattern = tuple(int(x) for x in input_as_list)
                
                
                valid = len(previous_pattern) == 5
                if not valid:
                    if len(input_as_list[0]) == 5:
                        previous_pattern = tuple(int(input_as_list[0][i]) for i in range(5))
                    
                    valid = True
                    
                for x in previous_pattern:
                    if x < 0 or x > 2:
                        valid = False
                        
                if valid: break
                else: print("Please input a list of 5 integers (0-2) seperated by commas.")
                
            except ValueError:
                print("Please input a list of 5 integers (0-2) seperated by commas.")
        
        return previous_pattern
    