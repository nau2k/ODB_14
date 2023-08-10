import random
import string

UNICODE_ASCII_CHARACTERS = string.ascii_letters + string.digits


def generate_token(length=30, chars=UNICODE_ASCII_CHARACTERS):
    generator = random.SystemRandom()
    return "".join(generator.choice(chars) for index in range(length))
