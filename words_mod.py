# Function to generate valid words from given letters
from itertools import permutations
import random

def ShuffleString(s):
  L1=list(s)
  random.shuffle(L1)
  return "".join(L1)

# Load words from the word list file

def load_words(file_path):
    try:
        with open(file_path, 'r') as file:
            # Read all lines and strip any extra whitespace
            words = [line.strip() for line in file.readlines()]
        return list(set(words))
    except Exception as e:
        print(f"Error loading word list: {e}")
        return []


def generate_valid_words(letters, word_set, min_length=3):
    # List to store valid words
    valid_words = []

    # Iterate over all possible word lengths
    for length in range(min_length, len(letters) + 1):
        for perm in permutations(letters, length):
            candidate_word = ''.join(perm)
            if candidate_word in word_set:
                valid_words.append(candidate_word)  # Add valid word to the list

    return valid_words  # Return the list of valid words