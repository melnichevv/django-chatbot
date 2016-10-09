import json

import requests
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from channels.utils import disable_middleware
from chatbot.settings import FB_APP_SECRET, FB_ACCESS_TOKEN


class FacebookHandler(View):

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(FacebookHandler, self).dispatch(*args, **kwargs)

    @staticmethod
    def find_channel_with_address(channel_address, channels):
        new_channel = None
        for channel in channels:
            if channel_address == channel.address:
                new_channel = channel
                break

        return new_channel

    def get(self, request, *args, **kwargs):
        # this is a verification of a webhook
        if request.GET.get('hub.mode') == 'subscribe':
            # verify the token against our secret, if the same return the challenge FB sent us
            if FB_APP_SECRET == request.GET.get('hub.verify_token'):
                # fire off a subscription for facebook events, we have a bit of a delay here so that FB can react to this webhook result
                # subscribe to messaging events for this channel
                response = requests.post('https://graph.facebook.com/v2.6/me/subscribed_apps',
                                         params=dict(access_token=FB_ACCESS_TOKEN))

                if response.status_code != 200 or not response.json()['success']:
                    print "Unable to subscribe for delivery of events: %s" % response.content

                return HttpResponse(request.GET.get('hub.challenge'))

        return JsonResponse(dict(error="Unknown request"), status=400)

    def post(self, request, *args, **kwargs):
        return FacebookHandler.parse_post_data(request)

    @staticmethod
    def parse_post_data(request):
        request_body = request.body
        # parse our response
        try:
            body = json.loads(request_body)
        except Exception as e:
            return HttpResponse("Invalid JSON in POST body: %s" % str(e), status=400)

        if 'entry' not in body:
            return HttpResponse("Missing entry array", status=400)
        print body
        return HttpResponse("Msg ignored. %s" % request_body)
        # iterate through our entries, handling them
        for entry in body.get('entry'):
            # this is an incoming message
            if 'messaging' in entry:
                msgs = []

                # Test against the original channel by default
                other_channels = []
                channel_address = str(entry.get('id', ''))
                if not channel_address:
                    continue

                for envelope in entry['messaging']:
                    if 'message' in envelope:
                        if 'is_echo' in envelope['message'] and envelope['message']['is_echo']:
                            continue

                        channel_address = str(envelope['recipient']['id'])
                        if channel_address != channel.address:
                            other_channels = other_channels or FacebookHandler.lookup_org_channels(channel)
                            channel = FacebookHandler.find_channel_with_address(channel_address, other_channels)

                            if not channel:
                                return HttpResponse("Msg does not match channel recipient id: %s" % channel_address,
                                                    status=400)

                        text = None
                        media = None
                        if 'quick_reply' in envelope['message'] and 'payload' in envelope['message']['quick_reply']:
                            text = envelope['message']['quick_reply']['payload']
                        elif 'text' in envelope['message']:
                            text = envelope['message']['text']
                        elif 'attachments' in envelope['message']:
                            text = ''
                            for attachment in envelope['message']['attachments']:
                                if 'type' in attachment:
                                    if 'payload' in attachment:
                                        payload = attachment['payload']
                                    if attachment['type'] == 'location':
                                        if payload and 'coordinates' in payload:
                                            coordinates = payload['coordinates']
                                            latitude = coordinates['lat']
                                            longitude = coordinates['long']
                                            if latitude and longitude:
                                                media = Msg.make_media_url(Msg.MEDIA_GPS,
                                                                           '%s,%s' % (latitude, longitude))
                                    elif attachment['type'] == 'image':
                                        if payload and 'url' in payload:
                                            media = FacebookHandler.download_file(channel, payload['url'],
                                                                                  Msg.MEDIA_IMAGE)
                                    elif attachment['type'] == 'audio':
                                        if payload and 'url' in payload:
                                            media = FacebookHandler.download_file(channel, payload['url'],
                                                                                  Msg.MEDIA_AUDIO)
                                    elif attachment['type'] == 'video':
                                        if payload and 'url' in payload:
                                            media = FacebookHandler.download_file(channel, payload['url'],
                                                                                  Msg.MEDIA_VIDEO)

                        # if we have some content or media, create the msg
                        if text or (text == '' and media):
                            # does this contact already exist?
                            sender_id = envelope['sender']['id']
                            contact = Contact.from_urn(channel.org, FACEBOOK_SCHEME, sender_id)

                            # if not, let's go create it
                            if not contact:
                                contact = FacebookHandler.create_contact(channel, sender_id)

                            msg_date = datetime.fromtimestamp(envelope['timestamp'] / 1000.0).replace(tzinfo=pytz.utc)
                            msg = Msg.create_incoming(channel, (FACEBOOK_SCHEME, sender_id),
                                                      text, media=media, date=msg_date, contact=contact,
                                                      external_id=envelope['message']['mid'])
                            msgs.append(msg)

                    elif 'delivery' in envelope and 'mids' in envelope['delivery']:
                        for external_id in envelope['delivery']['mids']:
                            msg = Msg.all_messages.filter(channel=channel, direction=OUTGOING,
                                                          external_id=external_id).first()
                            if msg:
                                msg.status_delivered()
                                msgs.append(msg)

                    elif 'postback' in envelope:
                        channel_address = str(envelope['recipient']['id'])
                        if channel_address != channel.address:
                            # Test if there are any other Facebook page in this organization, and support multi-page
                            other_channels = other_channels or FacebookHandler.lookup_org_channels(channel)
                            channel = FacebookHandler.find_channel_with_address(channel_address, other_channels)

                            if not channel:
                                return HttpResponse("Msg does not match channel recipient id: %s" % channel_address,
                                                    status=400)

                        content = None
                        if 'payload' in envelope['postback']:
                            content = envelope['postback']['payload']

                        # if we have some content, create the msg
                        if content:
                            # does this contact already exist?
                            sender_id = envelope['sender']['id']
                            contact = Contact.from_urn(channel.org, FACEBOOK_SCHEME, sender_id)

                            # if not, let's go create it
                            if not contact:
                                contact = FacebookHandler.create_contact(channel, sender_id)

                            msg_date = datetime.fromtimestamp(envelope['timestamp'] / 1000.0).replace(tzinfo=pytz.utc)
                            msg = Msg.create_incoming(channel, (FACEBOOK_SCHEME, sender_id),
                                                      content, date=msg_date, contact=contact)
                            msgs.append(msg)
                    elif 'account_linking' in envelope:
                        status = envelope['account_linking']['status']
                        sender_id = envelope['sender']['id']
                        contact = Contact.from_urn(channel.org, FACEBOOK_SCHEME, sender_id)

                        # if not, let's go create it
                        if not contact:
                            contact = FacebookHandler.create_contact(channel, sender_id)

                        from temba.msgs.metadata import FacebookMetadata
                        facebook_metadata = FacebookMetadata()
                        payload = {
                            'fb_account_status': status
                        }
                        if status == 'linked':
                            authorization_code = envelope['account_linking']['authorization_code']
                            try:
                                encoded = urllib.unquote(authorization_code)
                                authorization_code = json.loads(encoded)
                            except Exception as e:
                                logger.warning(
                                    "Error parsing authorization_code from Facebook: {}".format(authorization_code))

                            payload['fb_account_authorization_code'] = authorization_code

                        facebook_metadata.set_account_linking_payload(json.dumps(payload))
                        metadata = facebook_metadata.as_string()

                        msg = Msg.create_incoming(channel, (FACEBOOK_SCHEME, sender_id),
                                                  '', contact=contact, metadata=metadata)
                        msgs.append(msg)

                return HttpResponse("Msgs Updated: %s" % (",".join([str(m.id) for m in msgs])))
        return HttpResponse("Msg ignored. %s" % request_body)

    @staticmethod
    def create_contact(channel, sender_id):
        name = None
        additional_info = {}

        # if this isn't an anonymous org, look up their name from the Facebook API
        if not channel.org.is_anon:
            try:
                response = requests.get('https://graph.facebook.com/v2.6/' + unicode(sender_id),
                                        params=dict(fields='first_name,last_name,gender,locale',
                                                    access_token=channel.config_json()[AUTH_TOKEN]))

                if response.status_code == 200:
                    user_stats = response.json()
                    name = ' '.join([user_stats.get('first_name', ''), user_stats.get('last_name', '')])
                    locale = user_stats.get('locale', None)
                    gender = user_stats.get('gender', None)

                    if locale:
                        try:
                            language, country = locale.split('_')
                            language = find_iso_code_3_language(language)
                        except Exception as e:
                            logger.error("Error parsing locale from Facebook: %s" % locale, exc_info=True)
                            language = country = None

                        if language is not None:
                            additional_info['locale_language'] = language
                        if country is not None:
                            additional_info['locale_country'] = country
                    if gender:
                        additional_info['gender'] = gender

            except Exception as e:
                # something went wrong trying to look up the user's attributes, oh well, move on
                import traceback
                traceback.print_exc()

        contact = Contact.get_or_create(channel.org, channel.created_by, incoming_channel=channel,
                                        name=name, urns=[(FACEBOOK_SCHEME, sender_id)])
        for key, value in additional_info.iteritems():
            label = regex.sub(r'([^A-Za-z0-9\- ]+)', ' ', key, regex.V0).title()
            contact_field = ContactField.get_or_create(channel.org, channel.created_by, key,
                                                       label=label,
                                                       show_in_table=None,
                                                       value_type=Value.TYPE_TEXT)
            contact.set_field(channel.created_by, key, value)
        return contact