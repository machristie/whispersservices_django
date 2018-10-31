import re
from datetime import datetime as dt
from collections import OrderedDict
from django.core.mail import EmailMessage
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework import views, viewsets, authentication, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import BaseParser
from rest_framework.exceptions import PermissionDenied, APIException
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as csv_renderers
from whispersservices.serializers import *
from whispersservices.models import *
from whispersservices.permissions import *
from whispersservices.pagination import *
from dry_rest_permissions.generics import DRYPermissions
User = get_user_model()


########################################################################################################################
#
#  copyright: 2017 WiM - USGS
#  authors: Aaron Stephenson USGS WIM (Web Informatics and Mapping)
#
#  In Django, a view is what takes a Web request and returns a Web response. The response can be many things, but most
#  of the time it will be a Web page, a redirect, or a document. In this case, the response will almost always be data
#  in JSON format.
#
#  All these views are written as Class-Based Views (https://docs.djangoproject.com/en/2.0/topics/class-based-views/)
#  because that is the paradigm used by Django Rest Framework (http://www.django-rest-framework.org/api-guide/views/)
#  which is the toolkit we used to create web services in Django.
#
#
########################################################################################################################


class PlainTextParser(BaseParser):
    media_type = 'text/plain'

    def parse(self, stream, media_type=None, parser_context=None):
        text = stream.read().decode("utf-8")
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        return text


PK_REQUESTS = ['retrieve', 'update', 'partial_update', 'destroy']
LIST_DELIMETER = ','


def construct_email(request_data, requester_email, message):
    # construct and send the request email
    subject = "Assistance Request"
    body = "A person (" + requester_email + ") has requested assistance:\r\n\r\n"
    body += message + "\r\n\r\n"
    body += request_data
    from_address = settings.EMAIL_WHISPERS
    to_list = [settings.EMAIL_WHISPERS, ]
    bcc_list = []
    reply_to_list = [requester_email, ]
    headers = None  # {'Message-ID': 'foo'}
    email = EmailMessage(subject, body, from_address, to_list, bcc_list, reply_to=reply_to_list, headers=headers)
    try:
        # TODO: uncomment next line when code is deployed on the production server
        # email.send(fail_silently=False)
        return Response({"status": request_data}, status=200)
    except TypeError:
        return Response({"status": "send email failed, please contact the administrator."}, status=500)


######
#
#  Abstract Base Classes
#
######


class AuthLastLoginMixin(object):
    """
    This class will update the user's last_login field each time a request is received
    """

    # permission_classes = (permissions.IsAuthenticated,)

    def finalize_response(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        return super(AuthLastLoginMixin, self).finalize_response(request, *args, **kwargs)


class HistoryViewSet(AuthLastLoginMixin, viewsets.ModelViewSet):
    """
    This class will automatically assign the User ID to the created_by and modified_by history fields when appropriate
    """

    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.OrderingFilter,)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, modified_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    # override the default pagination to allow disabling of pagination
    def paginate_queryset(self, *args, **kwargs):
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(*args, **kwargs)


class ReadOnlyHistoryViewSet(AuthLastLoginMixin, viewsets.ReadOnlyModelViewSet):
    """
    This class will automatically assign the User ID to the created_by and modified_by history fields when appropriate
    """

    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.OrderingFilter,)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, modified_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    # override the default pagination to allow disabling of pagination
    def paginate_queryset(self, *args, **kwargs):
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(*args, **kwargs)


######
#
#  Events
#
######


class EventViewSet(HistoryViewSet):
    permission_classes = (DRYPermissions,)

    # TODO: would this be true?
    def destroy(self, request, *args, **kwargs):
        # if the event is complete, it cannot be deleted
        if self.get_object().complete:
            message = "A complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventViewSet, self).destroy(request, *args, **kwargs)

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        user = self.request.user
        queryset = Event.objects.all()

        # all requests from anonymous users must only return public data
        if not user.is_authenticated:
            return queryset.filter(public=True)
        # for pk requests, non-public data can only be returned to the owner or their org or shared circles or admins
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                queryset = Event.objects.filter(id=pk)
                obj = queryset[0]
                circle_read = obj.circle_read if obj.circle_read is not None else []
                circle_write = obj.circle_write if obj.circle_write is not None else []
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization
                                        or user in circle_read or user in circle_write
                                        or user.role.is_superadmin or user.role.is_admin):
                    return queryset
            return queryset.filter(public=True)
        # all list requests, and all requests from public users (except circle members), must only return public data
        elif self.action == 'list' or user.role.is_public:
            return queryset.filter(public=True)
        # that leaves the create request, implying that the requester is the owner
        else:
            return queryset

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous users must use the public serializer
        if not user.is_authenticated:
            return EventPublicSerializer
        # for all non-admins, primary key requests can only be performed by the owner or their org or shared circles
        if self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = Event.objects.filter(id=pk).first()
                if obj is not None:
                    circle_read = obj.circle_read if obj.circle_read is not None else []
                    circle_write = obj.circle_write if obj.circle_write is not None else []
                    # admins have full access to all fields
                    if user.role.is_superadmin or user.role.is_admin:
                        return EventAdminSerializer
                    elif user in circle_read:
                        # circle_read members can only retrieve
                        if self.action == 'retrieve':
                            return EventSerializer
                        else:
                            raise PermissionDenied
                            # message = "You do not have permission to perform this action"
                            # return JsonResponse({"Permission Denied": message}, status=403)
                    # circle_write members and org partners can retrieve and update but not delete
                    elif user in circle_write or (
                            user.organization == obj.created_by.organization and user.role.is_partner):
                        if self.action == 'delete':
                            raise PermissionDenied
                            # message = "You do not have permission to perform this action"
                            # return JsonResponse({"Permission Denied": message}, status=403)
                        else:
                            return EventSerializer
                    # owner and org partner managers and org partner admins have full access to non-admin fields
                    elif user == obj.created_by or (user.organization == obj.created_by.organization and (
                            user.role.is_partnermanager or user.role.is_partneradmin)):
                        return EventSerializer
            return EventPublicSerializer
        # all list requests, and all requests from public users (except circle members), must use the public serializer
        elif self.action == 'list' or user.role.is_public:
            return EventPublicSerializer
        # for all other requests admins have access to all fields
        elif user.role.is_superadmin or user.role.is_admin:
            return EventAdminSerializer
        # all create requests imply that the requester is the owner, so use the owner serializer
        elif self.action == 'create':
            return EventSerializer
        # non-admins and non-owners (and non-owner orgs and shared circles) must use the public serializer
        else:
            return EventPublicSerializer


class EventSuperEventViewSet(HistoryViewSet):
    queryset = EventSuperEvent.objects.all()
    serializer_class = EventSuperEventSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to superevents can be deleted
        if self.get_object().complete:
            message = "SuperEvent for a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventSuperEventViewSet, self).destroy(request, *args, **kwargs)


class SuperEventViewSet(HistoryViewSet):
    queryset = SuperEvent.objects.all()
    serializer_class = SuperEventSerializer


class EventTypeViewSet(HistoryViewSet):
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer


class StaffViewSet(HistoryViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


class LegalStatusViewSet(HistoryViewSet):
    queryset = LegalStatus.objects.all()
    serializer_class = LegalStatusSerializer


class EventStatusViewSet(HistoryViewSet):
    queryset = EventStatus.objects.all()
    serializer_class = EventStatusSerializer


class EventAbstractViewSet(HistoryViewSet):
    serializer_class = EventAbstractSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to abstracts can be deleted
        if self.get_object().event.complete:
            message = "Abstracts from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventAbstractViewSet, self).destroy(request, *args, **kwargs)

    def get_queryset(self):
        queryset = EventAbstract.objects.all()
        contains = self.request.query_params.get('contains', None)
        if contains is not None:
            queryset = queryset.filter(text__contains=contains)
        return queryset


class EventCaseViewSet(HistoryViewSet):
    queryset = EventCase.objects.all()
    serializer_class = EventCaseSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to cases can be deleted
        if self.get_object().event.complete:
            message = "Cases from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventCaseViewSet, self).destroy(request, *args, **kwargs)


class EventLabsiteViewSet(HistoryViewSet):
    queryset = EventLabsite.objects.all()
    serializer_class = EventLabsiteSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to labsites can be deleted
        if self.get_object().event.complete:
            message = "Labsites from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventLabsiteViewSet, self).destroy(request, *args, **kwargs)


class EventOrganizationViewSet(HistoryViewSet):
    queryset = EventOrganization.objects.all()

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to organizations can be deleted
        if self.get_object().event.complete:
            message = "Organizations from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventOrganizationViewSet, self).destroy(request, *args, **kwargs)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous users must use the public serializer
        if not user.is_authenticated:
            return EventOrganizationPublicSerializer
        # all list requests, and all requests from public users, must use the public serializer
        if self.action == 'list' or user.role.is_public:
            return EventOrganizationPublicSerializer
        # for all other requests admins have access to all fields
        if user.role.is_superadmin or user.role.is_admin:
            return EventOrganizationSerializer
        # for all non-admins, all post requests imply that the requester is the owner, so use the owner serializer
        elif self.action == 'create':
            return EventOrganizationSerializer
        # for all non-admins, requests requiring a primary key can only be performed by the owner or their org
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = EventOrganization.objects.filter(id=pk).first()
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization):
                    return EventOrganizationSerializer
            return EventOrganizationPublicSerializer
        # non-admins and non-owners (and non-owner orgs) must use the public serializer
        else:
            return EventOrganizationPublicSerializer


class EventContactViewSet(HistoryViewSet):
    queryset = EventContact.objects.all()
    serializer_class = EventContactSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to contacts can be deleted
        if self.get_object().event.complete:
            message = "Contacts from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventContactViewSet, self).destroy(request, *args, **kwargs)


######
#
#  Locations
#
######


class EventLocationViewSet(HistoryViewSet):
    permission_classes = (DRYPermissions,)
    queryset = EventLocation.objects.all()

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to locations can be deleted
        if self.get_object().event.complete:
            message = "Locations from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventLocationViewSet, self).destroy(request, *args, **kwargs)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous users must use the public serializer
        if not user.is_authenticated:
            return EventLocationPublicSerializer
        # all list requests, and all requests from public users, must use the public serializer
        if self.action == 'list' or user.role.is_public:
            return EventLocationPublicSerializer
        # for all other requests admins have access to all fields
        if user.role.is_superadmin or user.role.is_admin:
            return EventLocationSerializer
        # for all non-admins, all post requests imply that the requester is the owner, so use the owner serializer
        elif self.action == 'create':
            return EventLocationSerializer
        # for all non-admins, requests requiring a primary key can only be performed by the owner or their org
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = EventLocation.objects.filter(id=pk).first()
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization):
                    return EventLocationSerializer
            return EventLocationPublicSerializer
        # non-admins and non-owners (and non-owner orgs) must use the public serializer
        else:
            return EventLocationPublicSerializer


class EventLocationContactViewSet(HistoryViewSet):
    queryset = EventLocationContact.objects.all()
    serializer_class = EventLocationContactSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to location contacts can be deleted
        if self.get_object().event_location.event.complete:
            message = "Contacts from a location from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventLocationContactViewSet, self).destroy(request, *args, **kwargs)


class CountryViewSet(HistoryViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class AdministrativeLevelOneViewSet(HistoryViewSet):
    serializer_class = AdministrativeLevelOneSerializer

    def get_queryset(self):
        queryset = AdministrativeLevelOne.objects.all()
        countries = self.request.query_params.get('country', None)
        if countries is not None:
            countries_list = countries.split(',')
            queryset = queryset.filter(country__in=countries_list)
        return queryset


class AdministrativeLevelTwoViewSet(HistoryViewSet):
    serializer_class = AdministrativeLevelTwoSerializer

    @action(detail=False, methods=['post'], parser_classes=(PlainTextParser,))
    def request_new(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        message = "Please add a new administrative level two:"
        return construct_email(request.data, request.user.email, message)

    def get_queryset(self):
        queryset = AdministrativeLevelTwo.objects.all()
        administrative_level_one = self.request.query_params.get('administrativelevelone', None)
        if administrative_level_one is not None:
            administrative_level_one_list = administrative_level_one.split(',')
            queryset = queryset.filter(administrative_level_one__in=administrative_level_one_list)
        return queryset


class AdministrativeLevelLocalityViewSet(HistoryViewSet):
    queryset = AdministrativeLevelLocality.objects.all()
    serializer_class = AdministrativeLevelLocalitySerializer


class LandOwnershipViewSet(HistoryViewSet):
    queryset = LandOwnership.objects.all()
    serializer_class = LandOwnershipSerializer


class EventLocationFlywayViewSet(HistoryViewSet):
    queryset = EventLocationFlyway.objects.all()
    serializer_class = EventLocationFlywaySerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to location flyways can be deleted
        if self.get_object().event_location.event.complete:
            message = "Flyways from a location from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventLocationFlywayViewSet, self).destroy(request, *args, **kwargs)


class FlywayViewSet(HistoryViewSet):
    queryset = Flyway.objects.all()
    serializer_class = FlywaySerializer


######
#
#  Species
#
######


class LocationSpeciesViewSet(HistoryViewSet):
    queryset = LocationSpecies.objects.all()

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to location species can be deleted
        if self.get_object().event_location.event.complete:
            message = "Species from a location from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(LocationSpeciesViewSet, self).destroy(request, *args, **kwargs)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous users must use the public serializer
        if not user.is_authenticated:
            return LocationSpeciesPublicSerializer
        # all list requests, and all requests from public users, must use the public serializer
        if self.action == 'list' or user.role.is_public:
            return LocationSpeciesPublicSerializer
        # for all other requests admins have access to all fields
        if user.role.is_superadmin or user.role.is_admin:
            return LocationSpeciesSerializer
        # for all non-admins, all post requests imply that the requester is the owner, so use the owner serializer
        elif self.action == 'create':
            return LocationSpeciesSerializer
        # for all non-admins, requests requiring a primary key can only be performed by the owner or their org
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = LocationSpecies.objects.filter(id=pk).first()
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization):
                    return LocationSpeciesSerializer
            return LocationSpeciesPublicSerializer
        # non-admins and non-owners (and non-owner orgs) must use the public serializer
        else:
            return LocationSpeciesPublicSerializer


class SpeciesViewSet(HistoryViewSet):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer

    @action(detail=False, methods=['post'], parser_classes=(PlainTextParser,))
    def request_new(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        message = "Please add a new species:"
        return construct_email(request.data, request.user.email, message)


class AgeBiasViewSet(HistoryViewSet):
    queryset = AgeBias.objects.all()
    serializer_class = AgeBiasSerializer


class SexBiasViewSet(HistoryViewSet):
    queryset = SexBias.objects.all()
    serializer_class = SexBiasSerializer


######
#
#  Diagnoses
#
######


class DiagnosisViewSet(HistoryViewSet):
    serializer_class = DiagnosisSerializer

    @action(detail=False, methods=['post'], parser_classes=(PlainTextParser,))
    def request_new(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        message = "Please add a new diagnosis:"
        return construct_email(request.data, request.user.email, message)

    # override the default queryset to allow filtering by URL argument diagnosis_type
    def get_queryset(self):
        queryset = Diagnosis.objects.all()
        diagnosis_type = self.request.query_params.get('diagnosis_type', None)
        if diagnosis_type is not None:
            diagnosis_type_list = diagnosis_type.split(',')
            queryset = queryset.filter(diagnosis_type__in=diagnosis_type_list)
        return queryset


class DiagnosisTypeViewSet(HistoryViewSet):
    queryset = DiagnosisType.objects.all()
    serializer_class = DiagnosisTypeSerializer


class EventDiagnosisViewSet(HistoryViewSet):
    permission_classes = (DRYPermissions,)
    queryset = EventDiagnosis.objects.all()

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to diagnoses can be deleted
        if self.get_object().event.complete:
            message = "Diagnoses from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(EventDiagnosisViewSet, self).destroy(request, *args, **kwargs)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous users must use the public serializer
        if not user.is_authenticated:
            return EventDiagnosisPublicSerializer
        # all list requests, and all requests from public users, must use the public serializer
        if self.action == 'list' or user.role.is_public:
            return EventDiagnosisPublicSerializer
        # for all other requests admins have access to all fields
        if user.role.is_superadmin or user.role.is_admin:
            return EventDiagnosisSerializer
        # for all non-admins, all post requests imply that the requester is the owner, so use the owner serializer
        elif self.action == 'create':
            return EventDiagnosisSerializer
        # for all non-admins, requests requiring a primary key can only be performed by the owner or their org
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = EventDiagnosis.objects.filter(id=pk).first()
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization):
                    return EventDiagnosisSerializer
            return EventDiagnosisPublicSerializer
        # non-admins and non-owners (and non-owner orgs) must use the public serializer
        else:
            return EventDiagnosisPublicSerializer


class SpeciesDiagnosisViewSet(HistoryViewSet):
    permission_classes = (DRYPermissions,)
    queryset = SpeciesDiagnosis.objects.all()

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to location species diagnoses can be deleted
        if self.get_object().location_species.event_location.event.complete:
            message = "Diagnoses from a species from a location from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(SpeciesDiagnosisViewSet, self).destroy(request, *args, **kwargs)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous users must use the public serializer
        if not user.is_authenticated:
            return SpeciesDiagnosisPublicSerializer
        # all list requests, and all requests from public users, must use the public serializer
        if self.action == 'list' or user.role.is_public:
            return SpeciesDiagnosisPublicSerializer
        # for all other requests admins have access to all fields
        if user.role.is_superadmin or user.role.is_admin:
            return SpeciesDiagnosisSerializer
        # for all non-admins, all post requests imply that the requester is the owner, so use the owner serializer
        elif self.action == 'create':
            return SpeciesDiagnosisSerializer
        # for all non-admins, requests requiring a primary key can only be performed by the owner or their org
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = EventLocation.objects.filter(id=pk).first()
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization):
                    return SpeciesDiagnosisSerializer
            return SpeciesDiagnosisPublicSerializer
        # non-admins and non-owners (and non-owner orgs) must use the public serializer
        else:
            return SpeciesDiagnosisPublicSerializer


class SpeciesDiagnosisOrganizationViewSet(HistoryViewSet):
    queryset = SpeciesDiagnosisOrganization.objects.all()
    serializer_class = SpeciesDiagnosisOrganizationSerializer

    def destroy(self, request, *args, **kwargs):
        # if the related event is complete, no relates to location species diagnosis organizations can be deleted
        if self.get_object().species_diagnosis.location_species.event_location.event.complete:
            message = "Diagnoses from a species from a location from a complete event may not be changed"
            message += " unless the event is first re-opened by the event owner or an administrator."
            raise APIException(message)
        return super(SpeciesDiagnosisOrganizationViewSet, self).destroy(request, *args, **kwargs)


class DiagnosisBasisViewSet(HistoryViewSet):
    queryset = DiagnosisBasis.objects.all()
    serializer_class = DiagnosisBasisSerializer


class DiagnosisCauseViewSet(HistoryViewSet):
    queryset = DiagnosisCause.objects.all()
    serializer_class = DiagnosisCauseSerializer


######
#
#  Service Requests
#
######


class ServiceRequestViewSet(HistoryViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer


class ServiceRequestTypeViewSet(HistoryViewSet):
    queryset = ServiceRequestType.objects.all()
    serializer_class = ServiceRequestTypeSerializer


class ServiceRequestResponseViewSet(HistoryViewSet):
    queryset = ServiceRequestResponse.objects.all()
    serializer_class = ServiceRequestResponseSerializer


######
#
#  Misc
#
######


class CommentViewSet(HistoryViewSet):
    # queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = Comment.objects.all()
        contains = self.request.query_params.get('contains', None)
        if contains is not None:
            queryset = queryset.filter(comment__contains=contains)
        return queryset


class CommentTypeViewSet(HistoryViewSet):
    queryset = CommentType.objects.all()
    serializer_class = CommentTypeSerializer


class ArtifactViewSet(HistoryViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer


######
#
#  Users
#
######


class UserViewSet(HistoryViewSet):
    serializer_class = UserSerializer

    # anyone can request a new user, but an email address is required if the request comes from a non-user
    @action(detail=False, methods=['post'], parser_classes=(PlainTextParser,))
    def request_new(self, request):
        if not request.user.is_authenticated:
            words = request.data.split(" ")
            email_addresses = [word for word in words if '@' in word]
            if not email_addresses or not re.match(r"[^@]+@[^@]+\.[^@]+", email_addresses[0]):
                msg = "You must submit at least a valid email address to create a new user account."
                raise serializers.ValidationError(msg)
            user_email = email_addresses[0]
        else:
            user_email = request.user.email

        message = "Please add a new user:"
        return construct_email(request.data or '', user_email, message)

    #  override the default serializer_class to ensure the requester sees only permitted data
    # TODO: get_serializer_class(self):

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        user = self.request.user

        # anonymous users cannot see anything
        if not user.is_authenticated:
            return User.objects.none()
        # public and partner users can only see themselves
        elif user.role.is_public or user.role.is_partner or user.role.is_partnermanager:
            return User.objects.filter(pk=user.id)
        # user-specific requests and requests from a partner user can only return data owned by the user or user's org
        elif user.role.is_partneradmin:
            queryset = Contact.objects.all().filter(
                Q(created_by__exact=user) | Q(created_by__organization__exact=user.organization))
        # admins, superadmins, and superusers can see everything
        elif user.role.is_superadmin or user.role.is_admin:
            queryset = User.objects.all()
        # otherwise return nothing
        else:
            return Contact.objects.none()

        # never return the superuser(s)
        # queryset = queryset.exclude(is_superuser=True)
        # filter by username, exact
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(username__exact=username)
        email = self.request.query_params.get('email', None)
        if email is not None:
            queryset = queryset.filter(email__exact=email)
        role = self.request.query_params.get('role', None)
        if role is not None:
            queryset = queryset.filter(role__exact=role)
        organization = self.request.query_params.get('organization', None)
        if email is not None:
            queryset = queryset.filter(organization__exact=organization)
        return queryset

        # # do not allow an anonymous user to see anything at all
        # if not user.is_authenticated:
        #     return User.objects.none()
        # # do not allow a public user to see anything except their own user data
        # if user.role.is_public:
        #     return user
        # else:
        #     # never return the superuser(s)
        #     queryset = User.objects.all().exclude(is_superuser=True)
        #     # filter by username, exact
        #     username = self.request.query_params.get('username', None)
        #     if username is not None:
        #         queryset = queryset.filter(username__exact=username)
        #     email = self.request.query_params.get('email', None)
        #     if email is not None:
        #         queryset = queryset.filter(email__exact=email)
        #     role = self.request.query_params.get('role', None)
        #     if role is not None:
        #         queryset = queryset.filter(role__exact=role)
        #     organization = self.request.query_params.get('organization', None)
        #     if email is not None:
        #         queryset = queryset.filter(organization__exact=organization)
        #     return queryset


class AuthView(views.APIView):
    authentication_classes = (authentication.BasicAuthentication,)
    serializer_class = UserSerializer

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        return Response(self.serializer_class(user).data)


class RoleViewSet(HistoryViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class CircleViewSet(HistoryViewSet):
    queryset = Circle.objects.all()
    serializer_class = CircleSerlializer


class OrganizationViewSet(HistoryViewSet):
    serializer_class_public = OrganizationPublicSerializer
    serializer_class = OrganizationSerializer
    serializer_class_admin = OrganizationAdminSerializer

    @action(detail=False, methods=['post'], parser_classes=(PlainTextParser,))
    def request_new(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        message = "Please add a new organization:"
        return construct_email(request.data, request.user.email, message)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        # all requests from anonymous or public users must use the public serializer
        if not user.is_authenticated or user.role.is_public:
            return self.serializer_class_public
        # admins have access to all fields
        if user.role.is_superadmin or user.role.is_admin:
            return self.serializer_class_admin
        # partner requests only have access to a more limited list of fields
        if user.role.is_partner or user.role.is_partner_manager or user.role.is_partneradmin:
            return self.serializer_class
        # all other requests are rejected
        else:
            raise PermissionDenied
            # message = "You do not have permission to perform this action"
            # return JsonResponse({"Permission Denied": message}, status=403)

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        user = self.request.user
        queryset = Organization.objects.all()

        users = self.request.query_params.get('users', None)
        if users is not None:
            users_list = users.split(',')
            queryset = queryset.filter(users__in=users_list)
        contacts = self.request.query_params.get('contacts', None)
        if contacts is not None:
            contacts_list = contacts.split(',')
            queryset = queryset.filter(contacts__in=contacts_list)
        laboratory = self.request.query_params.get('laboratory', None)
        if laboratory is not None and laboratory in ['True', 'true', 'False', 'false']:
            queryset = queryset.filter(laboratory__exact=laboratory)

        # all requests from anonymous users must only return published data
        if not user.is_authenticated:
            return queryset.filter(do_not_publish=False)
        # for pk requests, unpublished data can only be returned to the owner or their org or admins
        elif self.action in PK_REQUESTS:
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                queryset = Organization.objects.filter(id=pk)
                obj = queryset[0]
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization
                                        or user.role.is_superadmin or user.role.is_admin):
                    return queryset
            return queryset.filter(do_not_publish=False)
        # all list requests, and all requests from public users, must only return published data
        elif self.action == 'list' or user.role.is_public:
            return queryset.filter(do_not_publish=False)
        # that leaves the create request, implying that the requester is the owner
        else:
            return queryset


class ContactViewSet(HistoryViewSet):
    serializer_class = ContactSerializer

    @action(detail=False)
    def user_contacts(self, request):
        # limit data to what the user owns and what the user's org owns
        query_params = self.request.query_params
        queryset = self.build_queryset(query_params, get_user_contacts=True).order_by('id')

        if 'no_page' in self.request.query_params:
            serializer = ContactSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data, status=200)
        else:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ContactSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            serializer = ContactSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data, status=200)

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        query_params = self.request.query_params
        return self.build_queryset(query_params, get_user_contacts=False)

    # build a queryset using query_params
    # NOTE: this is being done in its own method to adhere to the DRY Principle
    def build_queryset(self, query_params, get_user_contacts):
        user = self.request.user

        # anonymous users cannot see anything
        if not user.is_authenticated:
            return Contact.objects.none()
        # public users cannot see anything
        elif user.role.is_public:
            return Contact.objects.none()
        # user-specific requests and requests from a partner user can only return data owned by the user or user's org
        elif get_user_contacts or user.role.is_partner or user.role.is_partnermanager or user.role.is_partneradmin:
            queryset = Contact.objects.all().filter(
                Q(created_by__exact=user) | Q(created_by__organization__exact=user.organization))
        # admins, superadmins, and superusers can see everything
        elif user.role.is_superadmin or user.role.is_admin:
            queryset = Contact.objects.all()
        # otherwise return nothing
        else:
            return Contact.objects.none()

        orgs = query_params.get('org', None)
        if orgs is not None:
            orgs_list = orgs.split(',')
            queryset = queryset.filter(organization__in=orgs_list)
        owner_orgs = query_params.get('ownerorg', None)
        if owner_orgs is not None:
            owner_orgs_list = owner_orgs.split(',')
            queryset = queryset.filter(owner_organization__in=owner_orgs_list)
        return queryset


class ContactTypeViewSet(HistoryViewSet):
    queryset = ContactType.objects.all()
    serializer_class = ContactTypeSerializer


class SearchViewSet(viewsets.ModelViewSet):
    serializer_class = SearchSerializer

    @action(detail=False)
    def user_searches(self, request):
        # limit data to what the user owns and what the user's org owns
        query_params = self.request.query_params
        queryset = self.build_queryset(query_params, get_user_searches=True).order_by('id')

        if 'no_page' in self.request.query_params:
            serializer = SearchSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data, status=200)
        else:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = SearchSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            serializer = SearchSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data, status=200)

    @action(detail=False)
    def top_ten(self, request):
        # return top ten most popular searches
        queryset = Search.objects.all().values('data').annotate(use_count=Sum('count')).order_by('-use_count')[:10]
        serializer = SearchPublicSerializer(queryset, many=True, context={'request': request})

        return Response(serializer.data, status=200)

    # override the default pagination to allow disabling of pagination
    def paginate_queryset(self, *args, **kwargs):
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(*args, **kwargs)

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        query_params = self.request.query_params
        return self.build_queryset(query_params, get_user_searches=False)

    # build a queryset using query_params
    # NOTE: this is being done in its own method to adhere to the DRY Principle
    def build_queryset(self, query_params, get_user_searches):
        user = self.request.user

        # anonymous users cannot see anything
        if not user.is_authenticated:
            return Search.objects.none()
        # user-specific requests and requests from non-admin user can only return data owned by the user
        elif get_user_searches or not (user.role.is_superadmin or user.role.is_admin):
            queryset = Search.objects.all().filter(created_by__exact=user)
        # admins, superadmins, and superusers can see everything
        elif user.role.is_superadmin or user.role.is_admin:
            queryset = Search.objects.all()
        # otherwise return nothing
        else:
            return Search.objects.none()

        owners = query_params.get('owner', None)
        if owners is not None:
            owners_list = owners.split(',')
            queryset = queryset.filter(created_by__in=owners_list)
        return queryset


######
#
#  Special
#
######


class CSVEventSummaryPublicRenderer(csv_renderers.PaginatedCSVRenderer):
    header = ['id', 'type', 'affected', 'start_date', 'end_date', 'states', 'counties',  'species', 'eventdiagnoses']
    labels = {'id': 'Event ID', 'type': 'Event Type', 'affected': 'Number Affected', 'start_date': 'Event Start Date',
              'end_date': 'Event End Date', 'states': 'States (or equivalent)', 'counties': 'Counties (or equivalent)',
              'species': 'Species', 'eventdiagnoses': 'Event Diagnosis'}


class EventSummaryViewSet(ReadOnlyHistoryViewSet):

    @action(detail=False)
    def get_count(self, request):
        query_params = self.request.query_params
        return Response({"count": self.build_queryset(query_params, get_user_events=False).count()})

    @action(detail=False)
    def get_user_events_count(self, request):
        query_params = self.request.query_params
        return Response({"count": self.build_queryset(query_params, get_user_events=True).count()})

    @action(detail=False)
    def user_events(self, request):
        # limit data to what the user owns, what the user's org owns, and what has been shared with the user
        query_params = self.request.query_params
        queryset = self.build_queryset(query_params, get_user_events=True).order_by('id')
        user = self.request.user
        no_page = True if 'no_page' in self.request.query_params else False

        # determine the appropriate serializer to ensure the requester sees only permitted data
        # anonymous user must use the public serializer
        if not user.is_authenticated:
            if no_page:
                serializer = EventSummaryPublicSerializer(queryset, many=True, context={'request': request})
            else:
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = EventSummaryPublicSerializer(page, many=True, context={'request': request})
                    return self.get_paginated_response(serializer.data)
                serializer = EventSummaryPublicSerializer(queryset, many=True, context={'request': request})
        # public users must use the public serializer unless in a circle
        elif user.role.is_public:
            if user in queryset[0].circle_write or user in queryset[0].circle_read:
                if no_page:
                    serializer = EventSummarySerializer(queryset, many=True, context={'request': request})
                else:
                    page = self.paginate_queryset(queryset)
                    if page is not None:
                        serializer = EventSummarySerializer(page, many=True, context={'request': request})
                        return self.get_paginated_response(serializer.data)
                    serializer = EventSummarySerializer(queryset, many=True, context={'request': request})
            else:
                if no_page:
                    serializer = EventSummaryPublicSerializer(queryset, many=True, context={'request': request})
                else:
                    page = self.paginate_queryset(queryset)
                    if page is not None:
                        serializer = EventSummaryPublicSerializer(page, many=True, context={'request': request})
                        return self.get_paginated_response(serializer.data)
                    serializer = EventSummaryPublicSerializer(queryset, many=True, context={'request': request})
        # admins have access to all fields
        elif user.role.is_superadmin or user.role.is_admin:
            if no_page:
                serializer = EventSummaryAdminSerializer(queryset, many=True, context={'request': request})
            else:
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = EventSummaryAdminSerializer(page, many=True, context={'request': request})
                    return self.get_paginated_response(serializer.data)
                serializer = EventSummaryAdminSerializer(queryset, many=True, context={'request': request})
        # partner users can see public fields and event_reference field
        elif (user.role.is_partner or user.role.is_partnermanager or user.role.is_partneradmin or user.role.is_affiliate
              or user in queryset[0].circle_write or user in queryset[0].circle_read):
            if no_page:
                serializer = EventSummarySerializer(queryset, many=True, context={'request': request})
            else:
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = EventSummarySerializer(page, many=True, context={'request': request})
                    return self.get_paginated_response(serializer.data)
                serializer = EventSummarySerializer(queryset, many=True, context={'request': request})
        # non-admins and non-owners (and non-owner orgs) must use the public serializer
        else:
            if no_page:
                serializer = EventSummaryPublicSerializer(queryset, many=True, context={'request': request})
            else:
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = EventSummaryPublicSerializer(page, many=True, context={'request': request})
                    return self.get_paginated_response(serializer.data)
                serializer = EventSummaryPublicSerializer(queryset, many=True, context={'request': request})

        return Response(serializer.data, status=200)

    # override the default renderers to use a csv renderer when requested
    def get_renderers(self):
        frmt = self.request.query_params.get('format', None)
        if frmt is not None and frmt == 'csv':
            renderer_classes = (CSVEventSummaryPublicRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
        else:
            renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES)
        return [renderer_class() for renderer_class in renderer_classes]

    # override the default finalize_response to assign a filename to CSV files
    # see https://github.com/mjumbewu/django-rest-framework-csv/issues/15
    def finalize_response(self, request, *args, **kwargs):
        response = super(viewsets.ReadOnlyModelViewSet, self).finalize_response(request, *args, **kwargs)
        renderer_format = self.request.accepted_renderer.format
        if renderer_format == 'csv':
            fileextension = '.csv'
            filename = 'event_summary_'
            filename += dt.now().strftime("%Y") + '-' + dt.now().strftime("%m") + '-' + dt.now().strftime("%d")
            filename += fileextension
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        frmt = self.request.query_params.get('format', None)
        user = self.request.user

        if frmt is not None and frmt == 'csv':
            return FlatEventSummaryPublicSerializer
        elif not user.is_authenticated:
            return EventSummaryPublicSerializer
        # for all non-admins, primary key requests can only be performed by the owner or their org or shared circles
        elif self.action == 'retrieve':
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = Event.objects.filter(id=pk).first()
                if obj is not None:
                    circle_read = obj.circle_read if obj.circle_read is not None else []
                    circle_write = obj.circle_write if obj.circle_write is not None else []
                    # admins have full access to all fields
                    if user.role.is_superadmin or user.role.is_admin:
                        return EventSummaryAdminSerializer
                    # owner and org members and shared circles have full access to non-admin fields
                    elif user == obj.created_by or (user.organization == obj.created_by.organization and (
                            user.role.is_partnermanager or user.role.is_partneradmin)
                            or user in circle_read or user in circle_write):
                        return EventSummarySerializer
            return EventSummaryPublicSerializer
        # admins have access to all fields
        elif user.role.is_superadmin or user.role.is_admin:
            return EventSummaryAdminSerializer
        # everything else must use the public serializer
        else:
            return EventSummaryPublicSerializer

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        query_params = self.request.query_params
        return self.build_queryset(query_params, get_user_events=False)

    # build a queryset using query_params
    # NOTE: this is being done in its own method to adhere to the DRY Principle
    def build_queryset(self, query_params, get_user_events):
        user = self.request.user

        # first get or create the search and increment its count
        if query_params:
            ordered_query_params = OrderedDict(sorted(query_params.items()))
            ordered_query_params_static = ordered_query_params.copy()
            not_search_params = ['no_page', 'page', 'format']
            [ordered_query_params.popitem(param) for param in ordered_query_params_static if param in not_search_params]
            if len(ordered_query_params) > 0:
                if not user.is_authenticated:
                    admin_user = User.objects.get(pk=1)
                    search = Search.objects.filter(data=ordered_query_params, created_by=admin_user).first()
                else:
                    search = Search.objects.filter(data=ordered_query_params, created_by=user).first()
                if not search:
                    if not user.is_authenticated:
                        admin_user = User.objects.get(pk=1)
                        search = Search.objects.create(data=ordered_query_params, created_by=admin_user)
                    else:
                        search = Search.objects.create(data=ordered_query_params, created_by=user)
                search.count = F('count') + 1
                search.save()

        # then proceed to build the queryset
        queryset = Event.objects.all()

        # anonymous users can only see public data
        if not user.is_authenticated:
            if get_user_events:
                return queryset.none()
            else:
                queryset = queryset.filter(public=True)
        # user-specific event requests can only return data owned by the user or the user's org, or shared with the user
        elif get_user_events:
            queryset = queryset.filter(
                Q(created_by__exact=user) | Q(created_by__organization__exact=user.organization)).distinct()
                #| Q(circle_read__in=user.circles) | Q(circle_write__in=user.circles))
        # admins, superadmins, and superusers can see everything
        elif user.role.is_superadmin or user.role.is_admin:
            queryset = queryset
        # non-user-specific event requests can only return public data
        else:
            queryset = queryset.filter(public=True)

        # check for params that should use the 'and' operator
        and_params = query_params.get('and_params', None)

        # filter by complete, exact
        complete = query_params.get('complete', None)
        if complete is not None and complete in ['True', 'true', 'False', 'false']:
            queryset = queryset.filter(complete__exact=complete)
        # filter by event_type ID, exact list
        event_type = query_params.get('event_type', None)
        if event_type is not None:
            if LIST_DELIMETER in event_type:
                event_type_list = event_type.split(',')
                queryset = queryset.filter(event_type__in=event_type_list)
            else:
                queryset = queryset.filter(event_type__exact=event_type)
        # filter by diagnosis ID, exact list
        diagnosis = query_params.get('diagnosis', None)
        if diagnosis is not None:
            if LIST_DELIMETER in diagnosis:
                diagnosis_list = diagnosis.split(',')
                queryset = queryset.prefetch_related('eventdiagnoses').filter(
                    eventdiagnoses__diagnosis__in=diagnosis_list).distinct()
                if and_params is not None and 'diagnosis' in and_params:
                    # first, count the species for each returned event
                    # and only allow those with the same or greater count as the length of the query_param list
                    queryset = queryset.annotate(count_diagnosies=Count(
                        'eventdiagnoses__diagnosis', distinct=True)).filter(
                        count_diagnoses__gte=len(diagnosis_list))
                    diagnosis_list_ints = [int(i) for i in diagnosis_list]
                    # next, find only the events that have _all_ the requested values, not just any of them
                    for item in queryset:
                        evtdiags = EventDiagnosis.objects.filter(event_id=item.id)
                        all_diagnoses = [evtdiag.diagnosis.id for evtdiag in evtdiags]
                        if not set(diagnosis_list_ints).issubset(set(all_diagnoses)):
                            queryset = queryset.exclude(pk=item.id)
            else:
                queryset = queryset.filter(eventdiagnoses__diagnosis__exact=diagnosis).distinct()
        # filter by diagnosistype ID, exact list
        diagnosis_type = query_params.get('diagnosis_type', None)
        if diagnosis_type is not None:
            if LIST_DELIMETER in diagnosis_type:
                diagnosis_type_list = diagnosis_type.split(',')
                queryset = queryset.prefetch_related('eventdiagnoses__diagnosis__diagnosis_type').filter(
                    eventdiagnoses__diagnosis__diagnosis_type__in=diagnosis_type_list).distinct()
                if and_params is not None and 'diagnosis_type' in and_params:
                    # first, count the species for each returned event
                    # and only allow those with the same or greater count as the length of the query_param list
                    queryset = queryset.annotate(count_diagnosis_types=Count(
                        'eventdiagnoses__diagnosis__diagnosis_type', distinct=True)).filter(
                        count_diagnosis_types__gte=len(diagnosis_type_list))
                    diagnosis_type_list_ints = [int(i) for i in diagnosis_type_list]
                    # next, find only the events that have _all_ the requested values, not just any of them
                    for item in queryset:
                        evtdiags = EventDiagnosis.objects.filter(event_id=item.id)
                        all_diagnosis_types = [evtdiag.diagnosis.diagnosis_type.id for evtdiag in evtdiags]
                        if not set(diagnosis_type_list_ints).issubset(set(all_diagnosis_types)):
                            queryset = queryset.exclude(pk=item.id)
            else:
                queryset = queryset.filter(eventdiagnoses__diagnosis__diagnosis_type__exact=diagnosis_type).distinct()
        # filter by species ID, exact list
        species = query_params.get('species', None)
        if species is not None:
            if LIST_DELIMETER in species:
                species_list = species.split(',')
                queryset = queryset.prefetch_related('eventlocations__locationspecies__species').filter(
                    eventlocations__locationspecies__species__in=species_list).distinct()
                if and_params is not None and 'species' in and_params:
                    # first, count the species for each returned event
                    # and only allow those with the same or greater count as the length of the query_param list
                    queryset = queryset.annotate(count_species=Count(
                        'eventlocations__locationspecies__species')).filter(count_species__gte=len(species_list))
                    species_list_ints = [int(i) for i in species_list]
                    # next, find only the events that have _all_ the requested values, not just any of them
                    for item in queryset:
                        evtlocs = EventLocation.objects.filter(event_id=item.id)
                        locspecs = LocationSpecies.objects.filter(event_location__in=evtlocs)
                        all_species = [locspec.species.id for locspec in locspecs]
                        if not set(species_list_ints).issubset(set(all_species)):
                            queryset = queryset.exclude(pk=item.id)
            else:
                queryset = queryset.filter(eventlocations__locationspecies__species__exact=species).distinct()
        # filter by administrative_level_one, exact list
        administrative_level_one = query_params.get('administrative_level_one', None)
        if administrative_level_one is not None:
            if LIST_DELIMETER in administrative_level_one:
                admin_level_one_list = administrative_level_one.split(',')
                queryset = queryset.prefetch_related('eventlocations__administrative_level_two').filter(
                    eventlocations__administrative_level_one__in=admin_level_one_list).distinct()
                if and_params is not None and 'administrative_level_one' in and_params:
                    # this _should_ be fairly straight forward with the postgresql ArrayAgg function,
                    # (which would offload the hard work to postgresql and make this whole operation faster)
                    # but that function is just throwing an error about a Serial data type,
                    # so the following is a work-around

                    # first, count the eventlocations for each returned event
                    # and only allow those with the same or greater count as the length of the query_param list
                    queryset = queryset.annotate(
                        count_evtlocs=Count('eventlocations')).filter(count_evtlocs__gte=len(admin_level_one_list))
                    admin_level_one_list_ints = [int(i) for i in admin_level_one_list]
                    # next, find only the events that have _all_ the requested values, not just any of them
                    for item in queryset:
                        evtlocs = EventLocation.objects.filter(event_id=item.id)
                        all_a1s = [evtloc.administrative_level_one.id for evtloc in evtlocs]
                        if not set(admin_level_one_list_ints).issubset(set(all_a1s)):
                            queryset = queryset.exclude(pk=item.id)
            else:
                queryset = queryset.filter(
                    eventlocations__administrative_level_one__exact=administrative_level_one).distinct()
        # filter by administrative_level_two, exact list
        administrative_level_two = query_params.get('administrative_level_two', None)
        if administrative_level_two is not None:
            if LIST_DELIMETER in administrative_level_two:
                admin_level_two_list = administrative_level_two.split(',')
                queryset = queryset.prefetch_related('eventlocations__administrative_level_two').filter(
                    eventlocations__administrative_level_two__in=admin_level_two_list).distinct()
                if and_params is not None and 'administrative_level_two' in and_params:
                    # first, count the eventlocations for each returned event
                    # and only allow those with the same or greater count as the length of the query_param list
                    queryset = queryset.annotate(
                        count_evtlocs=Count('eventlocations')).filter(count_evtlocs__gte=len(admin_level_two_list))
                    admin_level_two_list_ints = [int(i) for i in admin_level_two_list]
                    # next, find only the events that have _all_ the requested values, not just any of them
                    for item in queryset:
                        evtlocs = EventLocation.objects.filter(event_id=item.id)
                        all_a2s = [evtloc.administrative_level_two.id for evtloc in evtlocs]
                        if not set(admin_level_two_list_ints).issubset(set(all_a2s)):
                            queryset = queryset.exclude(pk=item.id)
            else:
                queryset = queryset.filter(
                    eventlocations__administrative_level_two__exact=administrative_level_two).distinct()
        # filter by flyway, exact list
        flyway = query_params.get('flyway', None)
        if flyway is not None:
            queryset = queryset.prefetch_related('eventlocations__flyway')
            if LIST_DELIMETER in flyway:
                flyway_list = flyway.split(',')
                queryset = queryset.filter(eventlocations__flyway__in=flyway_list).distinct()
            else:
                queryset = queryset.filter(eventlocations__flyway__exact=flyway).distinct()
        # filter by country, exact list
        country = query_params.get('country', None)
        if country is not None:
            queryset = queryset.prefetch_related('eventlocations__country')
            if LIST_DELIMETER in country:
                country_list = country.split(',')
                queryset = queryset.filter(eventlocations__country__in=country_list).distinct()
            else:
                queryset = queryset.filter(eventlocations__country__exact=country).distinct()
        # filter by gnis_id, exact list
        gnis_id = query_params.get('gnis_id', None)
        if gnis_id is not None:
            queryset = queryset.prefetch_related('eventlocations__gnis_id')
            if LIST_DELIMETER in gnis_id:
                gnis_id_list = country.split(',')
                queryset = queryset.filter(eventlocations__gnis_id__in=gnis_id_list).distinct()
            else:
                queryset = queryset.filter(eventlocations__gnis_id__exact=gnis_id).distinct()
        # filter by affected, (greater than or equal to only, less than or equal to only,
        # or between both, depending on which URL params appear)
        affected_count__gte = query_params.get('affected_count__gte', None)
        affected_count__lte = query_params.get('affected_count__lte', None)
        if affected_count__gte is not None and affected_count__lte is not None:
            queryset = queryset.filter(affected_count__gte=affected_count__gte, affected_count__lte=affected_count__lte)
        elif affected_count__gte is not None:
            queryset = queryset.filter(affected_count__gte=affected_count__gte)
        elif affected_count__lte is not None:
            queryset = queryset.filter(affected_count__lte=affected_count__lte)
        # filter by start and end date (after only, before only, or between both, depending on which URL params appear)
        # the date filters below are date-exclusive
        start_date = query_params.get('start_date', None)
        end_date = query_params.get('end_date', None)
        if start_date is not None and end_date is not None:
            queryset = queryset.filter(start_date__gt=start_date, end_date__lt=end_date)
        elif start_date is not None:
            queryset = queryset.filter(start_date__gt=start_date)
        elif end_date is not None:
            queryset = queryset.filter(end_date__lt=end_date)
        # TODO: determine the intended use of the following three query params
        # because only admins or fellow org or circle members should even be able to filter on these values
        # perhaps these should instead be used implicitly based on the requester
        # (query will auto-filter based on the requester's ID/org/circle properties)
        # rather than something a requester explicitly queries?
        # # filter by owner ID, exact
        # owner = query_params.get('owner', None)
        # if owner is not None:
        #     queryset = queryset.filter(created_by__exact=owner)
        # # filter by ownerorg ID, exact
        # owner_org = query_params.get('owner_org', None)
        # if owner_org is not None:
        #     queryset = queryset.prefetch_related('created_by__organization')
        #     queryset = queryset.filter(created_by__organization__exact=owner_org)
        # # filter by circle ID, exact
        # TODO: this might need to be changed to select only events where the user is in a circle attached to this event
        # rather than the current set up where any circle ID can be used
        # circle = query_params.get('circle', None)
        # if circle is not None:
        #     queryset = queryset.filter(Q(circle_read__exact=circle) | Q(circle_write__exact=circle))
        return queryset


class CSVEventDetailRenderer(csv_renderers.CSVRenderer):
    header = ['event_id', 'event_reference', 'event_type', 'complete', 'organization', 'start_date', 'end_date',
              'affected_count', 'event_diagnosis', 'location_id', 'location_priority', 'county', 'state', 'nation',
              'location_start', 'location_end', 'location_species_id', 'species_priority', 'species_name', 'population',
              'sick', 'dead', 'estimated_sick', 'estimated_dead', 'captive', 'age_bias', 'sex_bias',
              'species_diagnosis_id', 'species_diagnosis_priority', 'speciesdx', 'causal', 'suspect', 'number_tested',
              'number_positive', 'lab']
    labels = {'event_id': 'Event ID', 'event_reference': 'User Event Reference', 'event_type': 'Event Type',
              'complete': 'WHISPers Record Status', 'organization': 'Organization', 'start_date': 'Event Start Date',
              'end_date': 'Event End Date', 'affected_count': 'Number Affected', 'event_diagnosis': 'Event Diagnosis',
              'location_id': 'Location ID', 'location_priority': 'Location Priority',
              'county': 'County (or equivalent)', 'state': 'State (or equivalent)', 'nation': 'Nation',
              'location_start': 'Location Start Date', 'location_end': 'Location End Date',
              'location_species_id': 'Location Species ID', 'species_priority': 'Species Priority',
              'species_name': 'Species', 'population': 'Population', 'sick': 'Known Sick', 'dead': 'Known Dead',
              'estimated_sick': 'Estimated Sick', 'estimated_dead': 'Estimated Dead', 'captive': 'Captive',
              'age_bias': 'Age Bias', 'sex_bias': 'Sex Bias', 'species_diagnosis_id': 'Species Diagnosis ID',
              'species_diagnosis_priority': 'Species Diagnosis Priority', 'speciesdx': 'Species Diagnosis',
              'causal': 'Significance of Diagnosis for Species', 'suspect': 'Species Diagnosis Suspect',
              'number_tested': 'Number Assessed', 'number_positive': 'Number Confirmed', 'lab': 'Lab'}


class EventDetailViewSet(ReadOnlyHistoryViewSet):
    permission_classes = (DRYPermissions,)
    # queryset = Event.objects.all()

    @action(detail=True)
    def flat(self, request, pk):
        # pk = self.request.parser_context['kwargs'].get('pk', None)
        queryset = FlatEventDetails.objects.filter(event_id=pk)
        serializer = FlatEventDetailSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=200)

    # override the default renderers to use a csv renderer when requested
    def get_renderers(self):
        frmt = self.request.query_params.get('format', None)
        if frmt is not None and frmt == 'csv':
            renderer_classes = (CSVEventDetailRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
        else:
            renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES)
        return [renderer_class() for renderer_class in renderer_classes]

    # override the default finalize_response to assign a filename to CSV files
    # see https://github.com/mjumbewu/django-rest-framework-csv/issues/15
    def finalize_response(self, request, *args, **kwargs):
        response = super(viewsets.ReadOnlyModelViewSet, self).finalize_response(request, *args, **kwargs)
        renderer_format = self.request.accepted_renderer.format
        if renderer_format == 'csv':
            fileextension = '.csv'
            filename = 'event_details_'
            filename += dt.now().strftime("%Y") + '-' + dt.now().strftime("%m") + '-' + dt.now().strftime("%d")
            filename += fileextension
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    # override the default queryset to allow filtering by URL arguments
    def get_queryset(self):
        user = self.request.user
        queryset = Event.objects.all()

        if not user.is_authenticated:
            return queryset.filter(public=True)

        # for pk requests, non-public data can only be returned to the owner or their org or shared circles or admins
        elif self.action == 'retrieve':
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                queryset = Event.objects.filter(id=pk)
                obj = queryset[0]
                circle_read = obj.circle_read if obj.circle_read is not None else []
                circle_write = obj.circle_write if obj.circle_write is not None else []
                if obj is not None and (user == obj.created_by or user.organization == obj.created_by.organization
                                        or user in circle_read or user in circle_write
                                        or user.role.is_superadmin or user.role.is_admin):
                    return queryset
            return queryset.filter(public=True)
        # all list requests must only return public data
        else:
            return queryset.filter(public=True)

    # override the default serializer_class to ensure the requester sees only permitted data
    def get_serializer_class(self):
        user = self.request.user
        if not user.is_authenticated:
            return EventDetailPublicSerializer
        # for all non-admins, primary key requests can only be performed by the owner or their org or shared circles
        elif self.action == 'retrieve':
            pk = self.request.parser_context['kwargs'].get('pk', None)
            if pk is not None:
                obj = Event.objects.filter(id=pk).first()
                if obj is not None:
                    circle_read = obj.circle_read if obj.circle_read is not None else []
                    circle_write = obj.circle_write if obj.circle_write is not None else []
                    # admins have full access to all fields
                    if user.role.is_superadmin or user.role.is_admin:
                        return EventDetailAdminSerializer
                    # owner and org members and shared circles have full access to non-admin fields
                    elif user == obj.created_by or (user.organization == obj.created_by.organization and (
                            user.role.is_partnermanager or user.role.is_partneradmin)
                            or user in circle_read or user in circle_write):
                        return EventDetailSerializer
            return EventDetailPublicSerializer
        # admins have access to all fields
        elif user.role.is_superadmin or user.role.is_admin:
            return EventDetailAdminSerializer
        # everything else must use the public serializer
        else:
            return EventDetailPublicSerializer
