import random
import string

def generate_unique_strings(length, count):
    unique_strings = set()

    while len(unique_strings) < count:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        unique_strings.add(random_string)

    return unique_strings

def save_to_file(filename, data):
    with open(filename, 'w') as file:
        for item in data:
            file.write(f"{item}\n")

if __name__ == "__main__":
    length = int(input("Введите длину строк: "))
    count = int(input("Введите количество строк: "))
    
    unique_strings = generate_unique_strings(length, count)
    
    save_to_file("numbers.txt", unique_strings)
    
    print(f"{count} уникальных строк длиной {length} символов сохранены в файле numbers.txt")
