import hashlib
import os
import re

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

    def parse_trailer(self, file_data):
        """

        :param file_data:
        :return:
        """
        for (start_offset, end_offset) in self.trailer:
            dictionary_start_offset = file_data.find(b"<<", start_offset, end_offset)
            dictionary_end_offset = file_data.find(b">>", start_offset, end_offset)

            offset = dictionary_start_offset
            dictionary_key_start_offsets = []
            while dictionary_end_offset > offset:
                offset = file_data.find(b'/', offset + 1)
                if offset == -1:
                    break
                dictionary_key_start_offsets.append(offset)

            dictionary_key_end_offsets = []
            for offset in dictionary_key_start_offsets:
                dictionary_key_end_offsets.append(file_data.find(b' ', offset))

            dictionary_value_start_offsets = []
            dictionary_value_end_offsets = []

            for offset in dictionary_key_end_offsets:
                dictionary_value_start_offsets.append(offset + 1)

            for offset in dictionary_value_start_offsets:
                temp = file_data.find(b'/', offset, dictionary_end_offset)
                if temp == -1:
                    dictionary_value_end_offsets.append(dictionary_end_offset)
                else:
                    dictionary_value_end_offsets.append(temp - 1)

            for i, j, k, l in zip(dictionary_key_start_offsets, dictionary_key_end_offsets, dictionary_value_start_offsets, dictionary_value_end_offsets):
                print("{0} : {1}".format(file_data[i:j], file_data[k:l]))


PATH = r"E:\PDF\mal\0902293f19286270122eacba8bf74c49.vir"
f = open(PATH, "rb")
data = f.read()
f.close()

pdfi = PDFInformation(data)

pdfi.parse_trailer(data)