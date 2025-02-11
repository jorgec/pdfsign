import string
import random
from datetime import datetime


def generate_random_string(length: int = 64, numbers_only: bool = False) -> str:
    random.seed(datetime.now())
    choices = string.ascii_lowercase
    if numbers_only:
        generated_str = ''.join(str(random.randint(0, 9)) for i in range(length))
    else:
        generated_str = ''.join(random.choice(choices) for i in range(length))
    return generated_str
