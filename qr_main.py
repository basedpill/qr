# qr_code.py
import numpy as np
from reedsolo import RSCodec
from PIL import Image
import static_values
import masking
import polygon

class QR_Code:
    def __init__(self, message : str, errorCorrection : str):
        #Set and validate the error correction level
        self.errorCorrection = errorCorrection.upper()
        if not (self.errorCorrection == "L" or self.errorCorrection == "M" or self.errorCorrection == "Q" or self.errorCorrection == "H"):
            raise Exception("Error correction level must be either 'L', 'M', 'Q' or 'H'.")

        #Set our variables
        self.message = message
        self.charCount = len(message)

        #Get the data type, the message converted to ones and zeroes and get the QR version (1-40)
        self.dataType, self.encodedMessage, = self.__Find_Data_Type_And_Encode_Message(self.message) 
        self.version = self.__Find_Version(self.dataType, self.charCount, self.errorCorrection)

        #Now pad the data and convert to bytes
        self.dataBlock = self.__Assemble_Bit_String(self.dataType, self.errorCorrection, self.charCount, self.encodedMessage, self.version)

        #Create our template images
        self.imgSize : int = static_values.QRCodeSizeArray[self.version - 1]
        self.QRCodePatternsArray, self.QRCodeImageArray = self.__Create_QR_Code_Images(self.version, self.imgSize)

        #Apply Reed-Solomon enocding to our message
        self.finalDataBlock = self.__Apply_Reed_Solomon(self.dataBlock, self.errorCorrection, self.QRCodePatternsArray)

        #Fill out the image with our data
        self.QRCodeImageArray = self.__Fill_QR_Code_Image(self.QRCodeImageArray, self.QRCodePatternsArray, self.imgSize, self.finalDataBlock)

        #Apply the best mask pattern
        self.QRCodeImageArray = self.__Apply_Best_Mask(self.QRCodeImageArray, self.QRCodePatternsArray, self.imgSize)


        #Important Variables:
        #
        #self.dataBlock -> A numpy array of 0s and 1s that is printed onto the QR code. Shouldn't be needed for masking
        #                  but I figured you'd want to know what it's for
        #
        #self.imgSize -> An integer equal to the width and height of the QR code
        #
        #self.QRCodePatternsArray -> A numpy array of size self.imgSize * self.imgSize, consisting of integers 0 and 1.
        #                            0 means that data can be placed there, 1 means it cannot, as it is being used to store other information
        #                            To index it, use self.QRCodePatternsArray[(y * self.imgSize) + x]
        #
        #self.QRCodeImageArray -> A numpy array of size self.imgSize * self.imgSize * 3, all values are either 0 (black) or 255 (white), stores the image information in RGB format
        #                         To index it, use self.QRCodePatternsArray[((y * self.imgSize) + x) * 3]
        #                         


    def __Find_Data_Type_And_Encode_Message(self, message : str):
        #There are four QR data types, binary, numeric, alphanumeric and Japanese Kanji
        #For now, we will be ignoring the last one

        dataType = None
        encodedMessage = None
        
        #Start with numeric, then alphanumeric, then binary to find the most efficient way of storing it
        #Convert the message to ones and zeroes
        if self.__String_Is_Numeric(message):
            dataType = "N"
            encodedMessage = self.__Message_To_Numeric(message)

        elif self.__String_Is_Alphanumeric(self.message):
            dataType = "A"
            encodedMessage = self.__Message_To_Alphanumeric(message)
            
        elif self.__String_Is_Binary(message):
            dataType = "B"
            encodedMessage = self.__Message_To_Latin_1(message)

        else:
            raise Exception(f"The string \"{self.message}\" contains invalid characters.")

        return dataType, encodedMessage

    def __Find_Version(self, dataType : str, charCount : int, errorCorrection : str) -> int:
        #Find the smallest version we can have that's valid
        for i in range(static_values.QRCodeTypeCount):
            if charCount <= static_values.dataCapacityDict.get(dataType).get(errorCorrection)[i]:
                return i + 1

        #Too much data
        raise Exception(f"Your string has too much data for your desired level of error correction.\nYour string's bit count: {charCount}\
                        \nMaximum allowed bits for type {errorCorrection} error correction: {static_values.dataCapacityDict.get(dataType).get(errorCorrection)[static_values.QRCodeTypeCount - 1]}")
        return 0

    #Create one numpy array consisting of the mode, cci , data, terminator and any padding we have to do
    def __Assemble_Bit_String(self, dataType : str, errorCorrection : str, charCount : int, encodedMessage : np.ndarray, version : int) -> np.ndarray:
        #Get CCI as a numpy array of the correct length
        cciLength : int = self.__Find_Character_Count_Indicator_Bit_Count(dataType, version)
        cciArray = np.array([int(bit) for bit in format(charCount, f'0{cciLength}b')], dtype=np.uint8)
        
        fullArray = np.concatenate((self.__Return_Mode_Indicator(dataType), cciArray, encodedMessage, np.array([0, 0, 0, 0])))
    
        #fullArray = mode, count, data & terminator
        #Now we need to do padding

        #Start with bits - if the array isn't divisible by 8, fill it with zeroes
        paddingBits : int = 8 - (len(fullArray) % 8)

        if paddingBits != 8:
            #Create a comprehension, turn it into a numpy array, add it to our array 
            fullArray = np.concatenate((fullArray, np.array([0 for x in range(paddingBits)])))

        #If we have any remaining space, fill it with alternating EC and 11s (11101100, 00010001)
        totalCapacity : int = (2 + (static_values.dataCapacityDict.get(dataType).get(errorCorrection)[version - 1])) * 8
        if len(fullArray) < totalCapacity:
            i : int = len(fullArray)
            index : int = 0

            while i < totalCapacity:
                if index % 2 == 0:
                    fullArray = np.concatenate((fullArray, np.array([1, 1, 1, 0, 1, 1, 0, 0])))
                else:
                    fullArray = np.concatenate((fullArray, np.array([0, 0, 0, 1, 0, 0, 0, 1])))

                index += 1
                i += 8
        
        return fullArray

    #Apply the Reed-Solomon error correction algorithm
    def __Apply_Reed_Solomon(self, dataBlock : np.ndarray, errorCorrection : str, QRCodePatternsArray : np.ndarray) -> np.ndarray:
        #Convert our ones and zeroes into bytes
        byteData : np.ndarray = self.__Binary_To_Bytes(dataBlock).tobytes()

        #Get an integer defining how many bytes are to be for error correction.
        #Work this out by finding the maximum spaces we can have minus our current size
        errorCorrectionCount : int = int(np.sum(QRCodePatternsArray == 0) / 8) - len(byteData)

        #Do the Reed-Solomon procedure, then send back as a numpy array of ones and zeroes
        rs = RSCodec(errorCorrectionCount)
        encodedBytes = rs.encode(byteData)

        return self.__Bytes_To_Binary(np.frombuffer(encodedBytes, dtype=np.uint8))

    #Create the arrays that we will turn into images
    def __Create_QR_Code_Images(self, version : int, imgSize : int):
        #patternArray is used to see if a pixel can be edited, QRImgArray is what gets turned into an image
        patternArray : np.ndarray = np.full((imgSize * imgSize), 0, dtype=np.uint8)
        QRImgArray : np.ndarray = np.full((imgSize * imgSize * 3), 127, dtype=np.uint8)


        #Draw timing patterns -> first do the horizontal, then the vertical
        for x in range(0, imgSize):
            patternIndex : int = imgSize * 6 + x
            imgIndex : int = patternIndex * 3
            
            patternArray[patternIndex] = 1

            #If on an even index, set pixel to black. Otherwise set it to white
            blackOrWhite : int = 0 if x % 2 == 0 else 255

            QRImgArray[imgIndex : imgIndex + 3] = blackOrWhite

        #Now do vertical
        for y in range(0, imgSize):
            patternIndex : int = imgSize * y + 6
            imgIndex : int = patternIndex * 3

            patternArray[patternIndex] = 1

            #If on an even index, set pixel to black. Otherwise set it to white
            blackOrWhite : int = 0 if y % 2 == 0 else 255

            QRImgArray[imgIndex : imgIndex + 3] = blackOrWhite

        #What index do we draw the finder patterns at (top left pixels, )
        finderPatternIndexes = [0, imgSize - 7, imgSize * (imgSize - 7)]

        #White outlines, 8*8 then format bits
        polygon.paste_polygon(patternArray, imgSize, imgSize, finderPatternIndexes[0], 9, 9, 1)
        polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0], 24, 8, 255)
        polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0] + 24, 3, 6, 255)
        polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0] + (imgSize * 24), 18, 1, 255)
        polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0] + (imgSize * 21) + 21, 6, 2, 255)
        
        polygon.paste_polygon(patternArray, imgSize, imgSize, finderPatternIndexes[1] - 1, 8, 9, 1)
        polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (finderPatternIndexes[1] - 1)* 3, 24, 9, 255)

        polygon.paste_polygon(patternArray, imgSize, imgSize, (finderPatternIndexes[2] -  imgSize), 9, 8, 1)
        polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (finderPatternIndexes[2] -  imgSize) * 3, 27, 8, 255)
        QRImgArray[(finderPatternIndexes[2] + 8 - imgSize) * 3 : (finderPatternIndexes[2] + 8 - imgSize) * 3 + 3] = 0

        for patternIndex in finderPatternIndexes:
            #Black square, 7*7
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, patternIndex * 3, 21, 7, 0)

            #White square, 5*5
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (patternIndex + imgSize + 1) * 3, 15, 5, 255)

            #Black square, 3*3
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (patternIndex + imgSize + imgSize + 2) * 3, 9, 3, 0)

        #Finder patterns are done, we just need to do alignment patterns now
        for index in static_values.alignMentPatternTopLeftArray[version - 1]:
            polygon.paste_polygon(patternArray, imgSize, imgSize, index, 5, 5, 1)
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, index * 3, 15, 5, 0)
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (index + imgSize + 1) * 3, 9, 3, 255)
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (index + imgSize + imgSize + 2) * 3, 3, 1, 0)

        #7 and height need the Version information area
        if version >= 7:
            polygon.paste_polygon(patternArray, imgSize, imgSize, imgSize - 11, 3, 6, 1)
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (imgSize - 11) * 3, 9, 6, 255)

            polygon.paste_polygon(patternArray, imgSize, imgSize, imgSize * (imgSize - 11), 6, 3, 1)
            polygon.paste_polygon(QRImgArray, imgSize * 3, imgSize, (imgSize * (imgSize - 11)) * 3, 18, 3, 255)
            

        return patternArray, QRImgArray

    #Fill the QR code
    def __Fill_QR_Code_Image(self, QRCodeImageArray : np.ndarray, QRCodePatternsArray : np.ndarray, imgSize : int, finalDataBlock : np.ndarray) -> np.ndarray:
        #Current piece of data that's being pasted
        dataIndex : int = 0

        #The starting index -> bottom right
        currentImgIndex : int = len(QRCodePatternsArray) - 1

        #Direction boolean
        directionUp : bool = True

        #Used to skip column six. Skip to next column if we have three left to traverse
        columnSkip : int = ((imgSize - 1) // 2) - 4

        #Modulo this to see if we move horizontally or vertically
        spacesTraversed : int = 0

        #First loop represents two columns, starting with the far right two, then the two before that, so on
        #Second one represents all of the modules in those columns
        for columnsTraversed in range((imgSize - 1) // 2):
            for i in range(imgSize * 2):
                
                #Only paste data if we have data to paste and we aren't pasting onto a pattern
                if dataIndex + 1 < len(finalDataBlock) and QRCodePatternsArray[currentImgIndex] == 0:
                    blackOrWhite : int = 255 if finalDataBlock[dataIndex] == 0 else 0
                    index : int = currentImgIndex * 3

                    QRCodeImageArray[index + 0] = blackOrWhite
                    QRCodeImageArray[index + 1] = blackOrWhite
                    QRCodeImageArray[index + 2] = blackOrWhite

                    dataIndex += 1

                    #x : int = currentImgIndex % imgSize
                    #y : int = currentImgIndex // imgSize

                    #print(f"X: {x}, Y: {y}, Value: {finalDataBlock[dataIndex]}")

                #Find out the next index, unless we're at the end of the column, we do that one below
                if i + 1 != (imgSize * 2):
                    if spacesTraversed % 2 == 0:
                        currentImgIndex -= 1   
                    else:
                        if directionUp == True:
                            currentImgIndex -= (imgSize - 1)
                        else:
                            currentImgIndex += (imgSize + 1)

                #Move a space
                spacesTraversed += 1

            #If we have to skip column six, move two across, otherwise move one
            if columnsTraversed == columnSkip:
                currentImgIndex -= 1
            currentImgIndex -= 1

            #Change direction
            directionUp = not directionUp

        #Set all remaining 127(grey) values to 255(white
        QRCodeImageArray[QRCodeImageArray == 127] = 255
        return QRCodeImageArray
    
    def __Apply_Best_Mask(self, QRCodeImageArray : np.ndarray, QRCodePatternsArray : np.ndarray, imgSize : int) -> np.ndarray:
        """Apply the best mask pattern and format information"""
        best_mask, best_array, best_score = masking.find_best_mask(
            QRCodeImageArray, QRCodePatternsArray, imgSize
        )
        
        # Add format information
        best_array = self.__Add_Format_Information(best_array, imgSize, best_mask, self.errorCorrection)
        
        print(f"Applied mask pattern {best_mask} with penalty score {best_score}")
        return best_array
    
    def __Add_Format_Information(self, QRCodeImageArray : np.ndarray, imgSize : int, mask_pattern : int, error_correction : str) -> np.ndarray:
        """Add format information bits to the QR code"""
        # Format information encoding for error correction and mask pattern
        format_info_table = {
            ('L', 0): 0b111011111000100,
            ('L', 1): 0b111001011110011,
            ('L', 2): 0b111110110101010,
            ('L', 3): 0b111100010011101,
            ('M', 0): 0b101010000010010,
            ('M', 1): 0b101000100100101,
            ('M', 2): 0b101111001111100,
            ('M', 3): 0b101101101001011,
            ('Q', 0): 0b011010101011111,
            ('Q', 1): 0b011000001101000,
            ('Q', 2): 0b011111100110001,
            ('Q', 3): 0b011101000000110,
            ('H', 0): 0b001011010001001,
            ('H', 1): 0b001001110111110,
            ('H', 2): 0b001110011100111,
            ('H', 3): 0b001100111010000,
        }
        
        # Get format info bits
        format_bits = format_info_table.get((error_correction, mask_pattern % 4), 0b111011111000100)
        format_string = format(format_bits, '015b')
        
        # Place format info around finder patterns
        bit_positions_1 = [
            (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
            (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)
        ]
        
        bit_positions_2 = [
            (imgSize-1, 8), (imgSize-2, 8), (imgSize-3, 8), (imgSize-4, 8),
            (imgSize-5, 8), (imgSize-6, 8), (imgSize-7, 8), (8, imgSize-8),
            (8, imgSize-7), (8, imgSize-6), (8, imgSize-5), (8, imgSize-4),
            (8, imgSize-3), (8, imgSize-2), (8, imgSize-1)
        ]
        
        # Apply format bits
        for i, (y, x) in enumerate(bit_positions_1):
            if i < len(format_string):
                color = 0 if format_string[i] == '1' else 255
                idx = (y * imgSize + x) * 3
                QRCodeImageArray[idx:idx+3] = color
        
        for i, (y, x) in enumerate(bit_positions_2):
            if i < len(format_string):
                color = 0 if format_string[i] == '1' else 255
                idx = (y * imgSize + x) * 3
                QRCodeImageArray[idx:idx+3] = color
        
        return QRCodeImageArray

    #Return four bites signalling to the QR reader what type of data is being stored here
    def __Return_Mode_Indicator(self, dataType : str) -> np.ndarray:
        if dataType == "B":
            return np.array([0, 1, 0, 0])
        elif dataType == "A":
            return np.array([0, 0, 1, 0])
        elif dataType == "N":
            return np.array([0, 0, 0, 1])
        else:
            raise Exception("Invalid data type")        #This shouldn't trigger
            return np.array([])

    #How many bits long will our CCI be
    def __Find_Character_Count_Indicator_Bit_Count(self, dataType : str, version : int) -> int:
        if dataType == "N":
            if version <= 9:
                return 10
            elif version >= 10 and self.version <= 26:
                return 12
            else:
                return 14
            
        elif dataType == "A":
            if version <= 9:
                return 9
            elif version >= 10 and version <= 26:
                return 11
            else:
                return 13
            
        elif dataType == "B":
            if version <= 9:
                return 8
            else:
                return 16
        

    #Functions to define what data type we're dealing with
    def __String_Is_Numeric(self, string : str) -> bool:
        return string.isdigit()

    def __String_Is_Alphanumeric(self, string : str) -> bool:
        #Only 45 valid characters for Alphanumeric
        
        return all(char in static_values.validAlphanumericCharacters for char in string)

    def __String_Is_Binary(self, string : str) -> bool:
        #QR codes are encoded in the Latin-1 / ISO 8859-1 standard
        
        try:
            string.encode('latin-1')
            return True
        except:
            return False

    #Functions to convert str into a numpy array containing the bytes of ones and zeroes
    def __Message_To_Numeric(self, string : str) -> np.ndarray:
        #QR codes turn Numeric strings to binary by splitting them into three digit arrays, with the last one being one or two if it does not fit
        #Example "1234567890" -> "123", "456", "789", "0"
        #Then convert that into binary and return

        bits : list[int] = []
        i : int = 0
        while i < len(string):
            numberSubString : list[str] = string[i : i+3]      #Won't loop around or throw an error if at the end of the list
            if len(numberSubString) == 3:
                bits += format(int(numberSubString), '010b')
            elif len(numberSubString) == 2:
                bits += format(int(numberSubString), '07b')
            else:
                bits += format(int(numberSubString), '04b')
                
            i += 3

        return np.array([int(b) for b in bits], dtype=np.uint8)

    def __Message_To_Alphanumeric(self, string : str) -> np.ndarray:
        #Convert to the AlphaNumeric values (0-44) from which we can store two at a time (11 bits) and the last one by itself (6 bits) if necessary 
        #We can store two values by timesing the first by 45 then adding it to the second one, the QR decoder will just do a modulo + floor division to get both numbers back
        
        i : int = 0
        bits : list[int] = []
        while i < len(string):
            if i + 1 < len(string):
                bits += format(((45 * static_values.alphanumericCharToValueDict[string[i]]) + static_values.alphanumericCharToValueDict[string[i+1]]), '011b')  
                i += 2
                
            else:
                bits += format((static_values.alphanumericCharToValueDict[string[i]]), '06b') 
                i += 1
            
        return np.array([int(b) for b in bits], dtype=np.uint8)
        
    def __Message_To_Latin_1(self, string : str) -> np.ndarray:
        #Convert self.message to latin-1 encoding then send each bit back as an entry within a numpy array
        
        npArrayMessage : np.ndarray = np.frombuffer(string.encode('latin-1'), dtype=np.uint8)
        
        #Create an array to store the ones and zeroes
        bits : list[int] = []
        for characterIntegerValue in npArrayMessage:
            bits += format(characterIntegerValue, '08b')

        # 4. Convert bitstring to NumPy array of integers
        return np.array([int(b) for b in bits], dtype=np.uint8)

    def __Binary_To_Bytes(self, array : np.ndarray) -> np.ndarray:
        return np.packbits(array)

    def __Bytes_To_Binary(self, array : np.ndarray) -> np.ndarray:
        return np.unpackbits(array)

    #Getters
    def Get_Data_Type(self) -> str:
        return self.dataType

    def Get_Bit_Array(self) -> np.ndarray:
        return self.encodedMessage

    def Get_Version(self) -> int:
        return self.version

    #Printers (Make it look nice)
    def Print_Message_To_Bit_Array(self):
        i : int = 0
        noToAdd : int = 10
        if self.dataType == "B":
            noToAdd = 8
        elif self.dataType == "A":
            noToAdd = 11
        while i < len(self.encodedMessage):
                
            print(self.encodedMessage[i : i + noToAdd])
            
            i += noToAdd
            
    def Print_Final_Data_Block_Array(self):
        i : int = 0
        noToAdd : int = 8
        while i < len(self.finalDataBlock):   
            print(str(int(i / 8)) + ": " + str(self.finalDataBlock[i : i + noToAdd]))
            i += noToAdd

    def Save_QR_Code(self, directory : str):
        outArray : np.ndarray = self.QRCodeImageArray.reshape((self.imgSize, self.imgSize, 3))
        img = Image.fromarray(outArray, mode='RGB')
        img.save(directory)
        
    def Save_QR_Fill(self, directory : str):
        outArray : np.ndarray = (1 - self.QRCodePatternsArray.reshape((self.imgSize, self.imgSize))) * 255
        img = Image.fromarray(outArray, mode='L')
        img.save(directory)