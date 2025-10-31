import random


def flip_coin():
    return "HEAD 🪙" if random.random() >= 0.5 else "TAIL 🪙"

def dice_roll():
    return str(random.randint(1, 6))

def dice_roll_20():
    num = random.randint(1, 20)
    if num == 20:
        return f"NATURAL 20💥 - Critical Success! 🎯"
    if num == 1:
        return f"1😬 - Critical Fail... 💀"
    return f"{num} 🪄"

def num_gen(num):
    return str(random.randint(1, num))

def destiny_decoder():
    DECODER = {
        0: "AI says yes, but do you trust AI?",
        1: "AI confidence level: 99.9%",
        2: "The neural network predicts success",
        3: "Machine learning model trained… verdict: YES",
        4: "Code compiled with no errors—green light",
        5: "The system predicts optimal results",
        6: "Data analysis complete—outcome is positive",
        7: "Server response: Approved!",
        8: "The AI overlords approve—go for it!",
        9: "All systems go—future looks bright!",

        10: "Computing probability… 0.00001%",
        11: "Probability matrix says… unlikely",
        12: "Debugging results: No solution found",
        13: "Fatal error: Outcome is NO",
        14: "Red alert: High chance of failure detected",
        15: "Data corrupted—outcome not favorable",
        16: "Insufficient data—proceed at your own risk",

        17: "System overload—reboot and ask again",
        18: "Error 404: Answer Not Found",
        19: "AI model needs more training—ask again soon",
    }
    return DECODER[random.randint(0, 19)]



if __name__ == '__main__':
    print(dice_roll())
    print(flip_coin())
    print(num_gen(10))
    print(num_gen(100))
    print(destiny_decoder())
    print(destiny_decoder())
    print(destiny_decoder())