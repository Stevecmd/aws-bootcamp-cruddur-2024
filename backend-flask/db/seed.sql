-- this file was manually created
INSERT INTO public.users (display_name, email, handle, cognito_user_id)
VALUES
  ('Andrew Brown', 'andrewbrown@exampro' ,'andrew','68f126b0-1ceb-4a33-88be-d90fa7109eee'),
  ('Andrew Bayko', 'bayko@exampro' ,'bayko','68f126b0-1ceb-4a33-88be-d90fa7109eee'),
  ('Londo Mollari','lmollari@centari.com' ,'londo','MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'andrew' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )