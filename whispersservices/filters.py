from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, CharFilter, BooleanFilter
from whispersservices.models import *
from whispersservices.field_descriptions import *


# TODO: improve labels such that only unique fields (like affected_count__gte) have string literal values, while all other labels (like diagnosis) are assigned to variables
class EventSummaryFilter(FilterSet):
    complete = BooleanFilter(field_name='complete', lookup_expr='exact', label=event.complete)
    event_type = NumberFilter(field_name='event_type', lookup_expr='exact', label=event.event_type)
    diagnosis = NumberFilter(field_name='diagnosis', lookup_expr='exact', label=diagnoses.diagnosis)
    diagnosis_type = NumberFilter(field_name='diagnosis_type', lookup_expr='exact', label=diagnoses.diagnosis_type)
    species = NumberFilter(field_name='species', lookup_expr='exact', label=speciesall.species)
    administrative_level_one = NumberFilter(
        field_name='administrative_level_one', lookup_expr='exact', label=queryparams.administrative_level_one)
    administrative_level_two = NumberFilter(
        field_name='administrative_level_two', lookup_expr='exact', label=queryparams.administrative_level_two)
    flyway = NumberFilter(field_name='flyway', lookup_expr='exact', label=queryparams.flyway)
    country = NumberFilter(field_name='country', lookup_expr='exact', label=queryparams.country)
    gnis_id = NumberFilter(field_name='gnis_id', lookup_expr='exact', label=queryparams.gnis_id)
    affected_count__gte = NumberFilter(field_name='affected_count__gte', lookup_expr='gte', label='affected_count__gte')
    affected_count__lte = NumberFilter(field_name='affected_count__lte', lookup_expr='lte', label='affected_count__lte')
    start_date = BooleanFilter(field_name='start_date', lookup_expr='exact', label=event.start_date)
    end_date = BooleanFilter(field_name='end_date', lookup_expr='exact', label=event.end_date)

    class Meta:
        model = Event
        fields = ['complete', 'event_type', 'diagnosis', 'diagnosis_type', 'species', 'administrative_level_one',
                  'administrative_level_two', 'flyway', 'country', 'gnis_id', 'affected_count__gte',
                  'affected_count__lte', 'start_date', 'end_date']

class UserFilter(FilterSet):
    username = CharFilter(field_name='username', lookup_expr='exact', label=users.username)
    email = CharFilter(field_name='email', lookup_expr='exact', label=users.email)
    role = NumberFilter(field_name='role', lookup_expr='exact', label=users.role)
    organization = NumberFilter(field_name='organization', lookup_expr='exact', label=users.organization)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'organization']

class AdministrativeLevelOneFilter(FilterSet):
    country = NumberFilter(field_name='country', lookup_expr='exact', label=queryparams.country)


    class Meta:
        model = AdministrativeLevelOne
        fields = ['country']

class DiagnosisFilter(FilterSet):
    diagnosis_type = NumberFilter(field_name='diagnosis_type', lookup_expr='exact', label=queryparams.diagnosis_type)


    class Meta:
        model = Diagnosis
        fields = ['diagnosis_type']

class CommentFilter(FilterSet):
    contains = CharFilter(field_name='contains', lookup_expr='exact', label=queryparams.contains)


    class Meta:
        model = Comment
        fields = ['contains']

class ContactsFilter(FilterSet):
    ordering = CharFilter(field_name='ordering_param', lookup_expr='exact', label=queryparams.ordering_param_contacts)
    org = NumberFilter(field_name='org', lookup_expr='exact', label=queryparams.org)
    owner_org = CharFilter(field_name='owner_org', lookup_expr='exact', label=queryparams.owner_org)


    class Meta:
        model = Contact
        fields = ['ordering', 'org', 'owner_org']

class OrganizationFilter(FilterSet):
    users = CharFilter(field_name='users', lookup_expr='exact', label=queryparams.users)
    contacts = CharFilter(field_name='contacts', lookup_expr='exact', label=queryparams.contacts)
    laboratory = BooleanFilter(field_name='laboratory', lookup_expr='exact', label=queryparams.laboratory)

    class Meta:
        model = Organization
        fields = ['users', 'contacts', 'laboratory']

class SearchFilter(FilterSet):
    ordering = CharFilter(field_name='ordering', lookup_expr='exact', label=queryparams.ordering_param_search)
    #owner = NumberFilter(field_name='owner', lookup_expr='exact', label=queryparams.owner)

    class Meta:
        model = Search
        fields = ['ordering']
