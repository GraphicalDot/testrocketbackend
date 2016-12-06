starting_delimeter_found = False
ending_delimeter_found = False
seperated_contents = []
for elem in contents:
    elem_ = str(elem)

    # the starting and ending are in the same element
    if elem_.count('%^&amp;*()') == 2:
        seperated_contents.append([])
        seperated_contents[-1].append(elem)
        continue

    # the starting has been found but not the ending
    if elem_.count('%^&amp;*()') == 1 and starting_delimeter_found is False:
        starting_delimeter_found = True
        seperated_contents.append([])
        seperated_contents[-1].append(elem)
        continue

    # ending not found, so continue append to the last group
    if elem_.count('%^&amp;*()') == 0 and starting_delimeter_found is True:
        seperated_contents[-1].append(elem)
        continue

    # ending delimeter is found
    if elem_.count('%^&amp;*()') == 1 and starting_delimeter_found is True:
        seperated_contents[-1].append(elem)
        starting_delimeter_found = False
        ending_delimeter_found = False
        continue
