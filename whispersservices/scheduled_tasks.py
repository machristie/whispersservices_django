from celery import shared_task
from django.db.models import Count
from whispersservices.serializers import *
from whispersservices.models import *
from whispersservices.immediate_tasks import generate_notification


@shared_task()
def all_events(events_created_yesterday, events_updated_yesterday):
    notifications = []
    msg_tmp = NotificationMessageTemplate.objects.filter(name='ALL Events').first()

    standard_notification_cues_new = NotificationCueStandard.objects.filter(
        standard_type__name='All', notification_cue_preference__create_when_new=True)
    for event in events_created_yesterday:
        for cue in standard_notification_cues_new:
            send_email = cue.notification_cue_preference.send_email
            recipients = [cue.created_by.id, ]
            email_to = [cue.created_by.email, ] if send_email else []

            eventlocations = EventLocation.objects.filter(event=event.id)
            short_evt_locs = ""
            for evtloc in eventlocations:
                short_evt_loc = ""
                if evtloc.administrative_level_two:
                    short_evt_loc += evtloc.administrative_level_two.name
                short_evt_loc += ", " + evtloc.administrative_level_one.abbreviation
                short_evt_loc += ", " + evtloc.country.abbreviation
                short_evt_locs = short_evt_loc if len(short_evt_locs) == 0 else short_evt_locs + "; " + short_evt_loc
            subject = msg_tmp.subject_template.format(event_id=event.id)
            body = msg_tmp.body_template.format(
                event_id=event.id, organization=event.created_by.organization.name, event_location=short_evt_locs,
                event_date=event.created_date, new_updated="New", created_updated="created", updates="N/A")
            source = event.created_by.username
            notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
            # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    standard_notification_cues_updated = NotificationCueStandard.objects.filter(
        standard_type__name='All', notification_cue_preference__create_when_modified=True)
    for event in events_updated_yesterday:
        for cue in standard_notification_cues_updated:
            send_email = cue.notification_cue_preference.send_email
            recipients = [cue.created_by.id, ]
            email_to = [cue.created_by.email, ] if send_email else []

            eventlocations = EventLocation.objects.filter(event=event.id)
            short_evt_locs = ""
            for evtloc in eventlocations:
                short_evt_loc = ""
                if evtloc.administrative_level_two:
                    short_evt_loc += evtloc.administrative_level_two.name
                short_evt_loc += ", " + evtloc.administrative_level_one.abbreviation
                short_evt_loc += ", " + evtloc.country.abbreviation
                short_evt_locs = short_evt_loc if len(short_evt_locs) == 0 else short_evt_locs + "; " + short_evt_loc
            updates = ""
            subject = msg_tmp.subject_template.format(event_id=event.id)
            body = msg_tmp.body_template.format(
                event_id=event.id, organization=event.modified_by.organization.name, event_location=short_evt_locs,
                event_date=event.modified_date, new_updated="Updated", created_updated="updated", updates=updates)
            source = event.modified_by.username
            notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
            # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    return notifications


@shared_task()
def own_events(events_created_yesterday, events_updated_yesterday):
    notifications = []
    msg_tmp = NotificationMessageTemplate.objects.filter(name='Your Events').first()

    standard_notification_cues_new = NotificationCueStandard.objects.filter(
        standard_type__name='Own', notification_cue_preference__create_when_new=True)
    for event in events_created_yesterday:
        for cue in standard_notification_cues_new:
            if cue.created_by.id == event.created_by.id:
                send_email = cue.notification_cue_preference.send_email
                recipients = [cue.created_by.id, ]
                email_to = [cue.created_by.email, ] if send_email else []

                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    first_name=event.created_by.first_name, last_name=event.created_by.last_name,
                    created_updated="created", event_id=event.id, event_date=event.created_date, updates="N/A",
                    new_updated="New")
                source = event.created_by.username
                notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
                # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    standard_notification_cues_updated = NotificationCueStandard.objects.filter(
        standard_type__name='Own', notification_cue_preference__create_when_modified=True)
    for event in events_updated_yesterday:
        for cue in standard_notification_cues_updated:
            if cue.created_by.id == event.created_by.id:
                send_email = cue.notification_cue_preference.send_email
                recipients = [cue.created_by.id, ]
                email_to = [cue.created_by.email, ] if send_email else []

                updates = ""
                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    first_name=event.modified_by.first_name, last_name=event.modified_by.last_name,
                    created_updated="updated", event_id=event.id, event_date=event.modified_date, updates=updates,
                    new_updated="Updated")
                source = event.modified_by.username
                notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
                # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    return notifications


@shared_task()
def organization_events(events_created_yesterday, events_updated_yesterday):
    notifications = []
    msg_tmp = NotificationMessageTemplate.objects.filter(name='Organization Events').first()

    standard_notification_cues_new = NotificationCueStandard.objects.filter(
        standard_type__name='Organization', notification_cue_preference__create_when_new=True)
    for event in events_created_yesterday:
        for cue in standard_notification_cues_new:
            if (cue.created_by.organization.id == event.created_by.organization.id
                    or cue.created_by.organization.id in event.created_by.organization.parent_organizations):
                send_email = cue.notification_cue_preference.send_email
                recipients = [cue.created_by.id, ]
                email_to = [cue.created_by.email, ] if send_email else []

                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    first_name=event.created_by.first_name, last_name=event.created_by.last_name,
                    created_updated="created", event_id=event.id, event_date=event.created_date, updates="N/A",
                    new_updated="New")
                source = event.created_by.username
                notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
                # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    standard_notification_cues_updated = NotificationCueStandard.objects.filter(
        standard_type__name='Organization', notification_cue_preference__create_when_modified=True)
    for event in events_updated_yesterday:
        for cue in standard_notification_cues_updated:
            if (cue.created_by.organization.id == event.created_by.organization.id
                    or cue.created_by.organization.id in event.created_by.organization.parent_organizations):
                send_email = cue.notification_cue_preference.send_email
                recipients = [cue.created_by.id, ]
                email_to = [cue.created_by.email, ] if send_email else []

                updates = ""
                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    first_name=event.modified_by.first_name, last_name=event.modified_by.last_name,
                    created_updated="updated", event_id=event.id, event_date=event.modified_date, updates=updates,
                    new_updated="Updated")
                source = event.modified_by.username
                notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
                # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    return notifications


@shared_task()
def collaborator_events(events_created_yesterday, events_updated_yesterday):
    notifications = []
    msg_tmp = NotificationMessageTemplate.objects.filter(name='Collaborator Events').first()

    standard_notification_cues_new = NotificationCueStandard.objects.filter(
        standard_type__name='Collaborator', notification_cue_preference__create_when_new=True)
    for event in events_created_yesterday:
        event_collaborator_ids = set(list(User.objects.filter(
            Q(eventwriteusers__event_id=event.id) |
            Q(eventreadusers__event_id=event.id)
        ).values_list('id', flat=True)))
        for cue in standard_notification_cues_new:
            if cue.created_by.id in event_collaborator_ids:
                send_email = cue.notification_cue_preference.send_email
                recipients = [cue.created_by.id, ]
                email_to = [cue.created_by.email, ] if send_email else []

                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    first_name=event.created_by.first_name, last_name=event.created_by.last_name,
                    created_updated="created", event_id=event.id, event_date=event.created_date, updates="N/A",
                    new_updated="New")
                source = event.created_by.username
                notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
                # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    standard_notification_cues_updated = NotificationCueStandard.objects.filter(
        standard_type__name='Collaborator', notification_cue_preference__create_when_modified=True)
    for event in events_updated_yesterday:
        event_collaborator_ids = set(list(User.objects.filter(
            Q(eventwriteusers__event_id=event.id) |
            Q(eventreadusers__event_id=event.id)
        ).values_list('id', flat=True)))
        for cue in standard_notification_cues_updated:
            if cue.created_by.id in event_collaborator_ids:
                send_email = cue.notification_cue_preference.send_email
                recipients = [cue.created_by.id, ]
                email_to = [cue.created_by.email, ] if send_email else []

                updates = ""
                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    first_name=event.modified_by.first_name, last_name=event.modified_by.last_name,
                    created_updated="updated", event_id=event.id, event_date=event.modified_date, updates=updates,
                    new_updated="Updated")
                source = event.modified_by.username
                notifications.append((recipients, source, event.id, 'event', subject, body, send_email, email_to))
                # generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    return notifications


@shared_task()
def standard_notifications():
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
    new_events = Event.objects.filter(created_date=yesterday)
    updated_events = Event.objects.filter(modified_date=yesterday).exclude(created_date=yesterday)

    own_evts = own_events(events_created_yesterday=new_events, events_updated_yesterday=updated_events)
    org_evts = organization_events(events_created_yesterday=new_events, events_updated_yesterday=updated_events)
    collab_evts = collaborator_events(events_created_yesterday=new_events, events_updated_yesterday=updated_events)
    all_evts = all_events(events_created_yesterday=new_events, events_updated_yesterday=updated_events)

    all_notifications = own_evts + org_evts + collab_evts + all_evts
    unique_notifications = []

    for notification in all_notifications:
        if (notification[0], notification[2]) not in unique_notifications:
            unique_notifications.append((notification[0], notification[2]))
            generate_notification.delay(*notification)

    return True


@shared_task()
def stale_events():
    stale_event_periods = Configuration.objects.filter(name='stale_event_periods').first()
    if stale_event_periods:
        stale_event_periods_list = stale_event_periods.value.split(',')
        if all(x.strip().isdigit() for x in stale_event_periods_list):
            stale_event_periods_list_ints = [int(x) for x in stale_event_periods_list]
            msg_tmp = NotificationMessageTemplate.objects.filter(name='Stale Events').first()
            for period in stale_event_periods_list_ints:
                period_date = datetime.strftime(datetime.now() - timedelta(period), '%Y-%m-%d')
                all_stale_events = Event.objects.filter(complete=False, created_date=period_date)
                for event in all_stale_events:
                    recipients = list(User.objects.filter(name='nwhc-epi').values_list('id', flat=True))
                    recipients += [event.created_by.id, ]
                    email_to = list(User.objects.filter(name='nwhc-epi').values_list('email', flat=True))
                    email_to += [event.created_by.email, ]

                    eventlocations = EventLocation.objects.filter(event=event.id)
                    short_evt_locs = ""
                    for evtloc in eventlocations:
                        short_evt_loc = ""
                        if evtloc.administrative_level_two:
                            short_evt_loc += evtloc.administrative_level_two.name
                        short_evt_loc += ", " + evtloc.administrative_level_one.abbreviation
                        short_evt_loc += ", " + evtloc.country.abbreviation
                        short_evt_locs = short_evt_loc if len(
                            short_evt_locs) == 0 else short_evt_locs + "; " + short_evt_loc
                    subject = msg_tmp.subject_template.format(event_id=event.id)
                    body = msg_tmp.body_template.format(
                        event_id=event.id, event_location=short_evt_locs, event_date=event.created_date,
                        stale_period=str(period))
                    source = 'system'
                    generate_notification.delay(recipients, source, event.id, 'event', subject, body, True, email_to)
    return True


def build_custom_notifications_query(cue, base_queryset):
    queryset = None
    criteria = []

    # event
    if cue.event:
        criteria.append(('Event', str(cue.event)))
        if not queryset:
            queryset = base_queryset
        queryset = queryset.filter(id=cue.event)

    # event_affected_count
    if cue.event_affected_count:
        operator = cue.event_affected_count_operator.upper()

        # criteria
        value = str(cue.event_affected_count)

        # queryset
        if not queryset:
            queryset = base_queryset
        if operator == "LTE":
            queryset = queryset.filter(affected_count__lte=value)
            criteria.append(('Affected Count', '<= ' + value))
        else:
            # default to GTE
            queryset = queryset.filter(affected_count__gte=value)
            criteria.append(('Affected Count', '>= ' + value))

    # event_location_land_ownership
    if cue.event_location_land_ownership:
        values = cue.event_location_land_ownership['values']
        if len(values) > 0:
            operator = cue.event_location_land_ownership['operator'].upper()

            # criteria
            names_list = list(LandOwnership.objects.filter(id__in=values).values_list('name', flat=True))
            if len(values) == 1:
                names = names_list[0]
            else:
                names = (' ' + operator + ' ').join(names_list)
            criteria.append(('Land Ownership', names))

            # queryset
            if not queryset:
                queryset = base_queryset
            if operator == "OR":
                queries = [Q(eventlocations__land_ownership=value) for value in values]
                query = queries.pop()
                for item in queries:
                    query |= item
                queryset = queryset.filter(query)
            else:
                # default to AND
                # figure out how to query if an event has a child with one of each
                for value in values:
                    queryset = queryset.filter(eventlocations__land_ownership=value)

    # event_location_administrative_level_one
    if cue.event_location_administrative_level_one:
        values = cue.event_location_administrative_level_one['values']
        if len(values) > 0:
            operator = cue.event_location_administrative_level_one['operator'].upper()

            # criteria
            # use locality name when possible
            ctry_ids = list(Country.objects.filter(
                administrativelevelones__in=values).values_list('id', flat=True))
            field_name = 'Administrative Level One'
            if ctry_ids:
                lcl = AdministrativeLevelLocality.objects.filter(country=ctry_ids[0]).first()
                if lcl and lcl.admin_level_one_name is not None:
                    field_name = lcl.admin_level_one_name

            names_list = list(AdministrativeLevelOne.objects.filter(id__in=values).values_list('name', flat=True))
            if len(values) == 1:
                names = names_list[0]
            else:
                names = (' ' + operator + ' ').join(names_list)
            criteria.append((field_name, names))

            # queryset
            if not queryset:
                queryset = base_queryset
            queryset = queryset.prefetch_related('eventlocations__administrative_level_two').filter(
                eventlocations__administrative_level_one__in=values).distinct()
            if operator == 'AND':
                # this _should_ be fairly straight forward with the postgresql ArrayAgg function,
                # (which would offload the hard work to postgresql and make this whole operation faster)
                # but that function is just throwing an error about a Serial data type,
                # so the following is a work-around

                # first, count the eventlocations for each returned event
                # and only allow those with the same or greater count as the length of the query_param list
                queryset = queryset.annotate(
                    count_evtlocs=Count('eventlocations')).filter(count_evtlocs__gte=len(values))
                admin_level_one_list_ints = [int(i) for i in values]
                # next, find only the events that have _all_ the requested values, not just any of them
                for item in queryset:
                    evtlocs = EventLocation.objects.filter(event_id=item.id)
                    all_a1s = [evtloc.administrative_level_one.id for evtloc in evtlocs]
                    if not set(admin_level_one_list_ints).issubset(set(all_a1s)):
                        queryset = queryset.exclude(pk=item.id)

    # species
    if cue.species:
        values = cue.species['values']
        if len(values) > 0:
            operator = cue.species['operator'].upper()

            # criteria
            names_list = list(Species.objects.filter(id__in=values).values_list('name', flat=True))
            if len(values) == 1:
                names = names_list[0]
            else:
                names = (' ' + operator + ' ').join(names_list)
            criteria.append(('Species', names))

            # queryset
            if not queryset:
                queryset = base_queryset
            queryset = queryset.prefetch_related('eventlocations__locationspecies__species').filter(
                eventlocations__locationspecies__species__in=values).distinct()
            if operator == "AND":
                # first, count the species for each returned event
                # and only allow those with the same or greater count as the length of the query_param list
                queryset = queryset.annotate(count_species=Count(
                    'eventlocations__locationspecies__species')).filter(count_species__gte=len(values))
                species_list_ints = [int(i) for i in values]
                # next, find only the events that have _all_ the requested values, not just any of them
                for item in queryset:
                    evtlocs = EventLocation.objects.filter(event_id=item.id)
                    locspecs = LocationSpecies.objects.filter(event_location__in=evtlocs)
                    all_species = [locspec.species.id for locspec in locspecs]
                    if not set(species_list_ints).issubset(set(all_species)):
                        queryset = queryset.exclude(pk=item.id)

    # species_diagnosis_diagnosis
    if cue.species_diagnosis_diagnosis:
        values = cue.species_diagnosis_diagnosis['values']
        if len(values) > 0:
            operator = cue.species_diagnosis_diagnosis['operator'].upper()

            # criteria
            names_list = list(Diagnosis.objects.filter(id__in=values).values_list('name', flat=True))
            if len(values) == 1:
                names = names_list[0]
            else:
                names = (' ' + operator + ' ').join(names_list)
            criteria.append(('Diagnosis', names))

            # queryset
            if not queryset:
                queryset = base_queryset
            queryset = queryset.prefetch_related('eventlocations__locationspecies__speciesdiagnoses__diagnosis').filter(
                eventlocations__locationspecies__speciesdiagnoses__diagnosis__in=values).distinct()
            if operator == "AND":
                # first, count the species for each returned event
                # and only allow those with the same or greater count as the length of the query_param list
                queryset = queryset.annotate(count_diagnoses=Count(
                    'eventlocations__locationspecies__speciesdiagnoses__diagnosis', distinct=True)).filter(
                    count_diagnoses__gte=len(values))
                diagnosis_list_ints = [int(i) for i in values]
                # next, find only the events that have _all_ the requested values, not just any of them
                for item in queryset:
                    evtdiags = EventDiagnosis.objects.filter(event_id=item.id)
                    all_diagnoses = [evtdiag.diagnosis.id for evtdiag in evtdiags]
                    if not set(diagnosis_list_ints).issubset(set(all_diagnoses)):
                        queryset = queryset.exclude(pk=item.id)

    criteria_string = ''
    for criterion in criteria:
        criteria_string += criterion[0] + ": " + criterion[1] + "<br />"

    return queryset, criteria_string


@shared_task()
def custom_notifications():
    # An event with a number affected greater than or equal to the provided integer is created,
    # OR an event location is added/updated that meets that criteria
    msg_tmp = NotificationMessageTemplate.objects.filter(name='Custom Notification').first()
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

    custom_notification_cues_new = NotificationCueCustom.objects.filter(
        notification_cue_preference__create_when_new=True)
    base_queryset = Event.objects.filter(created_date=yesterday)
    for cue in custom_notification_cues_new:
        queryset, criteria = build_custom_notifications_query(cue, base_queryset)

        if queryset:
            for event in queryset:
                send_email = cue.notification_cue_preference.send_email
                # recipients: users with this notification configured
                recipients = [cue.created_by.id, ]
                # email forwarding: Optional, set by user.
                email_to = [cue.created_by.email, ] if send_email else []

                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    new_updated="New", criteria=criteria, organization=event.created_by.organization.name,
                    created_updated="created", event_id=event.id, event_date=event.created_date, updates="N/A")
                # source: any user who creates or updates an event that meets the trigger criteria
                source = event.created_by.username
                generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    custom_notification_cues_updated = NotificationCueCustom.objects.filter(
        notification_cue_preference__create_when_modified=True)
    base_queryset = Event.objects.filter(modified_date=yesterday).exclude(created_date=yesterday)
    for cue in custom_notification_cues_updated:
        queryset, criteria = build_custom_notifications_query(cue, base_queryset)

        if queryset:
            for event in queryset:
                send_email = cue.notification_cue_preference.send_email
                # recipients: users with this notification configured
                recipients = [cue.created_by.id, ]
                # email forwarding: Optional, set by user.
                email_to = [cue.created_by.email, ] if send_email else []

                # TODO: implement population of updates text
                updates = ""

                subject = msg_tmp.subject_template.format(event_id=event.id)
                body = msg_tmp.body_template.format(
                    new_updated="Updated", criteria=criteria, organization=event.modified_by.organization.name,
                    created_updated="updated", event_id=event.id, event_date=event.modified_date, updates=updates)
                # source: any user who creates or updates an event that meets the trigger criteria
                source = event.modified_by.username
                generate_notification.delay(recipients, source, event.id, 'event', subject, body, send_email, email_to)

    return True
