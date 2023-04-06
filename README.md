# Wordle

Run wordle.py to generate the word lookup table (takes a few minutes).
Change LOAD_FROM_FILE in wordle.py to True to ensure the lookup table is simply read on subsequent runs.

Run play.py to use the wordle bot in a real game. 



Format the input as:
2 for green
1 for yellow
0 for black

The input pattern can be formatted as 
a comma separated list: 2,0,1,0,0
or a string: 20100

If you don't want to use the bot's suggestion, format the input as:
word,pattern
ex: salet,21002
or: salet,2,1,0,0,2