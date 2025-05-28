def paste_polygon(array, array_width, array_height, index_to_paste, width, height, val):
    for y in range(height):
        index = index_to_paste + (y * array_width)
        array[index: index + width] = val