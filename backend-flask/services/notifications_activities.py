# from datetime import datetime, timedelta, timezone
# class NotificationsActivities:
#   def run():
#     now = datetime.now(timezone.utc).astimezone()
#     results = [{

#       'uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
#       # 'uuid': 'c4f513be-7bb4-428e-ae87-31926e851fcf',
#       'handle':  'andrewbrown',
#       'message': 'I am white unicorn',
#       'created_at': (now - timedelta(days=2)).isoformat(),
#       'expires_at': (now + timedelta(days=5)).isoformat(),
#       'likes_count': 5,
#       'replies_count': 1,
#       'reposts_count': 0,
#       'replies': [{
#         'uuid': '26e12864-1c26-5c3a-9658-97a10f8fea67',
#         'reply_to_activity_uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
#         # 'reply_to_activity_uuid': 'c4f513be-7bb4-428e-ae87-31926e851fcf',
#         'handle':  'Worf',
#         'message': 'This post has no honor!',
#         'likes_count': 0,
#         'replies_count': 0,
#         'reposts_count': 0,
#         'created_at': (now - timedelta(days=2)).isoformat()
#       }],
#     },
#     ]
#     return results

from datetime import datetime, timedelta, timezone

class NotificationsActivities:
    def run(self):
        now = datetime.now(timezone.utc).astimezone()
        results = [{
            'uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
            'handle': 'andrewbrown',
            'message': 'I am a white unicorn',
            'created_at': (now - timedelta(days=2)).isoformat(),
            'expires_at': (now + timedelta(days=5)).isoformat(),
            'likes_count': 5,
            'replies_count': 1,
            'reposts_count': 0,
            'replies': [{
                'uuid': '26e12864-1c26-5c3a-9658-97a10f8fea67',
                'reply_to_activity_uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
                'handle': 'Worf',
                'message': 'This post has no honor!',
                'likes_count': 0,
                'replies_count': 0,
                'reposts_count': 0,
                'created_at': (now - timedelta(days=2)).isoformat()
            }],
        }]
        return results

# Create an instance of NotificationsActivities
notifications_instance = NotificationsActivities()

# Call the run method on the instance
data = notifications_instance.run()
