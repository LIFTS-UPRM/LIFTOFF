CREATE TABLE public.messages (
  id         BIGSERIAL   PRIMARY KEY,
  session_id TEXT        NOT NULL,
  user_id    UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  mission_id TEXT        NOT NULL REFERENCES public.missions(id) ON DELETE CASCADE,
  role       TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
  content    TEXT        NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.messages IS 'Per-session conversation history, written by the backend service role.';

CREATE INDEX idx_messages_session ON public.messages (session_id, created_at);
CREATE INDEX idx_messages_user    ON public.messages (user_id);

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Users read their own messages; backend (service role) handles all writes
CREATE POLICY "messages_select_own" ON public.messages
  FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

-- Allow authenticated users to query via Data API
GRANT SELECT ON public.messages TO authenticated;
