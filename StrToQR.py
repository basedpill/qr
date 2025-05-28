#Use numpy for the byte arrays
import numpy as np
#Use reedsolo for error encoding
from reedsolo import RSCodec

#Mostly used for debugging
from PIL import Image

#Global vairables

#Alphanumeric mode has 45 valid characters
validAlphanumericCharacters : str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
alphanumericCharToValueDict : dict = {char: index for index, char in enumerate(validAlphanumericCharacters)}

#Size of our QR code. v1 is 21x21, v40 is 177x177
QRCodeTypeCount : int = 40
QRCodeSizeArray : list[int] = [(i * 4 + 21) for i in range(QRCodeTypeCount)]

#How muchinformation can we store within the QR code, including the segment mode, count and terminator
#Yes I *could* work them out mathematically, but it's far easier just to copy them down manually
dataCapacityDict : dict = {
    'N': {
        'L': [41, 77, 127, 187, 255, 322, 370, 461, 552, 652, 772, 883, 1022, 1101, 1250, 1408, 1548, 1725, 1903, 2061, 2232, 2409, 2620, 2812, 3057, 3283, 3517, 3669, 3909, 4158, 4417, 4686, 4965, 5253, 5529, 5836, 6153, 6479, 6743, 7089],
        'M': [34, 63, 101, 149, 202, 255, 293, 365, 432, 513, 604, 691,  796,  871,  991, 1082, 1212, 1346, 1500, 1600, 1708, 1872, 2059, 2188, 2395, 2544, 2701, 2857, 3035, 3289, 3486, 3693, 3909, 4134, 4343, 4588, 4775, 5039, 5313, 5596],
        'Q': [27, 48,  77, 111, 144, 178, 207, 259, 312, 364, 427, 489,  580,  621,  703,  775,  876,  948, 1063, 1159, 1224, 1358, 1468, 1588, 1718, 1804, 1933, 2085, 2181, 2358, 2473, 2670, 2805, 2949, 3081, 3244, 3417, 3599, 3791, 3993],
        'H': [17, 34,  58,  82, 106, 139, 154, 202, 235, 288, 331, 374,  427,  468,  530,  602,  674,  746,  813,  919,  969, 1056, 1108, 1228, 1286, 1425, 1501, 1581, 1677, 1782, 1897, 2022, 2157, 2301, 2361, 2524, 2625, 2735, 2927, 3057]
    },
    'A': {
        'L': [25, 47, 77, 114, 154, 195, 224, 279, 335, 395, 468, 535, 619, 667, 758, 854, 938, 1046, 1153, 1249, 1352, 1460, 1588, 1704, 1853, 1990, 2132, 2223, 2369, 2520, 2677, 2840, 3009, 3183, 3351, 3537, 3729, 3927, 4087, 4296],
        'M': [20, 38, 61,  90, 122, 154, 178, 221, 262, 311, 366, 419, 483, 528, 600, 656, 734,  816,  909,  970, 1035, 1134, 1248, 1326, 1451, 1542, 1637, 1732, 1839, 1994, 2113, 2238, 2369, 2506, 2632, 2780, 2894, 3054, 3220, 3391],
        'Q': [16, 29, 47,  67,  87, 108, 125, 157, 189, 221, 259, 296, 352, 376, 426, 470, 531,  574,  644,  702,  742,  823,  890,  963, 1041, 1094, 1172, 1263, 1322, 1429, 1499, 1618, 1700, 1787, 1867, 1966, 2071, 2181, 2298, 2420],
        'H': [10, 20, 35,  50,  64,  84,  93, 122, 143, 174, 200, 227, 259, 283, 321, 365, 408,  452,  493,  557,  587,  640,  672,  744,  779,  864,  910,  958, 1016, 1080, 1150, 1226, 1307, 1394, 1431, 1530, 1591, 1658, 1774, 1852]
    },
    'B': {
        'L': [17, 32, 53, 78, 106, 134, 154, 192, 230, 271, 321, 367, 425, 458, 520, 586, 644, 718, 792, 858, 929, 1003, 1091, 1171, 1273, 1367, 1465, 1528, 1628, 1732, 1840, 1952, 2068, 2188, 2303, 2431, 2563, 2699, 2809, 2953],
        'M': [14, 26, 42, 62,  84, 106, 122, 152, 180, 213, 251, 287, 331, 362, 412, 450, 504, 560, 624, 666, 711,  779,  857,  911,  997, 1059, 1125, 1190, 1264, 1370, 1452, 1538, 1628, 1722, 1809, 1911, 1989, 2099, 2213, 2331],
        'Q': [11, 20, 32, 46,  60,  74,  86, 108, 130, 151, 177, 203, 241, 258, 292, 322, 364, 394, 442, 482, 509,  565,  611,  661,  715,  751,  805,  868,  908,  982, 1030, 1112, 1168, 1228, 1283, 1351, 1423, 1499, 1579, 1663],
        'H': [ 7, 14, 24, 34,  44,  58,  64,  84,  98, 119, 137, 155, 177, 194, 220, 250, 280, 310, 338, 382, 403,  439,  461,  511,  535,  593,  625,  658,  698,  742,  790,  842,  898,  958,  983, 1051, 1093, 1139, 1219, 1273]
    }
}

#Top left corner for the alignment patterns for each version, worked out with alignmentPatternGenerator.py
alignMentPatternTopLeftArray : list[list[int]] = [[], [416], [600], [816], [1064], [1344], [200, 904, 920, 936, 1640, 1656], [218, 1082, 1100, 1118, 1982, 2000],
                           [236, 1276, 1296, 1316, 2356, 2376], [254, 1486, 1508, 1530, 2762, 2784], [272, 1712, 1736, 1760, 3200, 3224], [290, 1954, 1980, 2006, 3670, 3696], [308, 2212, 2240, 2268, 4172, 4200],
                           [316, 336, 1756, 1776, 1796, 1816, 3216, 3236, 3256, 3276, 4696, 4716, 4736], [332, 354, 1852, 1872, 1894, 1916, 3546, 3566, 3588, 3610, 5260, 5282, 5304],
                           [348, 372, 1948, 1968, 1992, 2016, 3892, 3912, 3936, 3960, 5856, 5880, 5904], [368, 392, 2384, 2408, 2432, 2456, 4424, 4448, 4472, 4496, 6488, 6512, 6536],
                           [384, 410, 2496, 2520, 2546, 2572, 4810, 4834, 4860, 4886, 7148, 7174, 7200], [400, 428, 2608, 2632, 2660, 2688, 5212, 5236, 5264, 5292, 7840, 7868, 7896],
                           [420, 448, 3108, 3136, 3164, 3192, 5824, 5852, 5880, 5908, 8568, 8596, 8624], [430, 452, 474, 2630, 2652, 2674, 2696, 2718, 4852, 4874, 4896, 4918, 4940, 7074, 7096, 7118, 7140, 7162, 9318, 9340, 9362, 9384],
                           [444, 468, 492, 2524, 2544, 2568, 2592, 2616, 5044, 5064, 5088, 5112, 5136, 7564, 7584, 7608, 7632, 7656, 10104, 10128, 10152, 10176],
                           [464, 488, 512, 3056, 3080, 3104, 3128, 3152, 5672, 5696, 5720, 5744, 5768, 8288, 8312, 8336, 8360, 8384, 10928, 10952, 10976, 11000],
                           [478, 504, 530, 2942, 2964, 2990, 3016, 3042, 5880, 5902, 5928, 5954, 5980, 8818, 8840, 8866, 8892, 8918, 11778, 11804, 11830, 11856],
                           [498, 524, 550, 3514, 3540, 3566, 3592, 3618, 6556, 6582, 6608, 6634, 6660, 9598, 9624, 9650, 9676, 9702, 12666, 12692, 12718, 12744],
                           [512, 540, 568, 3392, 3416, 3444, 3472, 3500, 6780, 6804, 6832, 6860, 6888, 10168, 10192, 10220, 10248, 10276, 13580, 13608, 13636, 13664],
                           [532, 560, 588, 4004, 4032, 4060, 4088, 4116, 7504, 7532, 7560, 7588, 7616, 11004, 11032, 11060, 11088, 11116, 14532, 14560, 14588, 14616],
                           [540, 564, 588, 612, 3100, 3120, 3144, 3168, 3192, 3216, 6196, 6216, 6240, 6264, 6288, 6312, 9292, 9312, 9336, 9360, 9384, 9408, 12388, 12408, 12432, 12456, 12480, 12504, 15504, 15528, 15552, 15576, 15600],
                           [560, 584, 608, 632, 3728, 3752, 3776, 3800, 3824, 3848, 6920, 6944, 6968, 6992, 7016, 7040, 10112, 10136, 10160, 10184, 10208, 10232, 13304, 13328, 13352, 13376, 13400, 13424, 16520, 16544, 16568, 16592, 16616],
                           [572, 598, 624, 650, 3292, 3312, 3338, 3364, 3390, 3416, 6854, 6874, 6900, 6926, 6952, 6978, 10416, 10436, 10462, 10488, 10514, 10540, 13978, 13998, 14024, 14050, 14076, 14102, 17560, 17586, 17612, 17638, 17664],
                           [592, 618, 644, 670, 3952, 3976, 4002, 4028, 4054, 4080, 7618, 7642, 7668, 7694, 7720, 7746, 11284, 11308, 11334, 11360, 11386, 11412, 14950, 14974, 15000, 15026, 15052, 15078, 18640, 18666, 18692, 18718, 18744],
                           [612, 638, 664, 690, 4644, 4672, 4698, 4724, 4750, 4776, 8414, 8442, 8468, 8494, 8520, 8546, 12184, 12212, 12238, 12264, 12290, 12316, 15954, 15982, 16008, 16034, 16060, 16086, 19752, 19778, 19804, 19830, 19856],
                           [624, 652, 680, 708, 4176, 4200, 4228, 4256, 4284, 4312, 8348, 8372, 8400, 8428, 8456, 8484, 12520, 12544, 12572, 12600, 12628, 12656, 16692, 16716, 16744, 16772, 16800, 16828, 20888, 20916, 20944, 20972, 21000],
                           [644, 672, 700, 728, 4900, 4928, 4956, 4984, 5012, 5040, 9184, 9212, 9240, 9268, 9296, 9324, 13468, 13496, 13524, 13552, 13580, 13608, 17752, 17780, 17808, 17836, 17864, 17892, 22064, 22092, 22120, 22148, 22176],
                           [656, 680, 704, 728, 752, 4400, 4424, 4448, 4472, 4496, 4520, 4544, 8168, 8192, 8216, 8240, 8264, 8288, 8312, 11936, 11960, 11984, 12008, 12032, 12056, 12080, 15704, 15728, 15752, 15776, 15800, 15824, 15848, 19472, 19496, 19520, 19544, 19568, 19592, 19616, 23264, 23288, 23312, 23336, 23360, 23384],
                           [666, 692, 718, 744, 770, 3546, 3564, 3590, 3616, 3642, 3668, 3694, 7732, 7750, 7776, 7802, 7828, 7854, 7880, 11918, 11936, 11962, 11988, 12014, 12040, 12066, 16104, 16122, 16148, 16174, 16200, 16226, 16252, 20290, 20308, 20334, 20360, 20386, 20412, 20438, 24494, 24520, 24546, 24572, 24598, 24624],
                           [686, 712, 738, 764, 790, 4294, 4316, 4342, 4368, 4394, 4420, 4446, 8584, 8606, 8632, 8658, 8684, 8710, 8736, 12874, 12896, 12922, 12948, 12974, 13000, 13026, 17164, 17186, 17212, 17238, 17264, 17290, 17316, 21454, 21476, 21502, 21528, 21554, 21580, 21606, 25766, 25792, 25818, 25844, 25870, 25896],
                           [706, 732, 758, 784, 810, 5074, 5100, 5126, 5152, 5178, 5204, 5230, 9468, 9494, 9520, 9546, 9572, 9598, 9624, 13862, 13888, 13914, 13940, 13966, 13992, 14018, 18256, 18282, 18308, 18334, 18360, 18386, 18412, 22650, 22676, 22702, 22728, 22754, 22780, 22806, 27070, 27096, 27122, 27148, 27174, 27200],
                           [716, 744, 772, 800, 828, 4156, 4176, 4204, 4232, 4260, 4288, 4316, 9000, 9020, 9048, 9076, 9104, 9132, 9160, 13844, 13864, 13892, 13920, 13948, 13976, 14004, 18688, 18708, 18736, 18764, 18792, 18820, 18848, 23532, 23552, 23580, 23608, 23636, 23664, 23692, 28396, 28424, 28452, 28480, 28508, 28536],
                           [736, 764, 792, 820, 848, 4960, 4984, 5012, 5040, 5068, 5096, 5124, 9916, 9940, 9968, 9996, 10024, 10052, 10080, 14872, 14896, 14924, 14952, 14980, 15008, 15036, 19828, 19852, 19880, 19908, 19936, 19964, 19992, 24784, 24808, 24836, 24864, 24892, 24920, 24948, 29764, 29792, 29820, 29848, 29876, 29904]]

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
        self.imgSize : int = QRCodeSizeArray[self.version - 1]
        self.QRCodePatternsArray, self.QRCodeImageArray = self.__Create_QR_Code_Images(self.version, self.imgSize)

        #Apply Reed-Solomon enocding to our message
        self.finalDataBlock = self.__Apply_Reed_Solomon(self.dataBlock, self.errorCorrection, self.QRCodePatternsArray)

        #Fill out the image with our data
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
        for i in range(QRCodeTypeCount):
            if charCount <= dataCapacityDict.get(dataType).get(errorCorrection)[i]:
                return i + 1

        #Too much data
        raise Exception(f"Your string has too much data for your desired level of error correction.\nYour string's bit count: {charCount}\
                        \nMaximum allowed bits for type {errorCorrection} error correction: {dataCapacityDict.get(dataType).get(errorCorrection)[QRCodeTypeCount - 1]}")
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
        totalCapacity : int = (2 + (dataCapacityDict.get(dataType).get(errorCorrection)[version - 1])) * 8
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
        self.__PastePolygon(patternArray, imgSize, imgSize, finderPatternIndexes[0], 9, 9, 1)
        self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0], 24, 8, 255)
        self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0] + 24, 3, 6, 255)
        self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0] + (imgSize * 24), 18, 1, 255)
        self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, finderPatternIndexes[0] + (imgSize * 21) + 21, 6, 2, 255)
        
        self.__PastePolygon(patternArray, imgSize, imgSize, finderPatternIndexes[1] - 1, 8, 9, 1)
        self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (finderPatternIndexes[1] - 1)* 3, 24, 9, 255)

        self.__PastePolygon(patternArray, imgSize, imgSize, (finderPatternIndexes[2] -  imgSize), 9, 8, 1)
        self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (finderPatternIndexes[2] -  imgSize) * 3, 27, 8, 255)
        QRImgArray[(finderPatternIndexes[2] + 8 - imgSize) * 3 : (finderPatternIndexes[2] + 8 - imgSize) * 3 + 3] = 0

        for patternIndex in finderPatternIndexes:
            #Black square, 7*7
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, patternIndex * 3, 21, 7, 0)

            #White square, 5*5
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (patternIndex + imgSize + 1) * 3, 15, 5, 255)

            #Black square, 3*3
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (patternIndex + imgSize + imgSize + 2) * 3, 9, 3, 0)

        #Finder patterns are done, we just need to do alignment patterns now
        for index in alignMentPatternTopLeftArray[version - 1]:
            self.__PastePolygon(patternArray, imgSize, imgSize, index, 5, 5, 1)
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, index * 3, 15, 5, 0)
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (index + imgSize + 1) * 3, 9, 3, 255)
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (index + imgSize + imgSize + 2) * 3, 3, 1, 0)

        #7 and height need the Version information area
        if version >= 7:
            self.__PastePolygon(patternArray, imgSize, imgSize, imgSize - 11, 3, 6, 1)
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (imgSize - 11) * 3, 9, 6, 255)

            self.__PastePolygon(patternArray, imgSize, imgSize, imgSize * (imgSize - 11), 6, 3, 1)
            self.__PastePolygon(QRImgArray, imgSize * 3, imgSize, (imgSize * (imgSize - 11)) * 3, 18, 3, 255)
            

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
        best_mask, best_array, best_score = find_best_mask(QRCodeImageArray, QRCodePatternsArray, imgSize)
        
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
    
    def __PastePolygon(self, array : np.ndarray, arrayWidth : int, arrayHeight : int, indexToPaste : int, width : int, height : int, val : int) -> np.ndarray:
        for y in range(height):
            index = indexToPaste + (y * arrayWidth)
            array[index : index + width] = val
                

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
        
        return all(char in validAlphanumericCharacters for char in string)

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
                bits += format(((45 * alphanumericCharToValueDict[string[i]]) + alphanumericCharToValueDict[string[i+1]]), '011b')  
                i += 2
                
            else:
                bits += format((alphanumericCharToValueDict[string[i]]), '06b') 
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
    """
    Calculate penalty score for a QR code according to ISO/IEC 18004:2015
    Lower scores are better
    """
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
    """
    Test all 8 mask patterns and return the one with the lowest penalty score
    """
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


#test = QR_Code("https://www.nayuki.io/page/creating-a-qr-code-step-by-step", "L")
#test.Print_Final_Data_Block_Array()
#test.Save_QR_Code("QR.png")
#test.Save_QR_Fill("QR_Fill.png")