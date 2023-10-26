from lxml import etree
from datetime import datetime
from app.oaipmh.errors import Errors


class OAI():

    def __init__(self):
        self.repository_name = "Repositorio de recetas TOSCA del IM"
        self.repository_base_url = "http://158.42.104.43:5000/oai"
        self.repository_description = "Repositorio del Migue con recetas TOSCA."
        self.earliest_datestamp = "2023-03-01"
        self.datestamp_granularity = "YYYY-MM-DD"
        self.repository_admin_email = "asanchez@i3m.upv.es"
        self.repository_deleted_records = "no"
        self.repository_protocol_version = "2.0"

        self.valid_metadata_formats = ['oai_dc', 'oai_openaire']

        self.formats = [
            {
                'metadataPrefix': 'oai_dc',
                'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                'metadataNamespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            },
            {
                'metadataPrefix': 'oai_openaire',
                'schema': 'https://schema.datacite.org/meta/kernel-4.3/metadata.xsd',
                'metadataNamespace': 'http://datacite.org/schema/kernel-4',
            },
        ]

    @staticmethod
    def baseXMLTree():
        root = etree.Element('OAI-PMH')

        # Register the XML namespace for xsi
        etree.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

        # Set the xsi:schemaLocation attribute
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                 'http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd')

        root.set('xmlns', 'http://www.openarchives.org/OAI/2.0/')

        responseDate = etree.SubElement(root, 'responseDate')
        current_datetime = datetime.utcnow()
        response_date = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        responseDate.text = response_date

        return root

    def getRecord(self, root, metadata_dict, verb, identifier, metadata_prefix):
        self.addRequestElement(root, verb=verb, identifier=identifier, metadata_prefix=metadata_prefix)

        if not identifier or not metadata_prefix:
            error_element = Errors.badArgument()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        if not self.validMetadataPrefix(metadata_prefix):
            error_element = Errors.cannotDisseminateFormat()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        identifier = identifier
        name_identifier = identifier.split('templates/')[1]

        if name_identifier not in metadata_dict:
            error_element = Errors.idDoesNotExist()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        record_data = self.recordByIdentifier(metadata_dict, identifier)

        get_record_element = etree.SubElement(root, 'GetRecord')
        record = etree.SubElement(get_record_element, 'record')

        header = etree.SubElement(record, 'header')

        identifier_element = etree.SubElement(header, 'identifier')
        identifier_element.text = identifier
        datestamp_element = etree.SubElement(header, 'datestamp')
        datestamp_element.text = 'datestamp'

        metadata_element = etree.SubElement(record, 'metadata')

        if metadata_prefix == 'oai_dc':
            metadata_xml = self.mapDC(record_data)

        if metadata_prefix == 'oai_openaire':
            metadata_xml = self.mapOAIRE(record_data)

        metadata_element.append(etree.fromstring(metadata_xml))

    def identify(self, root, verb):
        self.addRequestElement(root, verb)
        identify_element = etree.SubElement(root, 'Identify')
        self.addIdentifyElements(identify_element)

        return etree.tostring(root, pretty_print=True, encoding='unicode')

    def listIdentifiers(self, root, metadata_dict, verb, metadata_prefix, from_date=None,
                        until_date=None, set_spec=None, resumption_token=None):
        self.addRequestElement(root, verb, metadata_prefix=metadata_prefix, from_date=from_date,
                               until_date=until_date, set_spec=None, resumption_token=resumption_token)

        from_date_dt = None
        until_date_dt = None

        if resumption_token is not None:
            error_element = Errors.badResumptionToken()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        if set_spec is not None:
            error_element = Errors.noSetHierarchy()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        # Check the validity of "from" and "until" parameters
        valid_from_date = from_date is None or self.isValidDate(from_date)
        valid_until_date = until_date is None or self.isValidDate(until_date)

        if not metadata_prefix or not valid_from_date or not valid_until_date:
            error_element = Errors.badArgument()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        if not self.validMetadataPrefix(metadata_prefix):
            error_element = Errors.cannotDisseminateFormat()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        # if from_date is not None:
        #     from_date_dt = self.isValidDate(from_date)
        # if until_date is not None:
        #     until_date_dt = self.isValidDate(until_date)

        # # Filter identifiers based on the date range specified by from_date and until_date
        # filtered_identifiers = []

        # for record_identifier, record_data in metadata_dict.items():
        #     record_date_str = record_data["metadata"]["date"]

        #     # Convert the date string to a datetime object
        #     record_date = datetime.strptime(record_date_str, "%Y-%m-%d")

            # if (from_date_dt is None or record_date >= from_date_dt) and \
            #     (until_date_dt is None or record_date <= until_date_dt):
            #     filtered_identifiers.append((record_identifier, record_date_str))

        # Create the ListIdentifiers element
        list_identifiers_element = etree.Element('ListIdentifiers')

        if not metadata_dict:
            # If the metadata_dict is empty, add a noRecordsMatch error
            error_element = Errors.noRecordsMatch()
            root.append(error_element)
        else:
            for record_identifier in list(metadata_dict.keys()):
                record_element = etree.Element('record')

                header_element = etree.Element('header')
                identifier_element = etree.Element('identifier')
                identifier_element.text = record_identifier
                datestamp_element = etree.Element('datestamp')
                datestamp_element.text = 'datestamp'

                header_element.append(identifier_element)
                header_element.append(datestamp_element)
                record_element.append(header_element)
                list_identifiers_element.append(record_element)

        root.append(list_identifiers_element)

        return etree.tostring(root, pretty_print=True, encoding='unicode')

    def listMetadataFormats(self, root, metadata_dict, verb, identifier=None):
        self.addRequestElement(root, verb, identifier=identifier)

        if identifier:
            record_data = self.recordByIdentifier(metadata_dict, identifier)

            if record_data is None:
                error_element = Errors.idDoesNotExist()
                root.append(error_element)

                return etree.tostring(root, pretty_print=True, encoding='unicode')

        list_metadata_formats_element = etree.SubElement(root, 'ListMetadataFormats')

        metadata_formats = self.formats

        # Iterate through your metadata formats metadata_formats list
        for format_info in metadata_formats:
            metadata_format_element = etree.SubElement(list_metadata_formats_element, 'metadataFormat')

            self.addMetadataFormatElement(metadata_format_element, format_info)

        return etree.tostring(root, pretty_print=True, encoding='unicode')

    def listRecords(self, root, metadata_dict, verb, metadata_prefix, from_date=None,
                    until_date=None, set_spec=None, resumption_token=None):
        self.addRequestElement(root, verb, metadata_prefix=metadata_prefix, from_date=from_date,
                               until_date=until_date, set_spec=set_spec, resumption_token=resumption_token)

        from_date_dt = None
        until_date_dt = None

        if resumption_token is not None:
            error_element = Errors.badResumptionToken()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        if set_spec is not None:
            error_element = Errors.noSetHierarchy()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        # Check the validity of "from" and "until" parameters
        valid_from_date = from_date is None or self.isValidDate(from_date)
        valid_until_date = until_date is None or self.isValidDate(until_date)

        if not metadata_prefix or not valid_from_date or not valid_until_date:
            error_element = Errors.badArgument()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        if not self.validMetadataPrefix(metadata_prefix):
            error_element = Errors.cannotDisseminateFormat()
            root.append(error_element)
            return etree.tostring(root, pretty_print=True, encoding='unicode')

        # if from_date is not None:
        #     from_date_dt = self.isValidDate(from_date)
        # if until_date is not None:
        #     until_date_dt = self.isValidDate(until_date)

        # Filter identifiers based on the date range specified by from_date and until_date
        # filtered_identifiers = []

        # for record_identifier, record_data in metadata_dict.items():
        #     record_date_str = record_data["date"]
        #     record_metadata = record_data

        #     # Convert the date string to a datetime object
        #     record_date = datetime.strptime(record_date_str, "%Y-%m-%d")

            # if (from_date_dt is None or record_date >= from_date_dt) and \
            #     (until_date_dt is None or record_date <= until_date_dt):
            #     filtered_identifiers.append((record_identifier, record_date_str, record_metadata))

        list_records_element = etree.Element('ListRecords')

        if not metadata_dict:
            # If the metadata_dict dictionary is empty
            error_element = Errors.noRecordsMatch()
            root.append(error_element)
        else:
            for record_name, record_metadata in metadata_dict.items():
                record_element = etree.Element('record')

                header_element = etree.Element('header')
                identifier_element = etree.Element('identifier')
                identifier_element.text = f'https://github.com/grycap/tosca/blob/main/templates/{record_name}'
                datestamp_element = etree.Element('datestamp')
                datestamp_element.text = 'datestamp'
                metadata_element = etree.Element('metadata')

                if metadata_prefix == 'oai_dc':
                    metadata_xml = self.mapDC(record_metadata)

                if metadata_prefix == 'oai_openaire':
                    metadata_xml = self.mapOAIRE(record_metadata)

                # Append the generated XML to the metadata element
                metadata_element.append(etree.fromstring(metadata_xml))

                header_element.append(identifier_element)
                header_element.append(datestamp_element)
                record_element.append(header_element)
                record_element.append(metadata_element)

                list_records_element.append(record_element)

        root.append(list_records_element)

        return etree.tostring(root, pretty_print=True, encoding='unicode')

    def listSets(self, root, verb, set_spec=False, resumption_token=None):
        self.addRequestElement(root, verb)

        error_element = Errors.noSetHierarchy()
        root.append(error_element)

        return etree.tostring(root, pretty_print=True, encoding='unicode')

    def addMetadataFormatElement(self, parent_element, format_info):
        metadata_prefix_element = etree.SubElement(parent_element, 'metadataPrefix')
        metadata_prefix_element.text = format_info['metadataPrefix']

        schema_element = etree.SubElement(parent_element, 'schema')
        schema_element.text = format_info['schema']

        metadata_namespace_element = etree.SubElement(parent_element, 'metadataNamespace')
        metadata_namespace_element.text = format_info['metadataNamespace']

    def addIdentifyElements(self, identify_element):
        repository_name_element = etree.SubElement(identify_element, 'repositoryName')
        repository_name_element.text = self.repository_name

        base_url_element = etree.SubElement(identify_element, 'baseURL')
        base_url_element.text = self.repository_base_url

        protocol_version_element = etree.SubElement(identify_element, 'protocolVersion')
        protocol_version_element.text = self.repository_protocol_version

        earliest_datestamp_element = etree.SubElement(identify_element, 'earliestDatestamp')
        earliest_datestamp_element.text = self.earliest_datestamp

        deleted_record_element = etree.SubElement(identify_element, 'deletedRecord')
        deleted_record_element.text = self.repository_deleted_records

        granularity_element = etree.SubElement(identify_element, 'granularity')
        granularity_element.text = self.datestamp_granularity

        admin_email_element = etree.SubElement(identify_element, 'adminEmail')
        admin_email_element.text = self.repository_admin_email

    def addRequestElement(self, root, verb=None, metadata_prefix=None, identifier=None,
                          from_date=None, until_date=None, set_spec=None, resumption_token=None):
        if verb:
            # Create the request element and add the verb attribute
            request_element = etree.Element('request', verb=verb)

            # Add additional attributes to the request element when necessary
            if metadata_prefix:
                request_element.set('metadataPrefix', metadata_prefix)

            if identifier:
                request_element.set('identifier', identifier)

            if from_date:
                request_element.set('from', from_date)

            if until_date:
                request_element.set('until', until_date)

            if set_spec:
                request_element.set('setSpec', set_spec)

            if resumption_token:
                request_element.set('resumptionToken', resumption_token)

            # Set the text content of the request element
            request_element.text = f"{self.repository_base_url}"

            # Append the request element to the root
            root.append(request_element)

    def validMetadataPrefix(self, metadata_prefix):
        if metadata_prefix in self.valid_metadata_formats:
            return True

    def recordByIdentifier(self, metadata_dict, identifier):
        for record_name, record_metadata in metadata_dict.items():
            if f'https://github.com/grycap/tosca/blob/main/templates/{record_name}' == identifier:
                return record_metadata
        return None

    def isValidDate(self, date_str):
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            # Check if the date string exactly matches the expected format
            if date.strftime('%Y-%m-%d') == date_str:
                return date
        except ValueError:
            return None

    def mapOAIRE(self, metadata_dict):
        # Create an XML document
        root = etree.Element('{http://www.openarchives.org/OAI/2.0/oai_dc/}dc', nsmap={
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'datacite': 'http://datacite.org/schema/kernel-4',
            'oaire': 'http://namespace.openaire.eu/schema/oaire/',
        })

        # Add xsi:schemaLocation attribute
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                 'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd')

        # Define the DataCite namespace and associate it with the root element
        nsmap = {
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'datacite': 'http://datacite.org/schema/kernel-4',
            'oaire': 'http://namespace.openaire.eu/schema/oaire/',
        }
        etree.register_namespace('dc', nsmap['dc'])
        etree.register_namespace('datacite', nsmap['datacite'])
        etree.register_namespace('oaire', nsmap['oaire'])
        etree.register_namespace('oai_dc', nsmap['oai_dc'])

        for key, value in metadata_dict.items():
            if key == 'title':
                title_element = etree.Element('{http://datacite.org/schema/kernel-4}title')
                title_element.text = value
                root.append(title_element)
            if key == 'creator':
                creator_element = etree.Element('{http://datacite.org/schema/kernel-4}creator')
                creator_name_element = etree.Element('{http://datacite.org/schema/kernel-4}creatorName')
                creator_name_element.text = value
                creator_element.append(creator_name_element)
                root.append(creator_element)
            if key == 'date':
                date_element = etree.Element('{http://datacite.org/schema/kernel-4}date', dateType="Issued")
                date_element.text = value
                root.append(date_element)
            if key == 'resource_type':
                resource_type_element = etree.Element('{http://namespace.openaire.eu/schema/oaire/}resourceType',
                                                      resourceTypeGeneral="software",
                                                      uri="http://purl.org/coar/resource_type/c_5ce6")
                resource_type_element.text = value
                root.append(resource_type_element)
            if key == 'identifier':
                identifier_element = etree.Element('{http://datacite.org/schema/kernel-4}identifier',
                                                   identifierType="URN")
                identifier_element.text = value
                root.append(identifier_element)
            if key == 'rights':
                rights_element = etree.Element('{http://datacite.org/schema/kernel-4}rights',
                                               rightsURI="http://purl.org/coar/access_right/c_abf2")
                rights_element.text = value
                root.append(rights_element)
            if key == 'publisher':
                publisher_element = etree.Element('{http://purl.org/dc/elements/1.1/}publisher')
                publisher_element.text = value
                root.append(publisher_element)
            if key == 'version':
                version_element = etree.Element('{http://purl.org/dc/elements/1.1/}version')
                version_element.text = value
                root.append(version_element)
            if key == 'subject':
                subject_element = etree.Element('{http://namespace.openaire.eu/schema/oaire/}subject')
                subject_element.text = value
                root.append(subject_element)
            if key == 'related_identifier':
                related_identifier_element = etree.Element('{http://datacite.org/schema/kernel-4}relatedIdentifier',
                                                           relatedIdentifierType="DOI", relationType="isContinuedBy")
                related_identifier_element.text = value
                root.append(related_identifier_element)
            if key == 'format':
                format_element = etree.Element('{http://purl.org/dc/elements/1.1/}format')
                format_element.text = value
                root.append(format_element)

        # Serialize the XML to a string
        xml_string = etree.tostring(root, pretty_print=True, encoding='unicode')

        return xml_string

    def mapDC(self, metadata_dict):
        # Create an XML document
        root = etree.Element('{http://www.openarchives.org/OAI/2.0/oai_dc/}dc', nsmap={
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/',
        })

        # Add xsi:schemaLocation attribute
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation',
                 'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd')

        # Define the DataCite namespace and associate it with the root element
        nsmap = {
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            'dc': 'http://purl.org/dc/elements/1.1/',
        }
        etree.register_namespace('dc', nsmap['dc'])
        etree.register_namespace('oai_dc', nsmap['oai_dc'])

        for key, value in metadata_dict.items():
            if key == 'display_name':
                title_element = etree.Element('{http://purl.org/dc/elements/1.1/}title')
                title_element.text = value
                root.append(title_element)
            if key == 'creator':
                creator_element = etree.Element('{http://purl.org/dc/elements/1.1/}creator')
                creator_element.text = value
                root.append(creator_element)
            if key == 'date':
                date_element = etree.Element('{http://purl.org/dc/elements/1.1/}date')
                date_element.text = value
                root.append(date_element)
            if key == 'resource_type':
                resource_type_element = etree.Element('{http://purl.org/dc/elements/1.1/}type')
                resource_type_element.text = value
                root.append(resource_type_element)
            if key == 'identifier':
                identifier_element = etree.Element('{http://purl.org/dc/elements/1.1/}identifier')
                identifier_element.text = value
                root.append(identifier_element)
            if key == 'rights':
                rights_element = etree.Element('{http://purl.org/dc/elements/1.1/}rights')
                rights_element.text = value
                root.append(rights_element)
            if key == 'publisher':
                publisher_element = etree.Element('{http://purl.org/dc/elements/1.1/}publisher')
                publisher_element.text = value
                root.append(publisher_element)
            if key == 'version':
                related_identifier_element = etree.Element('{http://purl.org/dc/elements/1.1/}version')
                related_identifier_element.text = value
                root.append(related_identifier_element)
            if key == 'tag':
                subject_element = etree.Element('{http://purl.org/dc/elements/1.1/}subject')
                subject_element.text = value
                root.append(subject_element)
            if key == 'childs':
                related_identifier_element = etree.Element('{http://purl.org/dc/elements/1.1/}relation')
                # childs = value["childs"]
                # related_identifier_element.text = ', '.join(childs)
                root.append(related_identifier_element)
            if key == 'format':
                format_element = etree.Element('{http://purl.org/dc/elements/1.1/}format')
                format_element.text = value
                root.append(format_element)
            if key == 'description':
                related_identifier_element = etree.Element('{http://purl.org/dc/elements/1.1/}description')
                related_identifier_element.text = value
                root.append(related_identifier_element)

        # Serialize the XML to a string
        xml_string = etree.tostring(root, pretty_print=True, encoding='unicode')

        return xml_string