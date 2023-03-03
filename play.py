from wordle import WordleBot

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