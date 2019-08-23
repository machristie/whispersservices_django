class ModelFieldDescriptions:
    def __init__(self, field_name_list):
        for k, v in field_name_list.items():
            setattr(self, k, v)


event = ModelFieldDescriptions({
    'event': 'A foreign key integer value identifying an event',
    'event_type': 'A foreign key integer value identifying a wildlife morbidity or mortality event',
    'event_reference': 'Name or number for an event designated by event owner',
    'complete': 'A boolean value indicating if an event is complete or incomplete. A complete event means it has ended, diagnostic tests are completed, and all information is updated in WHISPers',
    'start_date': 'The date this event started on',
    'end_date': 'The date this event ended on',
    'affected_count': 'An integer value for total number affected in this event',
    'staff': 'A foreign key integer value identifying a staff member',
    'event_status': 'A foreign key integer value identifying event statuses specific to NWHC.',
    'legal_status': 'A foreign key integer value identifying legal procedures associated with an event',
    'legal_number': 'An alphanumeric value of legal case identifier',
    'quality_check': 'The date an NWHC staff and event owner make changes and check the record',
    'public': 'A boolean value indicating if an event is public or not',
    'read_collaborators': 'A many to many releationship of read collaborators based on a foreign key integer value indentifying a user',
    'write_collaborators': 'A many to many releationship of write collaborators based on a foreign key integer value indentifying a user',
    'eventgroups': 'A many to many relationship of event groups based on a foreign key integer identifying an event group',
    'organizations': 'A many to many releationship of organizations based on a foreign key integer value indentifying an organization',
    'contacts': 'A many to many releationship of contacts based on a foreign key integer value indentifying a contact',
    'comments': 'A many to many releationship of comments based on a foreign key integer value indentifying a comment'
})

eventlocation = ModelFieldDescriptions({
    'event_location': 'A foreign key integer value identifying an event location',
    'name': 'An alphanumeric value of the name of this event location test',
    'complete': 'A boolean value indicating if an event is complete or incomplete. A complete event means it has ended, diagnostic tests are completed, and all information is updated in WHISPers',
    'start_date': 'The date of the event end at this location in "YYYY-MM-DD" format',
    'end_date': 'The date of the event end at this location in "YYYY-MM-DD" format',
    'country': 'A foreign key integer value identifying the country to which this event location belongs',
    'administrative_level_one': 'A foreign key integer value identifying the administrative level one to which this event location belongs',
    'administrative_level_two': 'A foreign key integer value identifying the administrative level two to which this event location belongs.',
    'county_multiple': 'A foreign key integer value identifying legal procedures associated with an event',
    'county_unknown': 'An alphanumeric value of legal case identifier',
    'latitude': 'The date an NWHC staff and event owner make changes and check the record',
    'longitude': 'A boolean value indicating if an event is public or not',
    'priority': 'A many to many releationship of read collaborators based on a foreign key integer value indentifying a user',
    'land_ownership': 'A many to many releationship of write collaborators based on a foreign key integer value indentifying a user',
    'contacts': 'A foreign key integer identifying the user who last modified the object',
    'flyways': 'A many to many releationship of flyways based on a foreign key integer value indentifying a flyway',
    'gnis_name': 'An alphanumeric value of a gnis name',
    'gnis_id': 'A foreign key integer value identifying a gnis',
    'comments': 'A many to many releationship of comments based on a foreign key integer value indentifying a comment'
})

eventorganization = ModelFieldDescriptions({
    'created_date': 'The date this object was created in "YYYY-MM-DD" format',
    'modified_by': 'A foreign key integer identifying the user who last modified the object',
    'organization': 'A foreign key integer value identifying a organization',
    'created_by': 'A foreign key integer identifying the user who created the object',
    'priority': 'An integer value indicating the event organizations priority'
})

history = ModelFieldDescriptions({
    'created_date': 'The date this object was created in "YYYY-MM-DD" format',
    'created_by': 'A foreign key integer identifying the user who created the object',
    'created_by_string': 'An alphanumeric value of user who created the object',
    'modified_date': 'The date this object was last modified on in "YYYY-MM-DD" format',
    'modified_by': 'A foreign key integer identifying the user who last modified the object',
    'name': 'An alphanumeric value of the name of this object'
})

eventgroup = ModelFieldDescriptions({
    'id': 'A foreign key integer value identifying a wildlife morbidity or mortality event',
    'eventgroup': 'A foreign key integer identifying an event group',
    'event_reference': 'Name or number for an event designated by event owner',
    'comments': 'A many to many relationship of comments based on a foreign key integer value indentifying a comment',
    'category': 'A foreign key integer value identifying a category',
})

eventabstract = ModelFieldDescriptions({
    'text': 'An alphanumeric value of information',
    'lab_id': 'An foreign key integer value identifying a lab',
})

eventcase = ModelFieldDescriptions({
    'case': 'An alphanumeric value of information on a case'
})

eventlabsite = ModelFieldDescriptions({
    'lab_id': 'A foreign key integer value identifying a lab'
})

contacts = ModelFieldDescriptions({
    'contact': 'A foreign key integer value indentifying a contact',
    'contacts': 'A many to many relationship of contacts based on a foreign key integer value indentifying a contact',
    'contact_type': 'A foreign key integer value identifying the contact type for this contact',
    'first_name': 'An alphanumeric value of the first name of this contact',
    'last_name': 'An alphanumeric value of the last name of this contact',
    'email': 'An alphanumeric value of the email of this contact',
    'phone': 'An alphanumeric value of the phone of this contact',
    'affiliation': 'An alphanumeric value identifying the affiliation of this contact',
    'title': 'An alphanumeric value of the title of this contact',
    'position': 'An alphanumeric value of the position of this contact',
    'organization': 'A foreign key integer value identifying the organization to which this contact belongs to',
    'name': 'An alphanumeric value of the name of this contact type'
})

staff = ModelFieldDescriptions({
    'first_name': 'An alphanumeric value of the staff members first name',
    'last_name': 'An alphanumeric value of the staff members last name',
    'role': 'A foreign key integer value for the staff role',
    'active': 'A foreign key integer value for the staff role',
})

country = ModelFieldDescriptions({
    'abbreviation': 'An alphanumeric value of the usual abbreviation of this country',
    'calling_code': 'An integer value identifying the calling code for this country',
})

administratives = ModelFieldDescriptions({
    'country': 'A foreign key integer value identifying the country to with this administrative level one belongs',
    'country_localities': 'A foreign key integer value identifying the country to which this administrative level locality belongs',
    'abbreviation': 'An alphanumeric value of the usual abbreviation of this administrative level one',
    'name': 'An alphanumeric value of the name of this administrative level two',
    'administrative_level_one': 'A foreign key integer value identifying the administrative level one to which this administrative level two belongs',
    'points': 'An alphanumeric value of the points of this administrative level two',
    'centroid_latitude': 'A fixed-precision decimal number value indentifying the latitude for this administrative level two',
    'centroid_longitude': 'An alphanumeric value of the usual abbreviation of this administrative level one',
    'fips_code': 'An alphanumeric value of the FIPS code for this administrative level two',
    'admin_level_one_name': 'An alphanumeric value of the name of the administrative level one',
    'admin_level_two_name': 'An alphanumeric value of the name of the administrative level two',
})

speciesall = ModelFieldDescriptions({
    'species': 'A foreign key integer value identifying a species',
    'population_count': 'An integer value indicating the population count',
    'sick_count': 'An integer value indicating the sick count',
    'sick_count_estimated': 'An integer value indicating the estimated sick count',
    'dead_count': 'An integer value indicating the dead count',
    'dead_count_estimated': 'An integer value indicating the estimated dead count',
    'priority': 'An integer value indicating the location species priority',
    'captive': 'A boolean value indicating if the location species was captive or not',
    'age_bias': 'A foreign key integer value identifying an age bias',
    'sex_bias': 'A foreign key integer value identifying an sex bias',
    'name': 'An alphanumeric value of the the name of this species',
    'class_name': 'An alphanumeric value of the name of this species class',
    'order_name': 'An alphanumeric value of the name of this species order',
    'family_name': 'An alphanumeric value of the name of this species family',
    'sub_family_name': 'An alphanumeric value of the name of this species sub family',
    'genus_name': 'An alphanumeric value of the name of this species genus',
    'species_latin_name': 'An alphanumeric value of the latin name of this species',
    'subspecies_latin_name': 'An alphanumeric value of the latin name of this subspecies',
    'location_species': 'A foreign key integer value identifying a location species for this species diagnosis',
    'tsn': 'An intger value identifying a TSN'
})

users = ModelFieldDescriptions({
    'role': 'A foreign key integer value identifying a role assigned to a user',
    'organization': 'A foreign key integer value identifying an organization assigned to a user',
    'circles': 'A many to many releationship of circles based on a foreign key integer value indentifying a circle',
    'active_key': 'An alphanumeric value of the active key for this user',
    'user_status': 'An alphanumeric value of the status for this user',
    'username': 'An alphanumeric value of the username for a user',
    'email': 'An alphanumeric value of the email for a user'
})

diagnoses = ModelFieldDescriptions({
    'diagnosis': 'A foreign key integer value identifying a diagnosis',
    'diagnosis_type': 'A foreign key integer value identifying the diagnosis type',
    'color': 'A alphanumeric value of the color of this diagnosis type',
    'suspect': 'A boolean value where if "true" then the diagnosis is suspect',
    'major': 'A boolean value indicating if the event diagnosis is major or not',
    'species_diagnosis': 'A foreign key integer value identifying a diagnosis for this species diagnosis',
    'cause': 'A foreign key integer value identifying the incidents cause for this species diagnosis',
    'basis': 'A foreign key integer value identifying a basis (how a species diagnosis was determined) for this species diagnosis',
    'tested_count': 'An integer value indicating the tested count for this species diagnosis',
    'diagnosis_count': 'An integer value indicating the diagnosis count for this species diagnosis',
    'positive_count': 'An integer value indicating the positive count for this species diagnosis',
    'suspect_count': 'An integer value indicating the suspect count for this species diagnosis',
    'pooled': 'A boolean value indicating if the species diagnosis was pooled or not',
    'organizations': 'A many to many releationship of organizations based on a foreign key integer value indentifying an organization',
    'priority': 'An integer value indicating the priority of this diagnosis'
})

servicerequest = ModelFieldDescriptions({
    'request_type': 'A foreign key integer value identifying a request type for this service submission request',
    'request_response': 'A foreign key integer value identifying a response to this request',
    'response_by': 'A foreign key integer value identifying a user',
    'created_time': 'The time this service request was submitted',
    'comments': 'An alphanumeric value for the comment of the service submission request'
})

comments = ModelFieldDescriptions({
    'comment': 'A foreign key integer value identifying a comment',
    'comment_type': 'A foreign key integer value identifying the comment type of this comment',
    'content_type': 'A foreign key integer value identifying the content type for this comment',
    'object_id': 'A positive integer value indentifying an object'
})

artifact = ModelFieldDescriptions({
    'filename': 'An alphanumeric value of the filename of this artifact',
    'keywords': 'An alphanumeric value of the keywords of this artifact',
})

circles = ModelFieldDescriptions({
    'description': 'An alphanumeric value of the description of this circle',
    'circle': 'A foreign key integer value identifying a circle',
    'user': 'A foreign key integer value identifying a circle user'
})

organizations = ModelFieldDescriptions({
    'private_name': 'An alphanumeric value of the private name of this organization',
    'address_one': 'An alphanumeric value of the address one of this organization',
    'address_two': 'An alphanumeric value of the address two of this organization',
    'city': 'An alphanumeric value of the city of this organization',
    'postal_code': 'An alphanumeric value of the postal code of this organization',
    'administrative_level_one': 'A foreign key integer value identifying the administrative level one to which this organization belongs',
    'country': 'A foreign key integer value identifying the country to which this organization belongs',
    'phone': 'An alphanumeric value of the phone number of this organization',
    'parent_organization': 'A foreign key integer value identifying the parent organization',
    'do_not_publish': 'A boolean value indicating if an organization is supposed to be published or not',
    'laboratory': 'A boolean value indicating if an organization has a laboratory or not'
})

search = ModelFieldDescriptions({
    'name': 'An alphanumeric value of the name of this search',
    'data': 'A JSON object containing the search data',
    'count': 'An integer value indentifying the count of searches',
})

queryparams = ModelFieldDescriptions({
    'administrative_level_one': 'A foreign key integer value identifying an administrative level one',
    'administrative_level_two': 'A foreign key integer value identifying an administrative level two',
    'flyway': 'A foreign key integer value indentifying a flyway',
    'country': 'A foreign key integer value identifying a country',
    'gnis_id': 'A foreign key integer value identifying a gnis',
    'diagnosis_type': 'A foreign key integer value identifying the diagnosis type',
    'contains': 'An alphanumeric value of the contents of a comment',
    'users': 'A foreign key value identifying users',
    'contacts': 'A foreign key value identifying contacts',
    'laboratory': 'A boolean value indicating if there is laboratory or not',
    'ordering_param_contacts': 'Order by options include affiliation, created_by, created_by_id, created_date, email, event, eventcontact, eventlocationcontact, eventlocations, first_name, id, last_name, modified_by, modified_by_id, modified_date, organization, organization_id, phone, position, title',
    'org': 'A alphanumeric value identifying an organization',
    'owner_org': 'An alphanumeric value identifying an owner organization',
    'ordering_param_search': 'Order by options include count, created_by, created_by_id, created_date, data, id, modified_by, modified_by_id, modified_date, name',
    'ordering_user_search': 'Order by options include count, created_by, created_by_id, created_date, data, id, modified_by, modified_by_id, modified_date, name',
    'owner': 'A foreign key integer value identifying an owner',
})
