-- Extensions
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Helper: auto-update updated_at on any table
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- ─────────────────────────────────────────────
-- Core tables
-- ─────────────────────────────────────────────

CREATE TABLE public.profiles (
  id            UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name  TEXT        NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.profiles IS 'One row per authenticated user, auto-created on signup.';

CREATE TABLE public.missions (
  id          TEXT        PRIMARY KEY,
  title       TEXT        NOT NULL,
  status      TEXT        NOT NULL DEFAULT 'upcoming'
                CHECK (status IN ('upcoming', 'in-progress', 'completed')),
  description TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.missions IS 'LIFTS mission definitions (e.g. AERO, SCRAM).';

CREATE TABLE public.mission_members (
  mission_id  TEXT        NOT NULL REFERENCES public.missions(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  role        TEXT        NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'lead')),
  joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (mission_id, user_id)
);
COMMENT ON TABLE public.mission_members IS 'Which users belong to which missions and in what role.';

CREATE TABLE public.user_sessions (
  id              TEXT        PRIMARY KEY,
  user_id         UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  mission_id      TEXT        NOT NULL REFERENCES public.missions(id) ON DELETE CASCADE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_active_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.user_sessions IS 'Hermes runtime sessions, one per user per mission conversation.';

-- ─────────────────────────────────────────────
-- Telemetry / audit tables
-- ─────────────────────────────────────────────

CREATE TABLE public.chat_usage_logs (
  id                   BIGSERIAL   PRIMARY KEY,
  user_id              UUID        REFERENCES public.profiles(id) ON DELETE SET NULL,
  mission_id           TEXT        REFERENCES public.missions(id) ON DELETE SET NULL,
  session_id           TEXT,
  usage_source         TEXT        NOT NULL,
  model                TEXT,
  llm_steps            INTEGER,
  message_chars        INTEGER,
  response_chars       INTEGER,
  tool_call_count      INTEGER,
  selected_tool_groups TEXT[],
  elapsed_seconds      NUMERIC(10,3),
  recorded_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.chat_usage_logs IS 'Per-request LLM usage telemetry written by the backend service role.';

CREATE TABLE public.mission_write_events (
  id           BIGSERIAL   PRIMARY KEY,
  user_id      UUID        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  mission_id   TEXT        NOT NULL REFERENCES public.missions(id) ON DELETE CASCADE,
  session_id   TEXT,
  operation    TEXT        NOT NULL,
  target_file  TEXT        NOT NULL,
  summary      TEXT,
  applied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE public.mission_write_events IS 'Audit trail for constrained shared mission doc writes.';

-- ─────────────────────────────────────────────
-- Vector / RAG table (future use)
-- ─────────────────────────────────────────────

CREATE TABLE public.mission_doc_embeddings (
  id           BIGSERIAL   PRIMARY KEY,
  mission_id   TEXT        NOT NULL REFERENCES public.missions(id) ON DELETE CASCADE,
  file_path    TEXT        NOT NULL,
  chunk_index  INTEGER     NOT NULL DEFAULT 0,
  content      TEXT        NOT NULL,
  embedding    extensions.vector(1536),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (mission_id, file_path, chunk_index)
);
COMMENT ON TABLE public.mission_doc_embeddings IS 'Chunked mission doc embeddings for RAG retrieval (1536-dim OpenAI text-embedding-3-small).';

-- ─────────────────────────────────────────────
-- Indexes
-- ─────────────────────────────────────────────

CREATE INDEX idx_mission_members_user         ON public.mission_members (user_id);
CREATE INDEX idx_user_sessions_user           ON public.user_sessions (user_id);
CREATE INDEX idx_user_sessions_mission        ON public.user_sessions (mission_id);
CREATE INDEX idx_chat_usage_logs_user         ON public.chat_usage_logs (user_id);
CREATE INDEX idx_chat_usage_logs_mission      ON public.chat_usage_logs (mission_id);
CREATE INDEX idx_chat_usage_logs_recorded_at  ON public.chat_usage_logs (recorded_at DESC);
CREATE INDEX idx_mission_write_events_mission ON public.mission_write_events (mission_id);
CREATE INDEX idx_mission_write_events_user    ON public.mission_write_events (user_id);
CREATE INDEX idx_mission_doc_embeddings_file  ON public.mission_doc_embeddings (mission_id, file_path);

-- ─────────────────────────────────────────────
-- updated_at triggers
-- ─────────────────────────────────────────────

CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_missions_updated_at
  BEFORE UPDATE ON public.missions
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_mission_doc_embeddings_updated_at
  BEFORE UPDATE ON public.mission_doc_embeddings
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ─────────────────────────────────────────────
-- Auth trigger: auto-create profile on signup
-- ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name)
  VALUES (
    NEW.id,
    COALESCE(
      NEW.raw_user_meta_data->>'display_name',
      split_part(NEW.email, '@', 1)
    )
  );
  RETURN NEW;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ─────────────────────────────────────────────
-- Row Level Security
-- ─────────────────────────────────────────────

ALTER TABLE public.profiles               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.missions               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mission_members        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_usage_logs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mission_write_events   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mission_doc_embeddings ENABLE ROW LEVEL SECURITY;

-- profiles
CREATE POLICY "profiles_select_own" ON public.profiles
  FOR SELECT TO authenticated
  USING ((SELECT auth.uid()) = id);

CREATE POLICY "profiles_update_own" ON public.profiles
  FOR UPDATE TO authenticated
  USING ((SELECT auth.uid()) = id)
  WITH CHECK ((SELECT auth.uid()) = id);

-- missions: visible to members only
CREATE POLICY "missions_select_member" ON public.missions
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.mission_members mm
      WHERE mm.mission_id = missions.id
        AND mm.user_id = (SELECT auth.uid())
    )
  );

-- mission_members
CREATE POLICY "mission_members_select_own" ON public.mission_members
  FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

-- user_sessions
CREATE POLICY "user_sessions_select_own" ON public.user_sessions
  FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

CREATE POLICY "user_sessions_insert_own" ON public.user_sessions
  FOR INSERT TO authenticated
  WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "user_sessions_update_own" ON public.user_sessions
  FOR UPDATE TO authenticated
  USING (user_id = (SELECT auth.uid()))
  WITH CHECK (user_id = (SELECT auth.uid()));

-- chat_usage_logs: service role writes, users read their own
CREATE POLICY "chat_usage_logs_select_own" ON public.chat_usage_logs
  FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

-- mission_write_events: mission members read
CREATE POLICY "mission_write_events_select_member" ON public.mission_write_events
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.mission_members mm
      WHERE mm.mission_id = mission_write_events.mission_id
        AND mm.user_id = (SELECT auth.uid())
    )
  );

-- mission_doc_embeddings: mission members read
CREATE POLICY "mission_doc_embeddings_select_member" ON public.mission_doc_embeddings
  FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM public.mission_members mm
      WHERE mm.mission_id = mission_doc_embeddings.mission_id
        AND mm.user_id = (SELECT auth.uid())
    )
  );

-- ─────────────────────────────────────────────
-- Storage: private mission workspace bucket
-- ─────────────────────────────────────────────

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'mission-workspace',
  'mission-workspace',
  false,
  52428800,
  ARRAY['text/markdown', 'text/plain', 'application/json']
);

-- Authenticated mission members can read their mission files
-- Path convention inside the bucket: missions/{mission_id}/...
CREATE POLICY "mission_workspace_select_member" ON storage.objects
  FOR SELECT TO authenticated
  USING (
    bucket_id = 'mission-workspace'
    AND EXISTS (
      SELECT 1 FROM public.mission_members mm
      WHERE mm.mission_id = split_part(name, '/', 2)
        AND mm.user_id = (SELECT auth.uid())
    )
  );

-- ─────────────────────────────────────────────
-- Seed data: existing missions
-- ─────────────────────────────────────────────

INSERT INTO public.missions (id, title, status) VALUES
  ('m1', 'ASCENT Sub-Scale', 'in-progress'),
  ('m2', 'ASCENT',           'upcoming'),
  ('m3', 'Nexo',             'completed');
