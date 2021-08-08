import hashlib
import os
import re
import zlib
import base64
import binascii

class PDFInformation:
    def __init__(self, file_data):
        """
        Get PDF element offset information
        :param file_data: byte sequence read from PDF file
        """
        self.error_information = set()
        self.status_information = set()

        # Get header start offset, end offset
        # keyword base search

        p = re.compile(b"%PDF", re.IGNORECASE)
        m = p.match(file_data)

        if m is None:
            self.error_information.add("PDF offset parse, header not found error")
        else:
            self.header = (m.start(), m.end() + 4)

        # Status : PDF Header Not found
        if m is None:
            self.status_information.add("PDF header not found")

        # Get body's objects start offset, end offset
        # keyword base search

        self.body = []

        p = re.compile(b"[0-9]{1,7} [0-9]{1,7} obj", re.IGNORECASE)
        mit = p.finditer(file_data)

        for match_object in mit:
            start_offset = match_object.start()
            end_offset = file_data.find(b"endobj", start_offset)

            if end_offset == -1:
                self.error_information.add("PDF offset parse, body's object end offset parse error")
            else:
                self.body.append((start_offset, end_offset))

        # Status : PDF body's objects not found
        if len(self.body) == 0:
            self.status_information.add("PDF body\'s objects not found")

        # Get cross reference table start offset, end offset
        # keyword base search

        self.cross_reference_table = []
        cross_reference_table_start_offset = []

        p = re.compile(b"xref", re.IGNORECASE)
        mit = p.finditer(data)

        for match_object in mit:
            cross_reference_table_start_offset.append(match_object.start())

        p = re.compile(b"startxref", re.IGNORECASE)
        mit = p.finditer(data)

        for match_object in mit:
            try:
                cross_reference_table_start_offset.remove(match_object.start() + 5)
            except ValueError as e:
                self.error_information.add("PDF offset parse, duplicated xref keyword deletion error")

        for start_offset in cross_reference_table_start_offset:
            end_offset = data.find(b"trailer", start_offset)
            if end_offset == -1:
                self.error_information.add("PDF offset parse, cross reference table end offset parse error")
            else:
                self.cross_reference_table.append((start_offset, end_offset))

        # Status : PDF cross reference table not found
        if len(self.cross_reference_table) == 0:
            self.status_information.add("PDF cross reference table not found")

        # Get trailer start offset, end offset
        # keyword base search

        self.trailer = []

        p = re.compile(b"trailer", re.IGNORECASE)
        mit = p.finditer(file_data)

        for match_object in mit:
            start_offset = match_object.start()
            end_offset = file_data.find(b"%EOF", start_offset)

            if end_offset == -1:
                self.error_information("Trailer end offset parse error")
            else:
                self.trailer.append((start_offset, end_offset))

        # Status : PDF trailer not found
        if len(self.trailer) == 0:
            self.status_information.add("PDF trailer not found")

    def __str__(self):
        """
        Customize str, print function
        :return: String
        """
        result = ""
        result += "PDF parse error : {0} \n".format(self.error_information)
        result += "PDF status : {0} \n".format(self.status_information)
        result += "PDF header offset : {0} \n".format(self.header)
        result += "PDF body\'s Objects\' offset : {0}\n".format(self.body)
        result += "PDF cross reference table offset : {0}\n".format(self.cross_reference_table)
        result += "PDF trailer offset : {0}\n".format(self.trailer)
        return result

    def print_element(self, file_data, maximum_length=200):
        """
        Print PDF elements' data (default limit length = 200)
        :param file_data: byte sequence read from PDF file
        :param maximum_length: Maximum length of data for PDF's elements to output
        """

        element_offset = [self.header]
        element_offset.extend(self.body)
        element_offset.extend(self.cross_reference_table)
        element_offset.extend(self.trailer)

        if maximum_length == "INF":
            for (start_offset, end_offset) in element_offset:
                print(file_data[start_offset : end_offset])
        else:
            for (start_offset, end_offset) in element_offset:
                if start_offset + maximum_length < end_offset:
                    print(file_data[start_offset:start_offset + maximum_length])
                else:
                    print(file_data[start_offset:end_offset])

    def parse_body_objects_keywords(self, file_data):
        """
        Parse PDF body objects' object number and keywords
        :param file_data: byte sequence read from PDF file
        :return: tuple list, [(object number, keywords), ... ]
        """
        result = []
        for (start_offset, end_offset) in self.body:
            keywords = []
            p = re.compile(b"\/[0-9a-zA-Z]{1,40} ")
            mit = p.finditer(file_data, start_offset, end_offset)
            for match_object in mit:
                keywords.append(match_object.group())


            p = re.compile(b"[0-9]{1,7}")
            m = p.match(file_data, start_offset, end_offset)
            object_number = int(m.group())

            result.append((object_number, keywords))

        return result

    def parse_cross_reference_table(self, file_data):
        """
        check PDF cross reference table has invalid information and parse cross reference tables' element
        :param file_data: byte sequence read from PDF file
        :return: tuple list, [(object_number, object_address, generation_number, is_object_free), ... ]
        """
        result = []
        for (start_offset, end_offset) in self.cross_reference_table:
            cross_reference_table_element = file_data[start_offset:end_offset].split(b"\n")[1:]
            for i in range(len(cross_reference_table_element)):
                cross_reference_table_element[i] = cross_reference_table_element[i].rstrip()

            for element in cross_reference_table_element:
                if element == b'':
                    cross_reference_table_element.remove(b'')

            object_number = 0
            element_count = 0

            for element in cross_reference_table_element:
                if element.count(b' ') == 1:
                    numbers = element.split(b' ')
                    object_number = int(numbers[0])
                    element_count = int(numbers[1])
                elif element.count(b' ') == 2:
                    object_information = element.split(b' ')
                    object_address = int(object_information[0])
                    generation_number = int(object_information[1])
                    is_object_free = object_information[2]
                    result.append((object_number, object_address, generation_number, is_object_free))
                    object_number += 1
                    element_count -= 1

        for (object_number, object_address, generation_number, is_object_free) in result:
            if is_object_free == b'n':
                if bytes(str(object_number), 'utf-8') != file_data[object_address : object_address + len(str(object_number))]:
                    self.status_information.add("Invalid cross reference table information")

        return result

    def parse_trailer_dictionary(self, file_data):
        """
        Parse PDF trailer dictionary key and value (recommend to use the rstrip function for each element.)
        :param file_data: byte sequence read from PDF file
        :return: tuple list, [(Key String, Value String), ...]
        """
        result = []
        for (start_offset, end_offset) in self.trailer:
            dictionary_start_offset = file_data.find(b'<<', start_offset, end_offset)
            dictionary_end_offset = file_data.find(b'>>', start_offset, end_offset)

            if dictionary_start_offset == -1 or dictionary_end_offset == -1:
                self.status_information.add("Trailer dictionary not found")
                break

            key_start_offsets = []
            key_end_offsets = []

            p = re.compile(b"\/")
            mit = p.finditer(file_data, dictionary_start_offset, dictionary_end_offset)
            for match_object in mit:
                key_start_offsets.append(match_object.start())

            for start_offset in key_start_offsets:
                key_end_offsets.append(file_data.find(b' ', start_offset))

            value_start_offsets = []
            value_end_offsets = []

            for end_offset in key_end_offsets:
                value_start_offsets.append(end_offset + 1)

            for i in range(len(key_start_offsets) - 1):
                value_end_offsets.append(key_start_offsets[i + 1])

            value_end_offsets.append(dictionary_end_offset)

            for key_start_offset, key_end_offset, value_start_offset, value_end_offset in zip(key_start_offsets, key_end_offsets, value_start_offsets, value_end_offsets):
                result.append((file_data[key_start_offset: key_end_offset], file_data[value_start_offset: value_end_offset]))

        return result

    def get_object_stream_offset(self, file_data, object_start_offset, object_end_offset):
        """
        Get object start offset and end offset, if fail return None
        :param file_data: byte sequence read from PDF file
        :param object_start_offset: Starting offset of object
        :param object_end_offset: End offset of object
        :return: tuple, (stream start offset, stream end offset)
        """

        stream_start_offset = file_data.find(b"stream", object_start_offset, object_end_offset)
        stream_end_offset = file_data.find(b"endstream", object_start_offset, object_end_offset)

        if stream_start_offset == -1 or stream_end_offset == -1:
            self.error_information("PDF offset parse, stream keywords not found")
            return None
        return (stream_start_offset + 6, stream_end_offset)

    # object stream dump

    def dump_object_stream(self, file_data, stream_offset, path, file_name, filter_name="", hash_name=""):
        """
        Dump stream to file
        :param file_data: byte sequence read from PDF file
        :param stream_offset: tuple, (stream start offset, stream end offset)
        :param filter_name: name of filter to use when decoding encoded objects
        :param path: path to save the file
        :param file_name: name to save the file
        :param hash_name: (optional), name of the function to replace file name
        :return: if function succeed return 0, not return None
        """

        stream_data = file_data[stream_offset[0]:stream_offset[1]]
        stream_data = stream_data.lstrip()
        stream_data = stream_data.rstrip()

        # get file handle(calc hash name or use file name)
        file_hash_name = ""
        f = None
        if hash_name != "":
            if hash_name == "MD5":
                file_hash_name = hashlib.md5(stream_data).hexdigest()
            elif hash_name == "SHA-1":
                file_hash_name = hashlib.sha1(stream_data).hexdigest()
            elif hash_name == "SHA-256":
                file_hash_name = hashlib.sha256(stream_data).hexdigest()
            else:
                self.error_information.add("Stream dump, invalid hash function name")

            f = open(os.path.join(path, file_hash_name), "wb")
        else:
            f = open(os.path.join(path, file_name), "wb")

        if filter_name == "":
            f.write(stream_data)
            f.close()
            return 0
        else:
            if filter_name == "FlateDecode":
                f.write(zlib.decompress(stream_data))
                f.close()
                return 0
            elif filter_name == "ASCIIHexDecode":
                stream_data = stream_data.replace(b' ')
                temp = str(stream_data, 'ascii')
                f.write(binascii.unhexlify(temp))
                f.close()
                return 0
            elif filter_name == "ASCII85Decode":
                f.write(base64.b85decode(stream_data))
                f.close()
                return 0
            else:
                f.close()
                self.error_information.add("Stream dump, invalid filter name")
                return None


PATH = r"C:\Users\User\Downloads\12.vir" # Replace the file path
f = open(PATH, "rb")
data = f.read()
f.close()

pdfi = PDFInformation(data)
pdfi.dump_object_stream(data, pdfi.get_object_stream_offset(data, 869, 1430), r"D:\lab", "test1.str")
pdfi.dump_object_stream(data, pdfi.get_object_stream_offset(data, 869, 1430), r"D:\lab", "test2.str", "FlateDecode")
pdfi.dump_object_stream(data, pdfi.get_object_stream_offset(data, 869, 1430), r"D:\lab", "test3.str", "FlateDecode", "MD5")
pdfi.dump_object_stream(data, pdfi.get_object_stream_offset(data, 869, 1430), r"D:\lab", "test4.str", "FlateDecode", "SHA-1")
pdfi.dump_object_stream(data, pdfi.get_object_stream_offset(data, 869, 1430), r"D:\lab", "test5.str", "FlateDecode", "SHA-256")
print(pdfi)


#pdfi.print_element(data)
#for element in pdfi.parse_cross_reference_table(data):
#    print("object {0} : {1}, {2}, {3}".format(element[0], element[1], element[2], element[3]))

#for element in pdfi.parse_trailer_dictionary(data):
#    print("{0} : {1}".format(element[0], element[1]))

#print(pdfi)
