import numpy as np

def apply_mask_pattern(data_array, pattern_array, pattern_num, size):
    """
    Apply one of the 8 standard QR code mask patterns
    
    Args:
        data_array: RGB image array (flattened)
        pattern_array: Pattern array indicating where data can be placed (0 = data, 1 = pattern)
        pattern_num: Integer 0-7 representing which mask pattern to use
        size: Size of the QR code matrix
    
    Returns:
        Masked RGB image array
    """
    masked_array = data_array.copy()
    
    for y in range(size):
        for x in range(size):
            index = y * size + x
            
            # Only apply mask to data areas (pattern_array == 0)
            if pattern_array[index] == 0:
                should_flip = False
                
                # Apply the appropriate mask pattern
                if pattern_num == 0:  # (i + j) % 2 == 0
                    should_flip = (y + x) % 2 == 0
                elif pattern_num == 1:  # i % 2 == 0
                    should_flip = y % 2 == 0
                elif pattern_num == 2:  # j % 3 == 0
                    should_flip = x % 3 == 0
                elif pattern_num == 3:  # (i + j) % 3 == 0
                    should_flip = (y + x) % 3 == 0
                elif pattern_num == 4:  # (floor(i/2) + floor(j/3)) % 2 == 0
                    should_flip = ((y // 2) + (x // 3)) % 2 == 0
                elif pattern_num == 5:  # (i*j) % 2 + (i*j) % 3 == 0
                    should_flip = ((y * x) % 2 + (y * x) % 3) == 0
                elif pattern_num == 6:  # ((i*j) % 2 + (i*j) % 3) % 2 == 0
                    should_flip = (((y * x) % 2 + (y * x) % 3) % 2) == 0
                elif pattern_num == 7:  # ((i+j) % 2 + (i*j) % 3) % 2 == 0
                    should_flip = (((y + x) % 2 + (y * x) % 3) % 2) == 0
                
                # Flip the pixel if mask condition is met
                if should_flip:
                    rgb_index = index * 3
                    current_color = masked_array[rgb_index]
                    new_color = 255 if current_color == 0 else 0
                    masked_array[rgb_index:rgb_index + 3] = new_color
    
    return masked_array

def calculate_penalty_score(image_array, size):
    score = 0
    
    # Convert RGB array to binary for easier processing
    binary_matrix = []
    for y in range(size):
        row = []
        for x in range(size):
            rgb_index = (y * size + x) * 3
            # 0 = black, 1 = white
            pixel_value = 1 if image_array[rgb_index] == 255 else 0
            row.append(pixel_value)
        binary_matrix.append(row)
    
    # Rule 1: Adjacent modules in row/column with same color
    # 3 points for each group of 5+ same-colored modules
    for y in range(size):
        count = 1
        for x in range(1, size):
            if binary_matrix[y][x] == binary_matrix[y][x-1]:
                count += 1
            else:
                if count >= 5:
                    score += 3 + (count - 5)
                count = 1
        if count >= 5:
            score += 3 + (count - 5)
    
    # Check columns
    for x in range(size):
        count = 1
        for y in range(1, size):
            if binary_matrix[y][x] == binary_matrix[y-1][x]:
                count += 1
            else:
                if count >= 5:
                    score += 3 + (count - 5)
                count = 1
        if count >= 5:
            score += 3 + (count - 5)
    
    # Rule 2: 2x2 blocks of same color
    # 3 points for each 2x2 block
    for y in range(size - 1):
        for x in range(size - 1):
            if (binary_matrix[y][x] == binary_matrix[y][x+1] == 
                binary_matrix[y+1][x] == binary_matrix[y+1][x+1]):
                score += 3
    
    # Rule 3: Patterns similar to finder patterns (1:1:3:1:1)
    # 40 points for each occurrence
    finder_pattern1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]  # 10111010000
    finder_pattern2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]  # 00001011101
    
    # Check rows
    for y in range(size):
        row = binary_matrix[y]
        for x in range(size - 10):
            if row[x:x+11] == finder_pattern1 or row[x:x+11] == finder_pattern2:
                score += 40
    
    # Check columns
    for x in range(size):
        col = [binary_matrix[y][x] for y in range(size)]
        for y in range(size - 10):
            if col[y:y+11] == finder_pattern1 or col[y:y+11] == finder_pattern2:
                score += 40
    
    # Rule 4: Balance of dark and light modules
    # 10 points for every 5% deviation from 50%
    total_modules = size * size
    dark_modules = sum(sum(1 for pixel in row if pixel == 0) for row in binary_matrix)
    dark_ratio = dark_modules / total_modules
    deviation = abs(dark_ratio - 0.5)
    score += int(deviation * 20) * 10
    
    return score

def find_best_mask(image_array, pattern_array, size):
    best_mask = 0
    best_score = float('inf')
    best_array = None
    
    for mask_num in range(8):
        masked_array = apply_mask_pattern(image_array, pattern_array, mask_num, size)
        score = calculate_penalty_score(masked_array, size)
        
        if score < best_score:
            best_score = score
            best_mask = mask_num
            best_array = masked_array.copy()
    
    return best_mask, best_array, best_score