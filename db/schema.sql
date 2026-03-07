\restrict dbmate

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: timescaledb; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS timescaledb WITH SCHEMA public;


--
-- Name: EXTENSION timescaledb; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION timescaledb IS 'Enables scalable inserts and complex queries for time-series data (Community Edition)';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_trade_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_trade_logs (
    symbol character varying(50),
    action character varying(20),
    verdict character varying(20),
    confidence double precision,
    size double precision,
    reasoning text,
    "timestamp" timestamp with time zone
);


--
-- Name: geopolitical_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.geopolitical_logs (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    event_date timestamp with time zone,
    source_url text,
    source_domain text,
    title text,
    cameo_code character varying(10),
    cameo_category character varying(50),
    goldstein_scale double precision,
    avg_tone double precision,
    num_sources integer,
    num_articles integer,
    actor1_country character varying(5),
    actor2_country character varying(5),
    action_geo character varying(5),
    risk_score double precision,
    risk_level character varying(10),
    themes jsonb,
    payload jsonb
);


--
-- Name: geopolitical_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.geopolitical_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: geopolitical_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.geopolitical_logs_id_seq OWNED BY public.geopolitical_logs.id;


--
-- Name: macro_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macro_logs (
    "timestamp" timestamp with time zone,
    fg_index double precision,
    yield_10y double precision
);


--
-- Name: playbook_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.playbook_logs (
    id bigint NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    log_type character varying(50) NOT NULL,
    regime character varying(20),
    payload jsonb NOT NULL
);


--
-- Name: playbook_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.playbook_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: playbook_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.playbook_logs_id_seq OWNED BY public.playbook_logs.id;


--
-- Name: portfolio_summary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolio_summary (
    symbol character varying(50),
    entry_price double precision,
    current_price double precision,
    market_value double precision,
    is_cash boolean,
    "timestamp" timestamp with time zone
);


--
-- Name: raw_market_ticks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.raw_market_ticks (
    id integer NOT NULL,
    symbol character varying(20) NOT NULL,
    price double precision NOT NULL,
    volume double precision,
    "timestamp" timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: raw_market_ticks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.raw_market_ticks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: raw_market_ticks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.raw_market_ticks_id_seq OWNED BY public.raw_market_ticks.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying NOT NULL
);


--
-- Name: sentiment_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sentiment_logs (
    "timestamp" timestamp with time zone,
    symbol character varying(50),
    sentiment_score double precision,
    source character varying(50)
);


--
-- Name: trade_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trade_history (
    "timestamp" timestamp with time zone,
    symbol character varying(50),
    action character varying(20),
    price double precision,
    reason text,
    rsi double precision,
    strategy character varying(100)
);


--
-- Name: v_correlation_metrics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_correlation_metrics AS
 WITH price_series AS (
         SELECT date_trunc('hour'::text, trade_history."timestamp") AS hour,
            trade_history.symbol,
            avg(trade_history.price) AS avg_price
           FROM public.trade_history
          WHERE (trade_history.price IS NOT NULL)
          GROUP BY (date_trunc('hour'::text, trade_history."timestamp")), trade_history.symbol
        ), pairs AS (
         SELECT DISTINCT a.symbol AS sym_a,
            b.symbol AS sym_b
           FROM (price_series a
             CROSS JOIN price_series b)
          WHERE ((a.symbol)::text < (b.symbol)::text)
        ), corr_calc AS (
         SELECT (((p.sym_a)::text || '/'::text) || (p.sym_b)::text) AS pair,
            corr(a.avg_price, b.avg_price) AS coefficient,
            count(*) AS data_points
           FROM ((pairs p
             JOIN price_series a ON (((a.symbol)::text = (p.sym_a)::text)))
             JOIN price_series b ON ((((b.symbol)::text = (p.sym_b)::text) AND (b.hour = a.hour))))
          GROUP BY (((p.sym_a)::text || '/'::text) || (p.sym_b)::text)
         HAVING (count(*) >= 5)
        )
 SELECT pair,
    round((coefficient)::numeric, 4) AS coefficient,
    data_points
   FROM corr_calc;


--
-- Name: geopolitical_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.geopolitical_logs ALTER COLUMN id SET DEFAULT nextval('public.geopolitical_logs_id_seq'::regclass);


--
-- Name: playbook_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playbook_logs ALTER COLUMN id SET DEFAULT nextval('public.playbook_logs_id_seq'::regclass);


--
-- Name: raw_market_ticks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_market_ticks ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: geopolitical_logs geopolitical_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.geopolitical_logs
    ADD CONSTRAINT geopolitical_logs_pkey PRIMARY KEY (id);


--
-- Name: playbook_logs playbook_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.playbook_logs
    ADD CONSTRAINT playbook_logs_pkey PRIMARY KEY (id);


--
-- Name: raw_market_ticks raw_market_ticks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_market_ticks
    ADD CONSTRAINT raw_market_ticks_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: idx_geo_logs_cameo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_geo_logs_cameo ON public.geopolitical_logs USING btree (cameo_code);


--
-- Name: idx_geo_logs_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_geo_logs_created ON public.geopolitical_logs USING btree (created_at DESC);


--
-- Name: idx_geo_logs_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_geo_logs_risk ON public.geopolitical_logs USING btree (risk_score DESC);


--
-- PostgreSQL database dump complete
--

\unrestrict dbmate


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20260307000000'),
    ('20260307000001');
