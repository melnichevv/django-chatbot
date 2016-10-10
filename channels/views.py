import json

import pytz
import requests
from datetime import datetime
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from chatbot.settings import FB_APP_SECRET, FB_ACCESS_TOKEN
from .exceptions import SendException


LAST_MESSAGE = None


class Flow(object):
    msg = {
        'text': '',
        'media': None,
        'metadata': None
    }

    @staticmethod
    def send_hello(contact):
        msg = dict(Flow.msg)
        msg['text'] = 'Hello from chat bot!'
        return FacebookHandler.send_message(msg, contact)

    @staticmethod
    def send_sorry(contact):
        msg = dict(Flow.msg)
        msg['text'] = "Sorry. I didn't get it :("
        return FacebookHandler.send_message(msg, contact)

    @staticmethod
    def send_image(contact):
        msg = dict(Flow.msg)
        msg['media'] = {
            'media_type': 'image',
            'media_url': 'https://lh6.ggpht.com/edSOTD7QaRqgc-BwMiJhkuTPOVKu-hBQlOSbGyQYXscAJvxupYPP4AZuA_qbFbr27A=w300'
        }
        return FacebookHandler.send_message(msg, contact)

    @staticmethod
    def send_wait_msg(contact):
        msg = dict(Flow.msg)
        msg['text'] = 'Uploading a video for you. Hang on :)'
        return FacebookHandler.send_message(msg, contact)

    @staticmethod
    def send_video(contact):
        # Flow.send_wait_msg(contact)
        msg = dict(Flow.msg)
        # msg['media'] = {
        #     'media_type': 'video',
        #     'media_url': 'http://www.sample-videos.com/video/mp4/720/big_buck_bunny_720p_5mb.mp4'
        # }
        # return FacebookHandler.send_message(msg, contact)

    @staticmethod
    def send_quick_replies(contact):
        msg = dict(Flow.msg)
        quick_replies = [
          {
            "content_type": "text",
            "title": "Red",
            "payload": "DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED"
          },
          {
            "content_type": "text",
            "title": "Green",
            "payload": "DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GREEN"
          }
        ]
        msg['metadata'] = {
            'quick_replies': quick_replies,
            'text': 'Wanna something cool? (:'
        }
        return FacebookHandler.send_message(msg, contact)


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

        # iterate through our entries, handling them
        for entry in body.get('entry'):
            # this is an incoming message
            if 'messaging' in entry:
                for envelope in entry['messaging']:
                    if 'message' in envelope:
                        if 'is_echo' in envelope['message'] and envelope['message']['is_echo']:
                            continue

                        text = None
                        if 'quick_reply' in envelope['message'] and 'payload' in envelope['message']['quick_reply']:
                            text = envelope['message']['quick_reply']['payload']
                        elif 'text' in envelope['message']:
                            text = envelope['message']['text']
                        elif 'attachments' in envelope['message']:
                            text = ''

                        # if we have some content or media, create the msg
                        if text:
                            # does this contact already exist?
                            sender_id = envelope['sender']['id']
                            contact = FacebookHandler.get_contact(sender_id)
                            msg_date = envelope['timestamp']

                            # Ignore incoming messages if there were multiple requests from Facebook for the same msg
                            if not LAST_MESSAGE:
                                global LAST_MESSAGE
                                LAST_MESSAGE = {
                                    'date': msg_date,
                                    'text': text
                                }
                                FacebookHandler.process_message(text, contact)
                            else:
                                if text != LAST_MESSAGE['text']:
                                    FacebookHandler.process_message(text, contact)
                                else:
                                    diff = msg_date - LAST_MESSAGE['date']
                                    if diff > 1000:
                                        FacebookHandler.process_message(text, contact)
                                    else:
                                        print('Ignoring incoming message')
                                global LAST_MESSAGE
                                LAST_MESSAGE = {
                                    'date': msg_date,
                                    'text': text
                                }

                return HttpResponse("Msgs handled")
        return HttpResponse("Msg ignored. %s" % request_body)

    @staticmethod
    def get_contact(sender_id):
        name = None
        gender = None

        # if this isn't an anonymous org, look up their name from the Facebook API
        try:
            response = requests.get('https://graph.facebook.com/v2.6/' + unicode(sender_id),
                                    params=dict(fields='first_name,last_name,gender',
                                                access_token=FB_ACCESS_TOKEN))

            if response.status_code == 200:
                user_stats = response.json()
                name = ' '.join([user_stats.get('first_name', ''), user_stats.get('last_name', '')])
                gender = user_stats.get('gender', None)

        except Exception as e:
            # something went wrong trying to look up the user's attributes, oh well, move on
            import traceback
            traceback.print_exc()
        return {
            'name': name,
            'gender': gender,
            'id': sender_id
        }

    @staticmethod
    def process_message(text, contact):
        text = text.lower()
        if text == 'hello':
            return Flow.send_hello(contact)
        elif 'image' in text:
            return Flow.send_image(contact)
        elif 'video' in text:
            return Flow.send_video(contact)
        elif 'quick replies' in text:
            return Flow.send_quick_replies(contact)
        return Flow.send_sorry(contact)

    @classmethod
    def send_message(cls, msg, contact):
        url = "https://graph.facebook.com/v2.6/me/messages"
        params = dict(access_token=FB_ACCESS_TOKEN)
        headers = {'Content-Type': 'application/json'}

        payload = dict()
        payload['recipient'] = dict(id=contact['id'])
        text = msg['text']

        # build our payload
        if msg['media']:
            try:
                media_type = msg['media']['media_type']
                media_url = msg['media']['media_url']
                if media_type == 'image':
                    attachment = dict(type='image', payload=dict(url=media_url))
                    payload['message'] = dict(attachment=attachment)

                elif media_type == 'video':
                    attachment = dict(type='video', payload=dict(url=media_url))
                    payload['message'] = dict(attachment=attachment)

                elif media_type == 'audio':
                    attachment = dict(type='audio', payload=dict(url=media_url))
                    payload['message'] = dict(attachment=attachment)

                elif media_type == 'file':
                    attachment = dict(type='file', payload=dict(url=media_url))
                    payload['message'] = dict(attachment=attachment)

            except Exception as e:
                raise SendException("Error sending a Media! %s" % e.message,
                                    method='POST',
                                    url='facebook',
                                    request=msg.media,
                                    response=str(contact),
                                    response_status=501,
                                    fatal=True)

        elif msg['metadata']:
            try:
                metadata_text = msg['metadata'].get('text', None)
                quick_replies = msg['metadata'].get('quick_replies', None)
                attachment = msg['metadata'].get('attachment', None)
                link = msg['metadata'].get('link', None)

                if (metadata_text or attachment) and quick_replies:
                    message = dict()
                    if metadata_text:
                        message['text'] = metadata_text
                    else:
                        message['attachment'] = attachment
                    message['quick_replies'] = quick_replies
                    payload['message'] = message

                elif link:
                    payload['message'] = dict(text=link)

                elif attachment:
                    payload['message'] = dict(attachment=attachment)

                else:
                    payload['message'] = dict(text=text)

            except Exception as e:
                import traceback
                traceback.print_exc(e)
                raise SendException("Error in your Facebook template! %s" % e.message,
                                    method='POST',
                                    url='facebook',
                                    request=msg.metadata,
                                    response=str(contact),
                                    response_status=501,
                                    fatal=True)
        else:
            payload['message'] = dict(text=text)

        payload = json.dumps(payload)
        print(payload)
        try:
            response = requests.post(url, payload, params=params, headers=headers, timeout=60)
        except Exception as e:
            raise SendException(e.message,
                                method='POST',
                                url=url,
                                request=payload,
                                response=str(dict(dict(error=e.message), **contact)),
                                response_status=503,
                                fatal=True)

        if response.status_code != 200:
            try:
                code = response.json()['error']['code']
                error = response.json()['error']['message']
                # if code == 200 or code == 551:
                #     contact = Contact.objects.get(pk=msg.contact)
                #     contact.fail(permanently=False)
            except (IndexError, KeyError):
                error = "Got non-200 response [%d] from Facebook" % response.status_code
                # something went wrong during error parsing process
                pass
            try:
                error_dict = response.text
                error_dict.pop('message')
            except Exception:
                error_dict = dict(error=response.text)
            raise SendException(error,
                                method='POST',
                                url=url,
                                request=payload,
                                response=str(dict(error_dict, **contact)),
                                response_status=response.status_code,
                                fatal=True)
