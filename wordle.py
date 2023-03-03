"""Authors v1.0 (Fall 2022): Andy Dong"""

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

load_from_file = False
if load_from_file:
    print("Please wait a moment while the bot loads the word table.")
else:
    print("Please wait a few minutes while the bot writes the word table.")
    print("Next time you run the bot make sure to change load_from_file to True")

pattern_table = {}

if not load_from_file:
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

"""## Guess Strategy

We use the term "alphabet of a random variable" to mean the set of potential values it could take on with positive probability (not to be confused with the English alphabet). For example, the alphabet of $X$ is the set of 2315 possible secret words.

Fix a time index $t$. Let $X_t = X|Y_1, \ldots, Y_{t-1}$ where $Y_i$ is the pattern we observe after our $i$th guess, which we assume has already happened. Then, we can see that $X_t$ also has a uniform distribution over its alphabet because the color pattens we observe only tell us which secret words are possible and which are not, but do not change the relative probabilities assigned to the possible secret words. In other words, we can think of each guess as "narrowing down" the alphabet of $X$.

Let $Y_{t,k}$ be the resulting pattern for guessing the word $k$ at timestep $t$. Both $X_t$ and $Y_{t,k}$ are random variables. Note that the index $k$ here is a word we guess. We want to minimize the conditional entropy $H(X_t|Y_{t,k})$ over $k \in$ `allowed_guesses` since it's the "leftover uncertainty" about $X_t$ after observing the color pattern for $k$. Namely, if $Y_t=Y_{t,k}$ (meaning that we guess word $k$), then $H(X_t|Y_{t,k})=\log_2 |\text{alphabet of $X_{t+1}$}|$ since $X_{t+1}$ is still uniform over its alphabet.

Recall that $$H(X_t)=I(X_t;Y_{t,k})+H(X_t|Y_{t,k}).$$

Since $H(X_t)$ is a constant given a particular observation of $Y_1, \ldots, Y_{t-1} = (y_1, \ldots, y_{t-1})$, minimizing $H(X_t|Y_{t,k})$ is equivalent to maximizing $I(X_t;Y_{t,k})$.

But what is $I(X_t;Y_{t,k})$? The mutual information is the amount of information in $X_t$ gained through observing $Y_{t,k}$, which equals the amount of information in $Y_{t,k}$ gained through observing $X_t$. However, if we know $X_t$ (which means we peek at the answer), then $Y_{t,k}|X_t$ is deterministic! Knowing $X_t$ would reduce the uncertainty in $Y_{t,k}$ from $H(Y_{t,k})$ to $0$, which means that

$$I(X_t;Y_{t,k})=H(Y_{t,k})-H(Y_{t,k}|X_t)=H(Y_{t,k})-0=H(Y_{t,k}).$$

The conclusion is that we reformulate the problem of minimizing $H(X_t|Y_{t,k})$ into maximizing $I(X_t;Y_{t,k})$ then into maximizing $H(Y_{t,k})$. Please make sure you fully understand our steps above!

**Let's start by implementating `divide_alphabet`**, which takes in a guess and the current alphabet. The function would split the alphabet into smaller subgroups. Namely, it returns a dictionary that maps from the set of possible color patterns to the set of secret words such that `pattern_table[guess][secret_word]` is that color pattern. For example, if `guess` is "shake" and `alphabet` is {shape, shake, shame}, then the function should return the mapping (2,2,2,2,2)$\to${shake}, (2,2,2,0,2)$\to${shape, shame}.
"""

def divide_alphabet(guess, alphabet):
    pattern_to_subgroup = {}
    
    for secret_word in alphabet:
      pattern = pattern_table[guess][secret_word]
      
      if pattern not in pattern_to_subgroup:
        pattern_to_subgroup.update({pattern: []})
        
      pattern_to_subgroup[pattern] += [secret_word]
    
    return pattern_to_subgroup

"""Then, since $X$ is uniform over its alphabet, the probability that we observe each pattern is proportional to the number of words in that subgroup. **In the following cell, implement `prob_dist`**, which takes in the output of the above function and returns the probability distribution over the set of possible patterns. For the same example above, this function would take in the mapping (2,2,2,2,2)$\to${shake}, (2,2,2,0,2)$\to${shape, shame} and return $\left[\frac{1}{3}, \frac{2}{3}\right]$ This is the distribution of $Y_{t,k}$."""

def prob_dist(pattern_groups):
    # returns a probability distribution in the form of a list
    # for example, if the probability distribution is
    # P(pattern_1) = 0.2, P(pattern_2) = 0.3, P(pattern_3) = 0.5,
    # this function should return [0.2, 0.3, 0.5]. Order doesn't matter
    dist = []
    
    total = 0
    for pattern, group in pattern_groups.items():
      dist += [len(group)]
      total += len(group)
      
    dist = [x/total for x in dist]
    return dist

"""**In the cell below, implement the function `entropy`**, which takes in a probability distribution (in a list format, like the output of the previous function) and outputs its entropy. You may assume that the distribution has no entry of $0$ and is a valid distribution. From this we can find $H(Y_k)$, which is the quantity we seek to maximize."""

def entropy(dist):
    ent = 0
    for p in dist:
      ent += p * math.log2(1/p)
    return ent

"""Now we're into business! We've specified how to quantitatively compare quality of guesses, and **let's now implement `find_best_guess`**, which takes in the alphabet of $X_t$ and returns the best guess to make. Recall that the best guess is a guess $k\in$ `allowed_guesses` that maximizes $H(Y_{t,k})$."""

def find_best_guess(alphabet, allowed_guesses):
    word, highest = None, 0
    
    for guess in allowed_guesses:
        pattern_groups = divide_alphabet(guess, alphabet)
        ent = entropy(prob_dist(pattern_groups))
        if ent > highest:
          word = guess
          highest = ent
          
    return word

"""## Best Wordle Opener

Here is the question that Wordle lovers are looking for: What is the best opening guess under our scheme? (**Important Note:** this is the best opener given our assumptions that the secret word is picked *uniformly at random* over the 2315 possible secret words, and we are using a greedy algorithm to get the most information out of each guess. This is not guaranteed to be the truly optimal guess.)
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

"""## Wordle Bot! (Optional)

For the final part of the lab, let's use what we've built so far and transform it into a Wordle bot! **Implement the following class `WordleBot`** that interactively outputs its suggested guess, and receives inputs that consist of your actual guess and the pattern displayed. Feel free to modify the code below to tailor the bot to your liking, such as outputting more than one suggested word, outputting the word along with its mutual information with the secret word, or giving it a better user interface in your personal project!
"""

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
            print("We got it in", bot.counter, 'tries!')
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
                
                # If they wan
                if len(input_as_list) == 6:
                    if len(input_as_list[0]) == 5:
                        self.next = input_as_list[0]
                        input_as_list = input_as_list[1:]
                        
                previous_pattern = tuple(int(x) for x in input_as_list)
                
                valid = len(previous_pattern) == 5
                if not valid:
                    if len(user_input) == 5:
                        previous_pattern = tuple(int(user_input[i]) for i in range(5))
                    
                    valid = True
                    
                for x in previous_pattern:
                    if x < 0 or x > 2:
                        valid = False
                        
                if valid: break
                else: print("Please input a list of 5 integers (0-2) seperated by commas.")
                
            except ValueError:
                print("Please input a list of 5 integers (0-2) seperated by commas.")
        
        return previous_pattern

user_input = input("Are you playing hard mode? (y/n) ")

if user_input == 'y' or user_input == 'yes':
    bot = WordleBot(hard=True)
else: bot = WordleBot()

previous_pattern = (0, 0, 0, 0, 0)
done = False

while not done:
    previous_pattern = bot.take_input()
    done = bot.observe(previous_pattern)
    
    if done:
        user_input = input("Would you like to play again? (y/n) ")
        if user_input == 'y' or user_input == 'yes':
            bot.restart()
            previous_pattern = (0, 0, 0, 0, 0)
            done = False