import sys
from TametsiGenerator import get_difficulty_steps, smooth_difficulty


def CL_survey(num):
  first_half = ['']
  second_half = None
  squared = num ** 2

  for i in range((squared + 1) // 2):
    temp = []
    for s in first_half:
      temp.extend([s + '.', s + '*', s + '?'])
    first_half = temp

    if i == squared // 2 - 1:
      second_half = temp

  print(first_half)
  print(second_half)

  with open('survey_{num}x{num}.txt'.format(num=num), 'w') as file:
    for s1 in first_half:
      for s2 in second_half:
        s = s1 + s2

        output = ','.join(map(str, [s, smooth_difficulty(num, num, s), get_difficulty_steps(num, num, s, cache_only=True)]))
        print(output)
        file.write(output + '\n')


if __name__ == '__main__':
  num = int(sys.argv[1]) if len(sys.argv) > 1 else 2
  CL_survey(num)
