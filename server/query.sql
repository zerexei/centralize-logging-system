CREATE TABLE public.logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    service TEXT NOT NULL,
    environment TEXT NOT NULL,
    level TEXT NOT NULL,
    log_message TEXT NOT NULL,

    trace_id TEXT,

    metadata JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- indexes
CREATE INDEX idx_logs_service
ON public.logs(service);

CREATE INDEX idx_logs_environment
ON public.logs(environment);

CREATE INDEX idx_logs_level
ON public.logs(level);

-- CREATE INDEX idx_logs_trace_id
-- ON public.logs(trace_id);

-- CREATE INDEX idx_logs_created_at
-- ON public.logs(created_at DESC);

-- -- JSONB index for metadata searches
-- CREATE INDEX idx_logs_metadata
-- ON public.logs
-- USING GIN(metadata);