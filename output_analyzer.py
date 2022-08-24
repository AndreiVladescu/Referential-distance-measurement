from main import file_name, measurements_limit

# 5% error
def print_with_error(number, average, err = 0.10):
    if (average * (1 - err) < number and average * (1 + err) > number):
        return True
    return False

if __name__ == "__main__":
    input_file = open(file_name, "r")
    input_lines = input_file.readlines()
    index = 0
    sum = 0

    for line in input_lines:
        if (index >= measurements_limit):
            break
        if (line != "inf\n" and line != '0\n' and line!='\n'):
            line = line.strip('\n')
            index += 1
            sum += float(line)

    average = sum / index
    index = 0
    no_error_list = list()
    for line in input_lines:
        if (index >= measurements_limit):
            break
        if (line != "inf\n" and line != '0\n' and line!='\n'):
            line = line.strip('\n')
            if (print_with_error(float(line), average)):
                #print(line)
                no_error_list.append(float(line))

    sum = 0
    for measurement in no_error_list:
        sum += measurement
        print(measurement)

    average = sum / len(no_error_list)

    print("Average: " + str(average))

    input_file.close()