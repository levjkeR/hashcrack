import argparse
import multiprocessing
from hashlib import new
from itertools import product

parser = argparse.ArgumentParser(description="HashCrack Multiprocessing Tool",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=('Example\nhashcrack.py -n 6 -c lower -l 5 5 -a md5 -t '
                                         '37b19816109a32106d109e83bbb3c97d\nhashcrack.py -a sha256 -t '
                                         '3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c1835420b6b9942dd4f1b'))
parser.add_argument('-n', '--number', type=int, default=multiprocessing.cpu_count() // 2,
                    help='number of process')
parser.add_argument('-c', '--charset', default='lower', help='upper[A-Z], lower[a-z], digits[0-9], extended[A-za-z0-9]')
parser.add_argument('-l', '--length', nargs='*', type=int, default=[5, 5], help='plain text length range')
parser.add_argument('-a', '--alg', help='hash function algorithm')
parser.add_argument('-t', '--target', help='target hash', required=False)

args = parser.parse_args()
if len(args.length) == 1:
    args.length = [args.length[0], args.length[0]]
combinations = 0


# Проверка текста на совпадение исходному тексту
def check_hash(alg, target_hash, suspect_str):
    return True if new(alg, suspect_str.encode()).hexdigest() == target_hash else False


def result_check(result, pool):
    global combinations
    combinations += result[2]
    if result[0] is not None:
        print(f"\033[92m[!]\033[0m Plain text: {result[0]}\n\033[96m[~]\033[0m Combinations: {combinations}")
        pool.terminate()


# Генерация строк перебора(запускается в отдельном процессе)
def generator(charset, first_char, chunk_len, required_len, alg, target):
    """
    :param target: Хэш
    :param alg: Алгоритм хэширования
    :param charset: Алфавит
    :param first_char: Первый символ, с которого начинается генерируемая строка
    :param chunk_len: Максимальная длина, при которой дорустима генерация без разделения задач
    :param required_len: Требуемая длина, генерируемой строки
    :return: None если исходный текст не был найден, иначе исходный текст
    """
    chunk_completed_count = 0
    if required_len <= chunk_len:
        for comb in product(charset, repeat=required_len):
            suspect = ''.join(comb)
            chunk_completed_count += 1
            if check_hash(alg, target, suspect):
                return suspect, target, chunk_completed_count
    else:
        for comb in product(charset, repeat=chunk_len):
            suspect = first_char + ''.join(comb)
            chunk_completed_count += 1
            if check_hash(alg, target, suspect):
                return suspect, target, chunk_completed_count
    return None, target, chunk_completed_count


def bruteforce(num_process, charset, len_ranges, alg, target, chunk_size=1000000):
    """
    :param num_process: Количество используемых рабочих процессов
    :param charset: Алфавит
    :param len_ranges: Диапазоны длины исходной фразы
    :param alg: Алгоритм хэширования
    :param target: Хэш
    :param chunk_size: Размер чанка
    :return:
    """
    pool = multiprocessing.Pool(num_process)
    charset_len = len(charset)
    # Количество символов, при которых перебор
    # будет произведен без разделения вычислений
    chunk_len = 1
    while charset_len ** chunk_len <= chunk_size:
        chunk_len += 1
    chunk_len -= 1

    ext_callback = lambda result: result_check(result, pool)

    if chunk_len >= len_ranges[0]:
        for length in range(len_ranges[0], chunk_len + 1):
            pool.apply_async(generator, args=(charset, '', chunk_len, length, alg, target),
                             callback=ext_callback)

    for length in range(len_ranges[0], len_ranges[1] + 1):
        for comb in product(charset, repeat=length - chunk_len):
            first_char = ''.join(comb)
            pool.apply_async(generator, args=(charset, first_char, chunk_len, length, alg, target),
                             callback=ext_callback)

    pool.close()
    pool.join()


if __name__ == '__main__':
    from sys import platform
    import time

    # Поддержка цветного вывода в консаоль для Windows
    if 'win' in platform:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    charset = {'lower': 'abcdefghijklmnopqrstuvwxyz',
               'digits': '0123456789',
               'upper': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
               'extended': '''ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"#$%&\\'()*+,-./:;'''}

    print(f'''\033[32m
 ██░ ██  ▄▄▄        ██████  ██░ ██  ▄████▄   ██▀███   ▄▄▄       ▄████▄   ██ ▄█▀
▓██░ ██▒▒████▄    ▒██    ▒ ▓██░ ██▒▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▒██▀ ▀█   ██▄█▒ 
▒██▀▀██░▒██  ▀█▄  ░ ▓██▄   ▒██▀▀██░▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▒▓█    ▄ ▓███▄░ 
░▓█ ░██ ░██▄▄▄▄██   ▒   ██▒░▓█ ░██ ▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▓██ █▄ 
░▓█▒░██▓ ▓█   ▓██▒▒██████▒▒░▓█▒░██▓▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒ ▓███▀ ░▒██▒ █▄
 ▒ ░░▒░▒ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░ ░▒ ▒  ░▒ ▒▒ ▓▒ 
 ▒ ░▒░ ░  ▒   ▒▒ ░░ ░▒  ░ ░ ▒ ░▒░ ░  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░  ░  ▒   ░ ░▒ ▒░
 ░  ░░ ░  ░   ▒   ░  ░  ░   ░  ░░ ░░          ░░   ░   ░   ▒   ░        ░ ░░ ░ 
 ░  ░  ░      ░  ░      ░   ░  ░  ░░ ░         ░           ░  ░░ ░      ░  ░   
                                   ░                           ░                \033[0mv\033[31m0.2\033[0m
''')
    print(f"[+] Process number: \033[32m{args.number}\033[0m")
    print(f"\033[93m[+]\033[0m Target: {args.target}")
    start = time.time()
    bruteforce(num_process=args.number, charset=charset[str(args.charset)], len_ranges=args.length,
               alg=args.alg, target=args.target)
    # bruteforce(6, charset, (5, 5), 'sha256', '1115dd800feaacefdf481f1f9070374a2a81e27880f187396db67958b207cbad')
    end = time.time() - start
    c = round(combinations/end, 2)
    print(f"\033[34m[*]\033[0m Speed: {c} words/sec")
    print(f"\033[36m[*]\033[0m Elapsed time: {end} sec")

