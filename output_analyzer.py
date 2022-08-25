from main import file_name, measurements_limit

error_list = [0.05, 0.10, 0.15, 0.18, 0.20, 0.22]
output_file_name = "tests_output.txt"
output_file = open(output_file_name, "w")
actual_distance = 0.48

def print_with_error(number, average, err = 0.20):
    if (average * (1 - err) < number and average * (1 + err) > number):
        return True
    return False

def test(error):
    global output_file
    input_file = open(file_name, "r")
    input_lines = input_file.readlines()
    index = 0
    sum = 0

    for line in input_lines:
        if index >= measurements_limit:
            break
        if line != "inf\n" and line != '0\n' and line != '\n':
            line = line.strip('\n')
            index += 1
            sum += float(line)

    average = sum / index
    index = 0
    no_error_list = list()
    for line in input_lines:
        if index >= measurements_limit:
            break
        if line != "inf\n" and line != '0\n' and line != '\n':
            line = line.strip('\n')
            if print_with_error(float(line), average, error):
                no_error_list.append(float(line))

    sum = 0
    for measurement in no_error_list:
        sum += measurement
        print(measurement)

    average = sum / len(no_error_list)
    print("Average: " + str(average))

    reported_distance_difference = str(((average - actual_distance) / actual_distance) * 100)
    output_file.write('Average: ' + str(average) + ' m, ' + str(error) + ' % error, ' + reported_distance_difference + ' % more/less reported distance' + '\n')
    input_file.close()

if __name__ == "__main__":
    for error in error_list:
        test(error)
