\restrict dbmate

-- Dumped from database version 16.11
-- Dumped by pg_dump version 18.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: _compressed_hypertable_7; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._compressed_hypertable_7 (
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
-- Name: _direct_view_6; Type: VIEW; Schema: _timescaledb_internal; Owner: -
--

CREATE VIEW _timescaledb_internal._direct_view_6 AS
 SELECT public.time_bucket('00:01:00'::interval, "timestamp") AS bucket,
    symbol,
    public.first(price, "timestamp") AS open,
    max(price) AS high,
    min(price) AS low,
    public.last(price, "timestamp") AS close,
    sum(volume) AS volume,
    count(*) AS tick_count
   FROM public.raw_market_ticks
  GROUP BY (public.time_bucket('00:01:00'::interval, "timestamp")), symbol;


--
-- Name: intel_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intel_embeddings (
    id bigint NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    source_type character varying(50) NOT NULL,
    source_id character varying(255),
    source_channel character varying(100),
    content text NOT NULL,
    embedding public.vector(384) NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    tickers character varying(20)[] DEFAULT '{}'::character varying[],
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: _hyper_4_100_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_100_chunk (
    CONSTRAINT constraint_100 CHECK ((("timestamp" >= '2016-10-20 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-10-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_101_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_101_chunk (
    CONSTRAINT constraint_101 CHECK ((("timestamp" >= '2016-02-04 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-02-11 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_102_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_102_chunk (
    CONSTRAINT constraint_102 CHECK ((("timestamp" >= '2016-09-15 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-09-22 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_103_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_103_chunk (
    CONSTRAINT constraint_103 CHECK ((("timestamp" >= '2018-10-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2018-10-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_104_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_104_chunk (
    CONSTRAINT constraint_104 CHECK ((("timestamp" >= '2024-08-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-09-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_105_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_105_chunk (
    CONSTRAINT constraint_105 CHECK ((("timestamp" >= '2024-08-01 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-08-08 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_106_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_106_chunk (
    CONSTRAINT constraint_106 CHECK ((("timestamp" >= '2013-02-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-02-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_107_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_107_chunk (
    CONSTRAINT constraint_107 CHECK ((("timestamp" >= '2013-01-10 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-01-17 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_108_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_108_chunk (
    CONSTRAINT constraint_108 CHECK ((("timestamp" >= '2012-12-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-01-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_109_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_109_chunk (
    CONSTRAINT constraint_109 CHECK ((("timestamp" >= '2012-12-13 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-12-20 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_10_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_10_chunk (
    CONSTRAINT constraint_10 CHECK ((("timestamp" >= '2025-12-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-01-01 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_110_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_110_chunk (
    CONSTRAINT constraint_110 CHECK ((("timestamp" >= '2013-02-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-03-07 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_111_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_111_chunk (
    CONSTRAINT constraint_111 CHECK ((("timestamp" >= '2013-02-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-02-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_112_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_112_chunk (
    CONSTRAINT constraint_112 CHECK ((("timestamp" >= '2013-01-03 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-01-10 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_113_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_113_chunk (
    CONSTRAINT constraint_113 CHECK ((("timestamp" >= '2012-12-20 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-12-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_114_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_114_chunk (
    CONSTRAINT constraint_114 CHECK ((("timestamp" >= '2012-11-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-12-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_115_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_115_chunk (
    CONSTRAINT constraint_115 CHECK ((("timestamp" >= '2013-01-31 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-02-07 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_116_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_116_chunk (
    CONSTRAINT constraint_116 CHECK ((("timestamp" >= '2013-01-24 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-01-31 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_117_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_117_chunk (
    CONSTRAINT constraint_117 CHECK ((("timestamp" >= '2013-01-17 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2013-01-24 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_118_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_118_chunk (
    CONSTRAINT constraint_118 CHECK ((("timestamp" >= '2012-12-06 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-12-13 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_119_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_119_chunk (
    CONSTRAINT constraint_119 CHECK ((("timestamp" >= '2012-11-22 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-11-29 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_11_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_11_chunk (
    CONSTRAINT constraint_11 CHECK ((("timestamp" >= '2025-12-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-12-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_120_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_120_chunk (
    CONSTRAINT constraint_120 CHECK ((("timestamp" >= '2012-11-15 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-11-22 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_121_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_121_chunk (
    CONSTRAINT constraint_121 CHECK ((("timestamp" >= '2012-11-01 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2012-11-08 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_122_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_122_chunk (
    CONSTRAINT constraint_122 CHECK ((("timestamp" >= '2025-04-03 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-04-10 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_123_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_123_chunk (
    CONSTRAINT constraint_123 CHECK ((("timestamp" >= '2025-02-13 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-02-20 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_124_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_124_chunk (
    CONSTRAINT constraint_124 CHECK ((("timestamp" >= '2023-12-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2023-12-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_125_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_125_chunk (
    CONSTRAINT constraint_125 CHECK ((("timestamp" >= '2025-06-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-07-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_126_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_126_chunk (
    CONSTRAINT constraint_126 CHECK ((("timestamp" >= '2023-12-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2023-12-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_127_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_127_chunk (
    CONSTRAINT constraint_127 CHECK ((("timestamp" >= '2024-02-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-03-07 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_128_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_128_chunk (
    CONSTRAINT constraint_128 CHECK ((("timestamp" >= '2025-02-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-03-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_129_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_129_chunk (
    CONSTRAINT constraint_129 CHECK ((("timestamp" >= '2025-10-16 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-10-23 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_12_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_12_chunk (
    CONSTRAINT constraint_12 CHECK ((("timestamp" >= '2025-12-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-12-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_130_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_130_chunk (
    CONSTRAINT constraint_130 CHECK ((("timestamp" >= '2024-01-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-01-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_131_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_131_chunk (
    CONSTRAINT constraint_131 CHECK ((("timestamp" >= '2024-11-21 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-11-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_132_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_132_chunk (
    CONSTRAINT constraint_132 CHECK ((("timestamp" >= '2023-12-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-01-04 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_133_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_133_chunk (
    CONSTRAINT constraint_133 CHECK ((("timestamp" >= '2024-03-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-03-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_134_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_134_chunk (
    CONSTRAINT constraint_134 CHECK ((("timestamp" >= '2024-01-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-01-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_135_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_135_chunk (
    CONSTRAINT constraint_135 CHECK ((("timestamp" >= '2025-03-13 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-03-20 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_136_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_136_chunk (
    CONSTRAINT constraint_136 CHECK ((("timestamp" >= '2024-03-21 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-03-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_137_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_137_chunk (
    CONSTRAINT constraint_137 CHECK ((("timestamp" >= '2024-01-04 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-01-11 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_138_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_138_chunk (
    CONSTRAINT constraint_138 CHECK ((("timestamp" >= '2024-11-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-12-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_139_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_139_chunk (
    CONSTRAINT constraint_139 CHECK ((("timestamp" >= '2024-04-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-04-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_13_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_13_chunk (
    CONSTRAINT constraint_13 CHECK ((("timestamp" >= '2026-01-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_140_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_140_chunk (
    CONSTRAINT constraint_140 CHECK ((("timestamp" >= '2024-05-30 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-06-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_141_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_141_chunk (
    CONSTRAINT constraint_141 CHECK ((("timestamp" >= '2024-01-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-02-01 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_142_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_142_chunk (
    CONSTRAINT constraint_142 CHECK ((("timestamp" >= '2023-12-21 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2023-12-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_143_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_143_chunk (
    CONSTRAINT constraint_143 CHECK ((("timestamp" >= '2025-03-20 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-03-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_144_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_144_chunk (
    CONSTRAINT constraint_144 CHECK ((("timestamp" >= '2024-05-16 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-05-23 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_145_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_145_chunk (
    CONSTRAINT constraint_145 CHECK ((("timestamp" >= '2024-06-13 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-06-20 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_146_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_146_chunk (
    CONSTRAINT constraint_146 CHECK ((("timestamp" >= '2024-04-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-04-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_147_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_147_chunk (
    CONSTRAINT constraint_147 CHECK ((("timestamp" >= '2024-02-01 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-02-08 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_148_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_148_chunk (
    CONSTRAINT constraint_148 CHECK ((("timestamp" >= '2024-04-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-05-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_149_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_149_chunk (
    CONSTRAINT constraint_149 CHECK ((("timestamp" >= '2024-02-08 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-02-15 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_14_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_14_chunk (
    CONSTRAINT constraint_14 CHECK ((("timestamp" >= '2026-02-05 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_150_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_150_chunk (
    CONSTRAINT constraint_150 CHECK ((("timestamp" >= '2026-03-05 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_151_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_151_chunk (
    CONSTRAINT constraint_151 CHECK ((("timestamp" >= '2025-09-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-09-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_152_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_152_chunk (
    CONSTRAINT constraint_152 CHECK ((("timestamp" >= '2025-11-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-12-04 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_153_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_153_chunk (
    CONSTRAINT constraint_153 CHECK ((("timestamp" >= '2025-11-06 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-11-13 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_15_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_15_chunk (
    CONSTRAINT constraint_15 CHECK ((("timestamp" >= '2026-01-22 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-01-29 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_16_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_16_chunk (
    CONSTRAINT constraint_16 CHECK ((("timestamp" >= '2026-01-01 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-01-08 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_17_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_17_chunk (
    CONSTRAINT constraint_17 CHECK ((("timestamp" >= '2026-01-08 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-01-15 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_18_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_18_chunk (
    CONSTRAINT constraint_18 CHECK ((("timestamp" >= '2026-01-15 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-01-22 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_19_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_19_chunk (
    CONSTRAINT constraint_19 CHECK ((("timestamp" >= '2025-03-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-04-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_1_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_1_chunk (
    CONSTRAINT constraint_1 CHECK ((("timestamp" >= '2026-02-19 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_20_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_20_chunk (
    CONSTRAINT constraint_20 CHECK ((("timestamp" >= '2025-11-13 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-11-20 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_21_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_21_chunk (
    CONSTRAINT constraint_21 CHECK ((("timestamp" >= '2025-12-04 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-12-11 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_22_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_22_chunk (
    CONSTRAINT constraint_22 CHECK ((("timestamp" >= '2024-10-03 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-10-10 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_23_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_23_chunk (
    CONSTRAINT constraint_23 CHECK ((("timestamp" >= '2024-06-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-07-04 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_24_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_24_chunk (
    CONSTRAINT constraint_24 CHECK ((("timestamp" >= '2024-09-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-10-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_25_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_25_chunk (
    CONSTRAINT constraint_25 CHECK ((("timestamp" >= '2024-09-19 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-09-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_26_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_26_chunk (
    CONSTRAINT constraint_26 CHECK ((("timestamp" >= '2024-10-31 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-11-07 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_27_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_27_chunk (
    CONSTRAINT constraint_27 CHECK ((("timestamp" >= '2024-07-04 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-07-11 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_28_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_28_chunk (
    CONSTRAINT constraint_28 CHECK ((("timestamp" >= '2025-01-23 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-01-30 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_29_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_29_chunk (
    CONSTRAINT constraint_29 CHECK ((("timestamp" >= '2025-05-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-06-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_2_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_2_chunk (
    CONSTRAINT constraint_2 CHECK ((("timestamp" >= '2026-02-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_30_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_30_chunk (
    CONSTRAINT constraint_30 CHECK ((("timestamp" >= '2025-09-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-10-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_31_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_31_chunk (
    CONSTRAINT constraint_31 CHECK ((("timestamp" >= '2024-10-24 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-10-31 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_32_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_32_chunk (
    CONSTRAINT constraint_32 CHECK ((("timestamp" >= '2024-07-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-07-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_33_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_33_chunk (
    CONSTRAINT constraint_33 CHECK ((("timestamp" >= '2024-07-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-07-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_34_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_34_chunk (
    CONSTRAINT constraint_34 CHECK ((("timestamp" >= '2025-10-30 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-11-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_35_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_35_chunk (
    CONSTRAINT constraint_35 CHECK ((("timestamp" >= '2024-08-15 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-08-22 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_36_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_36_chunk (
    CONSTRAINT constraint_36 CHECK ((("timestamp" >= '2024-10-17 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-10-24 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_37_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_37_chunk (
    CONSTRAINT constraint_37 CHECK ((("timestamp" >= '2024-09-05 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-09-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_38_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_38_chunk (
    CONSTRAINT constraint_38 CHECK ((("timestamp" >= '2024-08-22 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-08-29 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_39_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_39_chunk (
    CONSTRAINT constraint_39 CHECK ((("timestamp" >= '2025-07-17 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-07-24 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_3_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_3_chunk (
    CONSTRAINT constraint_3 CHECK ((("timestamp" >= '2026-02-12 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_40_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_40_chunk (
    CONSTRAINT constraint_40 CHECK ((("timestamp" >= '2025-03-06 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-03-13 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_41_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_41_chunk (
    CONSTRAINT constraint_41 CHECK ((("timestamp" >= '2024-12-19 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-12-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_42_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_42_chunk (
    CONSTRAINT constraint_42 CHECK ((("timestamp" >= '2024-06-20 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-06-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_43_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_43_chunk (
    CONSTRAINT constraint_43 CHECK ((("timestamp" >= '2025-06-05 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-06-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_44_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_44_chunk (
    CONSTRAINT constraint_44 CHECK ((("timestamp" >= '2025-02-20 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-02-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_45_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_45_chunk (
    CONSTRAINT constraint_45 CHECK ((("timestamp" >= '2025-04-10 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-04-17 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_46_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_46_chunk (
    CONSTRAINT constraint_46 CHECK ((("timestamp" >= '2024-09-12 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-09-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_47_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_47_chunk (
    CONSTRAINT constraint_47 CHECK ((("timestamp" >= '2024-08-08 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-08-15 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_48_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_48_chunk (
    CONSTRAINT constraint_48 CHECK ((("timestamp" >= '2024-07-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-08-01 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_49_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_49_chunk (
    CONSTRAINT constraint_49 CHECK ((("timestamp" >= '2024-10-10 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-10-17 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_4_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_4_chunk (
    CONSTRAINT constraint_4 CHECK ((("timestamp" >= '2021-09-23 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-09-30 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_50_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_50_chunk (
    CONSTRAINT constraint_50 CHECK ((("timestamp" >= '2024-11-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-11-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_51_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_51_chunk (
    CONSTRAINT constraint_51 CHECK ((("timestamp" >= '2025-07-03 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-07-10 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_52_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_52_chunk (
    CONSTRAINT constraint_52 CHECK ((("timestamp" >= '2025-06-12 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-06-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_53_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_53_chunk (
    CONSTRAINT constraint_53 CHECK ((("timestamp" >= '2025-11-20 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-11-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_54_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_54_chunk (
    CONSTRAINT constraint_54 CHECK ((("timestamp" >= '2025-06-19 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-06-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_55_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_55_chunk (
    CONSTRAINT constraint_55 CHECK ((("timestamp" >= '2025-08-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-08-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_56_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_56_chunk (
    CONSTRAINT constraint_56 CHECK ((("timestamp" >= '2024-11-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2024-11-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_57_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_57_chunk (
    CONSTRAINT constraint_57 CHECK ((("timestamp" >= '2025-08-21 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-08-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_58_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_58_chunk (
    CONSTRAINT constraint_58 CHECK ((("timestamp" >= '2025-08-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-08-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_59_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_59_chunk (
    CONSTRAINT constraint_59 CHECK ((("timestamp" >= '2025-04-24 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-05-01 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_5_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_5_chunk (
    CONSTRAINT constraint_5 CHECK ((("timestamp" >= '2022-02-10 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2022-02-17 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_60_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_60_chunk (
    CONSTRAINT constraint_60 CHECK ((("timestamp" >= '2025-04-17 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-04-24 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_61_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_61_chunk (
    CONSTRAINT constraint_61 CHECK ((("timestamp" >= '2025-09-04 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-09-11 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_62_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_62_chunk (
    CONSTRAINT constraint_62 CHECK ((("timestamp" >= '2025-08-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-09-04 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_63_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_63_chunk (
    CONSTRAINT constraint_63 CHECK ((("timestamp" >= '2025-09-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-09-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_64_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_64_chunk (
    CONSTRAINT constraint_64 CHECK ((("timestamp" >= '2025-10-23 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-10-30 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_65_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_65_chunk (
    CONSTRAINT constraint_65 CHECK ((("timestamp" >= '2025-05-15 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2025-05-22 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_66_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_66_chunk (
    CONSTRAINT constraint_66 CHECK ((("timestamp" >= '2020-01-30 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2020-02-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_67_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_67_chunk (
    CONSTRAINT constraint_67 CHECK ((("timestamp" >= '2016-12-22 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-12-29 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_68_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_68_chunk (
    CONSTRAINT constraint_68 CHECK ((("timestamp" >= '2017-01-12 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2017-01-19 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_69_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_69_chunk (
    CONSTRAINT constraint_69 CHECK ((("timestamp" >= '2016-10-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-11-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_6_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_6_chunk (
    CONSTRAINT constraint_6 CHECK ((("timestamp" >= '2021-12-16 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-12-23 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_70_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_70_chunk (
    CONSTRAINT constraint_70 CHECK ((("timestamp" >= '2021-08-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-09-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_71_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_71_chunk (
    CONSTRAINT constraint_71 CHECK ((("timestamp" >= '2017-08-24 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2017-08-31 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_72_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_72_chunk (
    CONSTRAINT constraint_72 CHECK ((("timestamp" >= '2017-01-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2017-02-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_73_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_73_chunk (
    CONSTRAINT constraint_73 CHECK ((("timestamp" >= '2016-03-24 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-03-31 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_74_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_74_chunk (
    CONSTRAINT constraint_74 CHECK ((("timestamp" >= '2017-09-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2017-10-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_75_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_75_chunk (
    CONSTRAINT constraint_75 CHECK ((("timestamp" >= '2016-09-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-10-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_76_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_76_chunk (
    CONSTRAINT constraint_76 CHECK ((("timestamp" >= '2018-12-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2019-01-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_77_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_77_chunk (
    CONSTRAINT constraint_77 CHECK ((("timestamp" >= '2016-03-17 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-03-24 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_78_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_78_chunk (
    CONSTRAINT constraint_78 CHECK ((("timestamp" >= '2020-04-02 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2020-04-09 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_79_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_79_chunk (
    CONSTRAINT constraint_79 CHECK ((("timestamp" >= '2018-10-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2018-11-01 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_7_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_7_chunk (
    CONSTRAINT constraint_7 CHECK ((("timestamp" >= '2021-10-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-10-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_80_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_80_chunk (
    CONSTRAINT constraint_80 CHECK ((("timestamp" >= '2016-07-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-07-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_81_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_81_chunk (
    CONSTRAINT constraint_81 CHECK ((("timestamp" >= '2020-06-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2020-06-18 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_82_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_82_chunk (
    CONSTRAINT constraint_82 CHECK ((("timestamp" >= '2017-06-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2017-07-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_83_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_83_chunk (
    CONSTRAINT constraint_83 CHECK ((("timestamp" >= '2016-08-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-08-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_84_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_84_chunk (
    CONSTRAINT constraint_84 CHECK ((("timestamp" >= '2016-02-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-03-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_85_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_85_chunk (
    CONSTRAINT constraint_85 CHECK ((("timestamp" >= '2021-04-22 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-04-29 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_86_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_86_chunk (
    CONSTRAINT constraint_86 CHECK ((("timestamp" >= '2016-02-18 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-02-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_87_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_87_chunk (
    CONSTRAINT constraint_87 CHECK ((("timestamp" >= '2016-05-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-06-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_88_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_88_chunk (
    CONSTRAINT constraint_88 CHECK ((("timestamp" >= '2016-03-31 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-04-07 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_89_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_89_chunk (
    CONSTRAINT constraint_89 CHECK ((("timestamp" >= '2016-03-10 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-03-17 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_8_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_8_chunk (
    CONSTRAINT constraint_8 CHECK ((("timestamp" >= '2021-10-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-10-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_90_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_90_chunk (
    CONSTRAINT constraint_90 CHECK ((("timestamp" >= '2016-01-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-02-04 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_91_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_91_chunk (
    CONSTRAINT constraint_91 CHECK ((("timestamp" >= '2016-12-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2017-01-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_92_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_92_chunk (
    CONSTRAINT constraint_92 CHECK ((("timestamp" >= '2016-01-21 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-01-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_93_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_93_chunk (
    CONSTRAINT constraint_93 CHECK ((("timestamp" >= '2021-04-15 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-04-22 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_94_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_94_chunk (
    CONSTRAINT constraint_94 CHECK ((("timestamp" >= '2016-04-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-04-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_95_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_95_chunk (
    CONSTRAINT constraint_95 CHECK ((("timestamp" >= '2016-03-03 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-03-10 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_96_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_96_chunk (
    CONSTRAINT constraint_96 CHECK ((("timestamp" >= '2016-01-14 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-01-21 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_97_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_97_chunk (
    CONSTRAINT constraint_97 CHECK ((("timestamp" >= '2021-05-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-06-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_98_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_98_chunk (
    CONSTRAINT constraint_98 CHECK ((("timestamp" >= '2021-04-29 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-05-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_99_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_99_chunk (
    CONSTRAINT constraint_99 CHECK ((("timestamp" >= '2016-04-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2016-04-14 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_4_9_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_4_9_chunk (
    CONSTRAINT constraint_9 CHECK ((("timestamp" >= '2021-09-16 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2021-09-23 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.intel_embeddings);


--
-- Name: _hyper_5_154_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_154_chunk (
    CONSTRAINT constraint_154 CHECK ((("timestamp" >= '2026-02-23 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-24 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_155_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_155_chunk (
    CONSTRAINT constraint_155 CHECK ((("timestamp" >= '2026-02-24 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-25 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_156_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_156_chunk (
    CONSTRAINT constraint_156 CHECK ((("timestamp" >= '2026-02-25 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-26 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_157_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_157_chunk (
    CONSTRAINT constraint_157 CHECK ((("timestamp" >= '2026-02-26 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-27 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_158_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_158_chunk (
    CONSTRAINT constraint_158 CHECK ((("timestamp" >= '2026-02-27 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-02-28 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_159_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_159_chunk (
    CONSTRAINT constraint_159 CHECK ((("timestamp" >= '2026-02-28 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-01 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_160_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_160_chunk (
    CONSTRAINT constraint_160 CHECK ((("timestamp" >= '2026-03-01 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-02 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_161_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_161_chunk (
    CONSTRAINT constraint_161 CHECK ((("timestamp" >= '2026-03-02 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-03 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_162_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_162_chunk (
    CONSTRAINT constraint_162 CHECK ((("timestamp" >= '2026-03-03 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-04 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_163_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_163_chunk (
    CONSTRAINT constraint_163 CHECK ((("timestamp" >= '2026-03-04 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-05 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_164_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_164_chunk (
    CONSTRAINT constraint_164 CHECK ((("timestamp" >= '2026-03-05 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-06 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_165_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_165_chunk (
    CONSTRAINT constraint_165 CHECK ((("timestamp" >= '2026-03-10 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-11 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_166_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_166_chunk (
    CONSTRAINT constraint_166 CHECK ((("timestamp" >= '2026-03-06 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-07 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_167_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_167_chunk (
    CONSTRAINT constraint_167 CHECK ((("timestamp" >= '2026-03-07 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-08 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_168_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_168_chunk (
    CONSTRAINT constraint_168 CHECK ((("timestamp" >= '2026-03-08 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-09 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_169_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_169_chunk (
    CONSTRAINT constraint_169 CHECK ((("timestamp" >= '2026-03-09 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-10 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_170_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_170_chunk (
    CONSTRAINT constraint_170 CHECK ((("timestamp" >= '2026-03-11 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-12 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _hyper_5_171_chunk; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._hyper_5_171_chunk (
    CONSTRAINT constraint_171 CHECK ((("timestamp" >= '2026-03-12 00:00:00+00'::timestamp with time zone) AND ("timestamp" < '2026-03-13 00:00:00+00'::timestamp with time zone)))
)
INHERITS (public.raw_market_ticks);


--
-- Name: _materialized_hypertable_6; Type: TABLE; Schema: _timescaledb_internal; Owner: -
--

CREATE TABLE _timescaledb_internal._materialized_hypertable_6 (
    bucket timestamp with time zone NOT NULL,
    symbol character varying(20),
    open double precision,
    high double precision,
    low double precision,
    close double precision,
    volume double precision,
    tick_count bigint
);


--
-- Name: _partial_view_6; Type: VIEW; Schema: _timescaledb_internal; Owner: -
--

CREATE VIEW _timescaledb_internal._partial_view_6 AS
 SELECT public.time_bucket('00:01:00'::interval, "timestamp") AS bucket,
    symbol,
    public.first(price, "timestamp") AS open,
    max(price) AS high,
    min(price) AS low,
    public.last(price, "timestamp") AS close,
    sum(volume) AS volume,
    count(*) AS tick_count
   FROM public.raw_market_ticks
  GROUP BY (public.time_bucket('00:01:00'::interval, "timestamp")), symbol;


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
-- Name: discovery_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discovery_audit_log (
    id bigint NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    ticker character varying(20) NOT NULL,
    action character varying(20) NOT NULL,
    conviction_before double precision,
    conviction_after double precision,
    source_channel character varying(100),
    extraction_confidence double precision,
    likelihood_ratio double precision,
    multi_source_bonus boolean DEFAULT false,
    payload jsonb,
    watchlist_size integer
);


--
-- Name: discovery_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.discovery_audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: discovery_audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.discovery_audit_log_id_seq OWNED BY public.discovery_audit_log.id;


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
-- Name: intel_embeddings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.intel_embeddings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: intel_embeddings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.intel_embeddings_id_seq OWNED BY public.intel_embeddings.id;


--
-- Name: macro_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.macro_logs (
    "timestamp" timestamp with time zone,
    fg_index double precision,
    yield_10y double precision
);


--
-- Name: market_ticks_1min; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.market_ticks_1min AS
 SELECT bucket,
    symbol,
    open,
    high,
    low,
    close,
    volume,
    tick_count
   FROM _timescaledb_internal._materialized_hypertable_6;


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
-- Name: _hyper_4_100_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_100_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_100_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_100_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_100_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_100_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_100_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_100_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_100_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_100_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_101_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_101_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_101_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_101_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_101_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_101_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_101_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_101_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_101_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_101_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_102_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_102_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_102_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_102_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_102_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_102_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_102_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_102_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_102_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_102_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_103_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_103_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_103_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_103_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_103_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_103_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_103_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_103_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_103_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_103_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_104_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_104_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_104_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_104_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_104_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_104_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_104_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_104_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_104_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_104_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_105_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_105_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_105_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_105_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_105_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_105_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_105_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_105_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_105_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_105_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_106_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_106_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_106_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_106_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_106_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_106_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_106_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_106_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_106_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_106_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_107_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_107_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_107_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_107_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_107_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_107_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_107_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_107_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_107_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_107_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_108_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_108_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_108_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_108_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_108_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_108_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_108_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_108_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_108_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_108_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_109_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_109_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_109_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_109_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_109_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_109_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_109_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_109_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_109_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_109_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_10_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_10_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_10_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_10_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_10_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_10_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_10_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_10_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_10_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_10_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_110_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_110_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_110_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_110_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_110_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_110_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_110_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_110_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_110_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_110_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_111_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_111_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_111_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_111_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_111_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_111_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_111_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_111_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_111_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_111_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_112_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_112_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_112_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_112_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_112_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_112_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_112_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_112_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_112_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_112_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_113_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_113_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_113_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_113_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_113_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_113_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_113_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_113_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_113_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_113_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_114_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_114_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_114_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_114_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_114_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_114_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_114_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_114_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_114_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_114_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_115_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_115_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_115_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_115_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_115_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_115_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_115_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_115_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_115_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_115_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_116_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_116_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_116_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_116_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_116_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_116_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_116_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_116_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_116_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_116_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_117_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_117_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_117_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_117_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_117_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_117_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_117_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_117_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_117_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_117_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_118_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_118_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_118_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_118_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_118_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_118_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_118_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_118_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_118_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_118_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_119_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_119_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_119_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_119_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_119_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_119_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_119_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_119_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_119_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_119_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_11_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_11_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_11_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_11_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_11_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_11_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_11_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_11_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_11_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_11_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_120_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_120_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_120_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_120_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_120_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_120_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_120_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_120_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_120_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_120_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_121_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_121_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_121_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_121_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_121_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_121_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_121_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_121_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_121_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_121_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_122_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_122_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_122_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_122_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_122_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_122_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_122_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_122_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_122_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_122_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_123_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_123_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_123_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_123_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_123_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_123_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_123_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_123_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_123_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_123_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_124_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_124_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_124_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_124_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_124_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_124_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_124_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_124_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_124_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_124_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_125_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_125_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_125_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_125_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_125_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_125_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_125_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_125_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_125_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_125_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_126_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_126_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_126_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_126_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_126_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_126_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_126_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_126_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_126_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_126_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_127_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_127_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_127_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_127_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_127_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_127_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_127_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_127_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_127_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_127_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_128_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_128_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_128_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_128_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_128_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_128_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_128_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_128_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_128_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_128_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_129_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_129_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_129_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_129_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_129_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_129_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_129_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_129_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_129_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_129_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_12_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_12_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_12_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_12_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_12_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_12_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_12_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_12_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_12_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_12_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_130_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_130_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_130_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_130_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_130_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_130_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_130_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_130_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_130_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_130_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_131_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_131_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_131_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_131_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_131_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_131_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_131_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_131_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_131_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_131_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_132_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_132_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_132_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_132_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_132_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_132_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_132_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_132_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_132_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_132_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_133_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_133_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_133_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_133_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_133_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_133_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_133_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_133_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_133_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_133_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_134_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_134_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_134_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_134_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_134_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_134_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_134_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_134_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_134_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_134_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_135_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_135_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_135_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_135_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_135_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_135_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_135_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_135_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_135_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_135_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_136_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_136_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_136_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_136_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_136_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_136_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_136_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_136_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_136_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_136_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_137_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_137_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_137_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_137_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_137_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_137_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_137_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_137_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_137_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_137_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_138_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_138_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_138_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_138_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_138_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_138_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_138_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_138_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_138_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_138_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_139_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_139_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_139_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_139_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_139_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_139_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_139_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_139_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_139_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_139_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_13_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_13_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_13_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_13_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_13_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_13_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_13_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_13_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_13_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_13_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_140_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_140_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_140_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_140_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_140_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_140_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_140_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_140_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_140_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_140_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_141_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_141_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_141_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_141_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_141_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_141_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_141_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_141_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_141_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_141_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_142_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_142_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_142_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_142_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_142_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_142_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_142_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_142_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_142_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_142_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_143_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_143_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_143_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_143_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_143_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_143_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_143_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_143_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_143_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_143_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_144_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_144_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_144_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_144_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_144_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_144_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_144_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_144_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_144_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_144_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_145_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_145_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_145_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_145_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_145_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_145_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_145_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_145_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_145_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_145_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_146_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_146_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_146_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_146_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_146_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_146_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_146_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_146_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_146_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_146_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_147_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_147_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_147_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_147_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_147_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_147_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_147_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_147_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_147_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_147_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_148_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_148_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_148_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_148_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_148_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_148_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_148_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_148_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_148_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_148_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_149_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_149_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_149_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_149_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_149_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_149_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_149_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_149_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_149_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_149_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_14_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_14_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_14_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_14_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_14_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_14_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_14_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_14_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_14_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_14_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_150_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_150_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_150_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_150_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_150_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_150_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_150_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_150_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_150_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_150_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_151_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_151_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_151_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_151_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_151_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_151_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_151_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_151_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_151_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_151_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_152_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_152_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_152_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_152_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_152_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_152_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_152_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_152_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_152_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_152_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_153_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_153_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_153_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_153_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_153_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_153_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_153_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_153_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_153_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_153_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_15_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_15_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_15_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_15_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_15_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_15_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_15_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_15_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_15_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_15_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_16_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_16_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_16_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_16_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_16_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_16_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_16_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_16_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_16_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_16_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_17_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_17_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_17_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_17_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_17_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_17_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_17_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_17_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_17_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_17_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_18_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_18_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_18_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_18_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_18_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_18_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_18_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_18_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_18_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_18_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_19_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_19_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_19_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_19_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_19_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_19_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_19_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_19_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_19_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_19_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_1_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_1_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_1_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_1_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_1_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_1_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_1_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_1_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_1_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_1_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_20_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_20_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_20_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_20_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_20_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_20_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_20_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_20_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_20_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_20_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_21_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_21_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_21_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_21_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_21_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_21_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_21_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_21_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_21_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_21_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_22_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_22_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_22_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_22_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_22_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_22_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_22_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_22_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_22_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_22_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_23_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_23_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_23_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_23_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_23_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_23_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_23_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_23_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_23_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_23_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_24_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_24_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_24_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_24_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_24_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_24_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_24_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_24_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_24_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_24_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_25_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_25_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_25_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_25_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_25_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_25_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_25_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_25_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_25_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_25_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_26_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_26_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_26_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_26_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_26_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_26_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_26_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_26_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_26_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_26_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_27_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_27_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_27_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_27_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_27_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_27_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_27_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_27_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_27_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_27_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_28_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_28_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_28_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_28_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_28_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_28_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_28_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_28_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_28_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_28_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_29_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_29_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_29_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_29_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_29_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_29_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_29_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_29_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_29_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_29_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_2_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_2_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_2_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_2_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_2_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_2_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_2_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_2_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_2_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_2_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_30_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_30_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_30_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_30_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_30_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_30_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_30_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_30_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_30_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_30_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_31_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_31_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_31_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_31_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_31_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_31_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_31_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_31_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_31_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_31_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_32_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_32_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_32_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_32_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_32_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_32_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_32_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_32_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_32_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_32_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_33_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_33_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_33_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_33_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_33_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_33_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_33_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_33_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_33_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_33_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_34_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_34_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_34_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_34_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_34_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_34_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_34_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_34_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_34_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_34_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_35_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_35_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_35_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_35_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_35_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_35_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_35_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_35_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_35_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_35_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_36_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_36_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_36_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_36_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_36_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_36_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_36_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_36_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_36_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_36_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_37_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_37_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_37_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_37_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_37_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_37_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_37_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_37_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_37_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_37_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_38_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_38_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_38_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_38_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_38_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_38_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_38_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_38_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_38_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_38_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_39_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_39_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_39_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_39_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_39_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_39_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_39_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_39_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_39_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_39_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_3_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_3_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_3_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_3_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_3_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_3_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_3_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_3_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_3_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_3_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_40_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_40_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_40_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_40_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_40_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_40_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_40_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_40_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_40_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_40_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_41_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_41_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_41_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_41_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_41_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_41_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_41_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_41_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_41_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_41_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_42_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_42_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_42_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_42_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_42_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_42_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_42_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_42_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_42_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_42_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_43_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_43_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_43_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_43_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_43_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_43_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_43_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_43_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_43_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_43_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_44_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_44_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_44_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_44_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_44_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_44_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_44_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_44_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_44_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_44_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_45_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_45_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_45_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_45_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_45_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_45_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_45_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_45_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_45_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_45_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_46_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_46_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_46_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_46_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_46_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_46_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_46_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_46_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_46_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_46_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_47_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_47_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_47_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_47_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_47_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_47_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_47_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_47_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_47_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_47_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_48_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_48_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_48_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_48_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_48_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_48_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_48_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_48_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_48_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_48_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_49_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_49_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_49_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_49_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_49_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_49_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_49_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_49_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_49_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_49_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_4_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_4_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_4_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_4_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_4_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_4_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_4_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_4_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_4_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_4_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_50_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_50_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_50_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_50_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_50_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_50_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_50_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_50_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_50_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_50_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_51_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_51_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_51_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_51_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_51_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_51_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_51_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_51_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_51_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_51_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_52_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_52_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_52_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_52_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_52_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_52_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_52_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_52_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_52_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_52_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_53_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_53_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_53_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_53_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_53_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_53_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_53_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_53_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_53_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_53_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_54_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_54_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_54_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_54_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_54_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_54_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_54_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_54_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_54_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_54_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_55_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_55_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_55_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_55_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_55_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_55_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_55_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_55_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_55_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_55_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_56_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_56_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_56_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_56_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_56_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_56_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_56_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_56_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_56_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_56_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_57_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_57_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_57_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_57_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_57_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_57_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_57_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_57_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_57_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_57_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_58_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_58_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_58_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_58_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_58_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_58_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_58_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_58_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_58_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_58_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_59_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_59_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_59_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_59_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_59_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_59_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_59_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_59_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_59_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_59_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_5_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_5_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_5_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_5_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_5_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_5_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_5_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_5_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_5_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_5_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_60_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_60_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_60_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_60_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_60_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_60_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_60_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_60_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_60_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_60_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_61_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_61_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_61_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_61_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_61_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_61_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_61_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_61_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_61_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_61_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_62_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_62_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_62_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_62_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_62_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_62_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_62_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_62_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_62_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_62_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_63_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_63_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_63_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_63_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_63_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_63_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_63_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_63_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_63_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_63_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_64_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_64_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_64_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_64_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_64_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_64_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_64_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_64_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_64_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_64_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_65_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_65_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_65_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_65_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_65_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_65_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_65_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_65_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_65_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_65_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_66_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_66_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_66_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_66_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_66_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_66_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_66_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_66_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_66_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_66_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_67_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_67_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_67_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_67_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_67_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_67_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_67_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_67_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_67_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_67_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_68_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_68_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_68_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_68_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_68_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_68_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_68_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_68_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_68_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_68_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_69_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_69_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_69_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_69_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_69_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_69_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_69_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_69_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_69_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_69_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_6_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_6_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_6_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_6_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_6_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_6_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_6_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_6_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_6_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_6_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_70_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_70_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_70_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_70_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_70_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_70_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_70_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_70_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_70_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_70_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_71_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_71_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_71_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_71_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_71_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_71_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_71_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_71_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_71_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_71_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_72_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_72_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_72_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_72_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_72_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_72_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_72_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_72_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_72_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_72_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_73_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_73_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_73_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_73_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_73_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_73_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_73_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_73_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_73_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_73_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_74_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_74_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_74_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_74_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_74_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_74_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_74_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_74_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_74_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_74_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_75_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_75_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_75_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_75_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_75_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_75_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_75_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_75_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_75_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_75_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_76_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_76_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_76_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_76_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_76_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_76_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_76_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_76_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_76_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_76_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_77_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_77_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_77_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_77_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_77_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_77_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_77_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_77_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_77_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_77_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_78_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_78_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_78_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_78_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_78_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_78_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_78_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_78_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_78_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_78_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_79_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_79_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_79_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_79_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_79_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_79_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_79_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_79_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_79_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_79_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_7_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_7_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_7_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_7_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_7_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_7_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_7_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_7_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_7_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_7_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_80_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_80_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_80_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_80_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_80_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_80_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_80_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_80_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_80_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_80_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_81_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_81_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_81_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_81_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_81_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_81_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_81_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_81_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_81_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_81_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_82_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_82_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_82_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_82_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_82_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_82_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_82_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_82_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_82_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_82_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_83_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_83_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_83_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_83_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_83_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_83_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_83_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_83_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_83_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_83_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_84_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_84_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_84_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_84_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_84_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_84_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_84_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_84_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_84_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_84_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_85_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_85_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_85_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_85_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_85_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_85_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_85_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_85_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_85_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_85_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_86_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_86_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_86_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_86_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_86_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_86_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_86_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_86_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_86_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_86_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_87_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_87_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_87_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_87_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_87_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_87_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_87_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_87_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_87_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_87_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_88_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_88_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_88_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_88_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_88_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_88_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_88_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_88_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_88_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_88_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_89_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_89_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_89_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_89_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_89_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_89_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_89_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_89_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_89_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_89_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_8_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_8_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_8_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_8_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_8_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_8_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_8_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_8_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_8_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_8_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_90_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_90_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_90_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_90_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_90_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_90_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_90_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_90_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_90_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_90_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_91_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_91_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_91_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_91_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_91_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_91_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_91_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_91_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_91_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_91_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_92_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_92_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_92_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_92_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_92_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_92_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_92_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_92_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_92_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_92_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_93_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_93_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_93_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_93_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_93_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_93_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_93_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_93_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_93_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_93_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_94_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_94_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_94_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_94_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_94_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_94_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_94_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_94_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_94_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_94_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_95_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_95_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_95_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_95_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_95_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_95_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_95_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_95_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_95_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_95_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_96_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_96_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_96_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_96_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_96_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_96_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_96_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_96_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_96_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_96_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_97_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_97_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_97_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_97_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_97_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_97_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_97_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_97_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_97_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_97_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_98_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_98_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_98_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_98_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_98_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_98_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_98_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_98_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_98_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_98_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_99_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_99_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_99_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_99_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_99_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_99_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_99_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_99_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_99_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_99_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_4_9_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_9_chunk ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


--
-- Name: _hyper_4_9_chunk timestamp; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_9_chunk ALTER COLUMN "timestamp" SET DEFAULT now();


--
-- Name: _hyper_4_9_chunk metadata; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_9_chunk ALTER COLUMN metadata SET DEFAULT '{}'::jsonb;


--
-- Name: _hyper_4_9_chunk tickers; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_9_chunk ALTER COLUMN tickers SET DEFAULT '{}'::character varying[];


--
-- Name: _hyper_4_9_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_4_9_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_154_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_154_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_154_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_154_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_155_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_155_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_155_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_155_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_156_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_156_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_156_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_156_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_157_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_157_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_157_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_157_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_158_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_158_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_158_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_158_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_159_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_159_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_159_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_159_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_160_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_160_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_160_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_160_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_161_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_161_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_161_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_161_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_162_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_162_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_162_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_162_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_163_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_163_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_163_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_163_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_164_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_164_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_164_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_164_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_165_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_165_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_165_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_165_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_166_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_166_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_166_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_166_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_167_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_167_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_167_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_167_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_168_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_168_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_168_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_168_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_169_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_169_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_169_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_169_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_170_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_170_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_170_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_170_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: _hyper_5_171_chunk id; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_171_chunk ALTER COLUMN id SET DEFAULT nextval('public.raw_market_ticks_id_seq'::regclass);


--
-- Name: _hyper_5_171_chunk created_at; Type: DEFAULT; Schema: _timescaledb_internal; Owner: -
--

ALTER TABLE ONLY _timescaledb_internal._hyper_5_171_chunk ALTER COLUMN created_at SET DEFAULT now();


--
-- Name: discovery_audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discovery_audit_log ALTER COLUMN id SET DEFAULT nextval('public.discovery_audit_log_id_seq'::regclass);


--
-- Name: geopolitical_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.geopolitical_logs ALTER COLUMN id SET DEFAULT nextval('public.geopolitical_logs_id_seq'::regclass);


--
-- Name: intel_embeddings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_embeddings ALTER COLUMN id SET DEFAULT nextval('public.intel_embeddings_id_seq'::regclass);


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
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: _hyper_4_100_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_100_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_100_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_100_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_100_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_100_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_100_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_100_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_100_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_100_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_100_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_100_chunk USING gin (tickers);


--
-- Name: _hyper_4_100_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_100_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_100_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_101_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_101_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_101_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_101_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_101_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_101_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_101_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_101_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_101_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_101_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_101_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_101_chunk USING gin (tickers);


--
-- Name: _hyper_4_101_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_101_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_101_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_102_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_102_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_102_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_102_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_102_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_102_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_102_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_102_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_102_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_102_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_102_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_102_chunk USING gin (tickers);


--
-- Name: _hyper_4_102_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_102_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_102_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_103_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_103_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_103_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_103_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_103_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_103_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_103_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_103_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_103_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_103_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_103_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_103_chunk USING gin (tickers);


--
-- Name: _hyper_4_103_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_103_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_103_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_104_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_104_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_104_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_104_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_104_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_104_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_104_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_104_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_104_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_104_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_104_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_104_chunk USING gin (tickers);


--
-- Name: _hyper_4_104_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_104_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_104_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_105_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_105_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_105_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_105_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_105_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_105_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_105_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_105_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_105_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_105_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_105_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_105_chunk USING gin (tickers);


--
-- Name: _hyper_4_105_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_105_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_105_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_106_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_106_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_106_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_106_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_106_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_106_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_106_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_106_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_106_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_106_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_106_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_106_chunk USING gin (tickers);


--
-- Name: _hyper_4_106_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_106_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_106_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_107_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_107_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_107_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_107_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_107_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_107_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_107_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_107_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_107_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_107_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_107_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_107_chunk USING gin (tickers);


--
-- Name: _hyper_4_107_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_107_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_107_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_108_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_108_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_108_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_108_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_108_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_108_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_108_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_108_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_108_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_108_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_108_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_108_chunk USING gin (tickers);


--
-- Name: _hyper_4_108_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_108_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_108_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_109_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_109_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_109_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_109_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_109_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_109_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_109_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_109_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_109_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_109_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_109_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_109_chunk USING gin (tickers);


--
-- Name: _hyper_4_109_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_109_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_109_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_10_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_10_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_10_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_10_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_10_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_10_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_10_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_10_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_10_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_10_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_10_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_10_chunk USING gin (tickers);


--
-- Name: _hyper_4_10_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_10_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_10_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_110_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_110_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_110_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_110_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_110_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_110_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_110_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_110_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_110_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_110_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_110_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_110_chunk USING gin (tickers);


--
-- Name: _hyper_4_110_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_110_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_110_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_111_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_111_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_111_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_111_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_111_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_111_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_111_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_111_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_111_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_111_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_111_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_111_chunk USING gin (tickers);


--
-- Name: _hyper_4_111_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_111_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_111_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_112_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_112_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_112_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_112_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_112_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_112_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_112_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_112_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_112_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_112_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_112_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_112_chunk USING gin (tickers);


--
-- Name: _hyper_4_112_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_112_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_112_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_113_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_113_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_113_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_113_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_113_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_113_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_113_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_113_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_113_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_113_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_113_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_113_chunk USING gin (tickers);


--
-- Name: _hyper_4_113_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_113_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_113_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_114_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_114_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_114_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_114_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_114_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_114_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_114_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_114_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_114_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_114_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_114_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_114_chunk USING gin (tickers);


--
-- Name: _hyper_4_114_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_114_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_114_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_115_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_115_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_115_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_115_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_115_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_115_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_115_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_115_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_115_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_115_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_115_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_115_chunk USING gin (tickers);


--
-- Name: _hyper_4_115_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_115_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_115_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_116_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_116_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_116_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_116_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_116_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_116_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_116_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_116_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_116_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_116_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_116_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_116_chunk USING gin (tickers);


--
-- Name: _hyper_4_116_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_116_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_116_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_117_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_117_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_117_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_117_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_117_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_117_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_117_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_117_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_117_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_117_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_117_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_117_chunk USING gin (tickers);


--
-- Name: _hyper_4_117_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_117_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_117_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_118_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_118_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_118_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_118_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_118_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_118_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_118_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_118_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_118_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_118_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_118_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_118_chunk USING gin (tickers);


--
-- Name: _hyper_4_118_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_118_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_118_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_119_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_119_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_119_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_119_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_119_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_119_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_119_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_119_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_119_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_119_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_119_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_119_chunk USING gin (tickers);


--
-- Name: _hyper_4_119_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_119_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_119_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_11_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_11_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_11_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_11_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_11_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_11_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_11_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_11_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_11_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_11_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_11_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_11_chunk USING gin (tickers);


--
-- Name: _hyper_4_11_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_11_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_11_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_120_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_120_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_120_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_120_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_120_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_120_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_120_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_120_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_120_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_120_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_120_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_120_chunk USING gin (tickers);


--
-- Name: _hyper_4_120_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_120_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_120_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_121_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_121_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_121_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_121_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_121_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_121_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_121_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_121_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_121_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_121_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_121_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_121_chunk USING gin (tickers);


--
-- Name: _hyper_4_121_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_121_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_121_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_122_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_122_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_122_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_122_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_122_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_122_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_122_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_122_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_122_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_122_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_122_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_122_chunk USING gin (tickers);


--
-- Name: _hyper_4_122_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_122_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_122_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_123_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_123_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_123_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_123_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_123_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_123_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_123_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_123_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_123_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_123_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_123_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_123_chunk USING gin (tickers);


--
-- Name: _hyper_4_123_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_123_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_123_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_124_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_124_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_124_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_124_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_124_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_124_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_124_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_124_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_124_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_124_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_124_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_124_chunk USING gin (tickers);


--
-- Name: _hyper_4_124_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_124_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_124_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_125_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_125_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_125_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_125_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_125_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_125_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_125_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_125_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_125_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_125_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_125_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_125_chunk USING gin (tickers);


--
-- Name: _hyper_4_125_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_125_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_125_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_126_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_126_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_126_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_126_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_126_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_126_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_126_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_126_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_126_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_126_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_126_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_126_chunk USING gin (tickers);


--
-- Name: _hyper_4_126_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_126_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_126_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_127_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_127_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_127_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_127_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_127_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_127_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_127_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_127_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_127_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_127_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_127_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_127_chunk USING gin (tickers);


--
-- Name: _hyper_4_127_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_127_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_127_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_128_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_128_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_128_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_128_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_128_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_128_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_128_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_128_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_128_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_128_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_128_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_128_chunk USING gin (tickers);


--
-- Name: _hyper_4_128_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_128_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_128_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_129_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_129_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_129_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_129_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_129_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_129_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_129_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_129_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_129_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_129_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_129_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_129_chunk USING gin (tickers);


--
-- Name: _hyper_4_129_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_129_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_129_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_12_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_12_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_12_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_12_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_12_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_12_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_12_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_12_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_12_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_12_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_12_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_12_chunk USING gin (tickers);


--
-- Name: _hyper_4_12_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_12_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_12_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_130_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_130_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_130_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_130_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_130_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_130_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_130_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_130_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_130_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_130_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_130_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_130_chunk USING gin (tickers);


--
-- Name: _hyper_4_130_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_130_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_130_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_131_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_131_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_131_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_131_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_131_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_131_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_131_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_131_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_131_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_131_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_131_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_131_chunk USING gin (tickers);


--
-- Name: _hyper_4_131_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_131_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_131_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_132_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_132_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_132_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_132_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_132_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_132_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_132_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_132_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_132_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_132_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_132_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_132_chunk USING gin (tickers);


--
-- Name: _hyper_4_132_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_132_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_132_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_133_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_133_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_133_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_133_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_133_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_133_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_133_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_133_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_133_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_133_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_133_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_133_chunk USING gin (tickers);


--
-- Name: _hyper_4_133_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_133_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_133_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_134_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_134_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_134_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_134_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_134_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_134_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_134_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_134_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_134_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_134_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_134_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_134_chunk USING gin (tickers);


--
-- Name: _hyper_4_134_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_134_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_134_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_135_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_135_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_135_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_135_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_135_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_135_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_135_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_135_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_135_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_135_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_135_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_135_chunk USING gin (tickers);


--
-- Name: _hyper_4_135_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_135_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_135_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_136_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_136_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_136_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_136_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_136_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_136_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_136_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_136_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_136_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_136_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_136_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_136_chunk USING gin (tickers);


--
-- Name: _hyper_4_136_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_136_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_136_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_137_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_137_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_137_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_137_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_137_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_137_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_137_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_137_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_137_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_137_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_137_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_137_chunk USING gin (tickers);


--
-- Name: _hyper_4_137_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_137_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_137_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_138_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_138_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_138_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_138_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_138_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_138_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_138_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_138_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_138_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_138_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_138_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_138_chunk USING gin (tickers);


--
-- Name: _hyper_4_138_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_138_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_138_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_139_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_139_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_139_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_139_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_139_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_139_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_139_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_139_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_139_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_139_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_139_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_139_chunk USING gin (tickers);


--
-- Name: _hyper_4_139_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_139_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_139_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_13_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_13_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_13_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_13_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_13_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_13_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_13_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_13_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_13_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_13_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_13_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_13_chunk USING gin (tickers);


--
-- Name: _hyper_4_13_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_13_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_13_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_140_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_140_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_140_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_140_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_140_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_140_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_140_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_140_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_140_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_140_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_140_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_140_chunk USING gin (tickers);


--
-- Name: _hyper_4_140_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_140_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_140_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_141_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_141_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_141_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_141_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_141_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_141_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_141_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_141_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_141_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_141_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_141_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_141_chunk USING gin (tickers);


--
-- Name: _hyper_4_141_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_141_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_141_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_142_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_142_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_142_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_142_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_142_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_142_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_142_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_142_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_142_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_142_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_142_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_142_chunk USING gin (tickers);


--
-- Name: _hyper_4_142_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_142_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_142_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_143_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_143_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_143_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_143_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_143_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_143_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_143_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_143_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_143_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_143_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_143_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_143_chunk USING gin (tickers);


--
-- Name: _hyper_4_143_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_143_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_143_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_144_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_144_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_144_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_144_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_144_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_144_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_144_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_144_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_144_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_144_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_144_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_144_chunk USING gin (tickers);


--
-- Name: _hyper_4_144_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_144_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_144_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_145_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_145_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_145_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_145_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_145_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_145_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_145_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_145_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_145_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_145_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_145_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_145_chunk USING gin (tickers);


--
-- Name: _hyper_4_145_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_145_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_145_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_146_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_146_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_146_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_146_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_146_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_146_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_146_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_146_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_146_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_146_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_146_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_146_chunk USING gin (tickers);


--
-- Name: _hyper_4_146_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_146_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_146_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_147_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_147_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_147_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_147_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_147_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_147_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_147_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_147_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_147_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_147_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_147_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_147_chunk USING gin (tickers);


--
-- Name: _hyper_4_147_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_147_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_147_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_148_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_148_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_148_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_148_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_148_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_148_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_148_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_148_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_148_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_148_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_148_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_148_chunk USING gin (tickers);


--
-- Name: _hyper_4_148_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_148_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_148_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_149_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_149_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_149_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_149_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_149_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_149_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_149_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_149_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_149_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_149_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_149_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_149_chunk USING gin (tickers);


--
-- Name: _hyper_4_149_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_149_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_149_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_14_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_14_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_14_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_14_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_14_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_14_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_14_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_14_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_14_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_14_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_14_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_14_chunk USING gin (tickers);


--
-- Name: _hyper_4_14_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_14_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_14_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_150_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_150_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_150_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_150_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_150_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_150_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_150_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_150_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_150_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_150_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_150_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_150_chunk USING gin (tickers);


--
-- Name: _hyper_4_150_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_150_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_150_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_151_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_151_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_151_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_151_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_151_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_151_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_151_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_151_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_151_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_151_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_151_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_151_chunk USING gin (tickers);


--
-- Name: _hyper_4_151_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_151_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_151_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_152_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_152_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_152_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_152_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_152_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_152_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_152_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_152_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_152_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_152_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_152_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_152_chunk USING gin (tickers);


--
-- Name: _hyper_4_152_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_152_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_152_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_153_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_153_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_153_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_153_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_153_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_153_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_153_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_153_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_153_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_153_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_153_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_153_chunk USING gin (tickers);


--
-- Name: _hyper_4_153_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_153_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_153_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_15_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_15_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_15_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_15_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_15_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_15_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_15_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_15_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_15_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_15_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_15_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_15_chunk USING gin (tickers);


--
-- Name: _hyper_4_15_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_15_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_15_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_16_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_16_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_16_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_16_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_16_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_16_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_16_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_16_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_16_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_16_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_16_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_16_chunk USING gin (tickers);


--
-- Name: _hyper_4_16_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_16_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_16_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_17_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_17_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_17_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_17_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_17_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_17_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_17_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_17_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_17_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_17_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_17_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_17_chunk USING gin (tickers);


--
-- Name: _hyper_4_17_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_17_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_17_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_18_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_18_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_18_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_18_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_18_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_18_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_18_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_18_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_18_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_18_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_18_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_18_chunk USING gin (tickers);


--
-- Name: _hyper_4_18_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_18_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_18_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_19_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_19_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_19_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_19_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_19_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_19_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_19_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_19_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_19_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_19_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_19_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_19_chunk USING gin (tickers);


--
-- Name: _hyper_4_19_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_19_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_19_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_1_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_1_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_1_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_1_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_1_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_1_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_1_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_1_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_1_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_1_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_1_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_1_chunk USING gin (tickers);


--
-- Name: _hyper_4_1_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_1_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_1_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_20_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_20_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_20_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_20_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_20_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_20_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_20_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_20_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_20_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_20_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_20_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_20_chunk USING gin (tickers);


--
-- Name: _hyper_4_20_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_20_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_20_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_21_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_21_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_21_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_21_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_21_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_21_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_21_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_21_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_21_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_21_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_21_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_21_chunk USING gin (tickers);


--
-- Name: _hyper_4_21_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_21_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_21_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_22_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_22_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_22_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_22_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_22_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_22_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_22_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_22_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_22_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_22_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_22_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_22_chunk USING gin (tickers);


--
-- Name: _hyper_4_22_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_22_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_22_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_23_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_23_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_23_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_23_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_23_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_23_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_23_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_23_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_23_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_23_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_23_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_23_chunk USING gin (tickers);


--
-- Name: _hyper_4_23_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_23_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_23_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_24_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_24_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_24_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_24_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_24_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_24_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_24_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_24_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_24_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_24_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_24_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_24_chunk USING gin (tickers);


--
-- Name: _hyper_4_24_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_24_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_24_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_25_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_25_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_25_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_25_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_25_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_25_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_25_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_25_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_25_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_25_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_25_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_25_chunk USING gin (tickers);


--
-- Name: _hyper_4_25_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_25_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_25_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_26_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_26_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_26_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_26_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_26_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_26_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_26_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_26_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_26_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_26_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_26_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_26_chunk USING gin (tickers);


--
-- Name: _hyper_4_26_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_26_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_26_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_27_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_27_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_27_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_27_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_27_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_27_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_27_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_27_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_27_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_27_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_27_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_27_chunk USING gin (tickers);


--
-- Name: _hyper_4_27_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_27_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_27_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_28_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_28_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_28_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_28_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_28_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_28_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_28_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_28_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_28_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_28_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_28_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_28_chunk USING gin (tickers);


--
-- Name: _hyper_4_28_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_28_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_28_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_29_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_29_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_29_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_29_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_29_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_29_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_29_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_29_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_29_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_29_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_29_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_29_chunk USING gin (tickers);


--
-- Name: _hyper_4_29_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_29_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_29_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_2_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_2_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_2_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_2_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_2_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_2_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_2_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_2_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_2_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_2_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_2_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_2_chunk USING gin (tickers);


--
-- Name: _hyper_4_2_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_2_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_2_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_30_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_30_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_30_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_30_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_30_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_30_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_30_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_30_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_30_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_30_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_30_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_30_chunk USING gin (tickers);


--
-- Name: _hyper_4_30_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_30_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_30_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_31_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_31_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_31_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_31_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_31_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_31_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_31_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_31_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_31_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_31_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_31_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_31_chunk USING gin (tickers);


--
-- Name: _hyper_4_31_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_31_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_31_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_32_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_32_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_32_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_32_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_32_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_32_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_32_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_32_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_32_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_32_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_32_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_32_chunk USING gin (tickers);


--
-- Name: _hyper_4_32_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_32_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_32_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_33_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_33_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_33_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_33_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_33_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_33_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_33_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_33_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_33_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_33_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_33_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_33_chunk USING gin (tickers);


--
-- Name: _hyper_4_33_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_33_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_33_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_34_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_34_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_34_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_34_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_34_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_34_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_34_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_34_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_34_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_34_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_34_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_34_chunk USING gin (tickers);


--
-- Name: _hyper_4_34_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_34_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_34_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_35_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_35_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_35_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_35_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_35_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_35_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_35_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_35_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_35_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_35_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_35_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_35_chunk USING gin (tickers);


--
-- Name: _hyper_4_35_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_35_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_35_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_36_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_36_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_36_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_36_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_36_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_36_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_36_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_36_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_36_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_36_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_36_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_36_chunk USING gin (tickers);


--
-- Name: _hyper_4_36_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_36_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_36_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_37_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_37_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_37_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_37_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_37_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_37_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_37_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_37_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_37_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_37_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_37_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_37_chunk USING gin (tickers);


--
-- Name: _hyper_4_37_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_37_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_37_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_38_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_38_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_38_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_38_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_38_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_38_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_38_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_38_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_38_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_38_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_38_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_38_chunk USING gin (tickers);


--
-- Name: _hyper_4_38_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_38_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_38_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_39_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_39_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_39_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_39_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_39_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_39_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_39_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_39_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_39_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_39_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_39_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_39_chunk USING gin (tickers);


--
-- Name: _hyper_4_39_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_39_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_39_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_3_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_3_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_3_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_3_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_3_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_3_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_3_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_3_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_3_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_3_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_3_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_3_chunk USING gin (tickers);


--
-- Name: _hyper_4_3_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_3_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_3_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_40_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_40_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_40_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_40_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_40_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_40_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_40_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_40_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_40_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_40_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_40_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_40_chunk USING gin (tickers);


--
-- Name: _hyper_4_40_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_40_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_40_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_41_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_41_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_41_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_41_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_41_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_41_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_41_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_41_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_41_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_41_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_41_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_41_chunk USING gin (tickers);


--
-- Name: _hyper_4_41_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_41_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_41_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_42_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_42_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_42_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_42_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_42_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_42_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_42_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_42_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_42_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_42_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_42_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_42_chunk USING gin (tickers);


--
-- Name: _hyper_4_42_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_42_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_42_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_43_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_43_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_43_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_43_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_43_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_43_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_43_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_43_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_43_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_43_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_43_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_43_chunk USING gin (tickers);


--
-- Name: _hyper_4_43_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_43_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_43_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_44_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_44_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_44_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_44_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_44_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_44_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_44_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_44_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_44_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_44_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_44_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_44_chunk USING gin (tickers);


--
-- Name: _hyper_4_44_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_44_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_44_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_45_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_45_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_45_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_45_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_45_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_45_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_45_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_45_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_45_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_45_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_45_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_45_chunk USING gin (tickers);


--
-- Name: _hyper_4_45_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_45_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_45_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_46_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_46_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_46_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_46_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_46_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_46_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_46_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_46_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_46_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_46_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_46_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_46_chunk USING gin (tickers);


--
-- Name: _hyper_4_46_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_46_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_46_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_47_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_47_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_47_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_47_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_47_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_47_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_47_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_47_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_47_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_47_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_47_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_47_chunk USING gin (tickers);


--
-- Name: _hyper_4_47_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_47_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_47_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_48_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_48_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_48_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_48_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_48_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_48_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_48_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_48_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_48_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_48_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_48_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_48_chunk USING gin (tickers);


--
-- Name: _hyper_4_48_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_48_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_48_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_49_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_49_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_49_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_49_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_49_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_49_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_49_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_49_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_49_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_49_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_49_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_49_chunk USING gin (tickers);


--
-- Name: _hyper_4_49_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_49_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_49_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_4_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_4_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_4_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_4_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_4_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_4_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_4_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_4_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_4_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_4_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_4_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_4_chunk USING gin (tickers);


--
-- Name: _hyper_4_4_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_4_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_4_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_50_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_50_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_50_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_50_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_50_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_50_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_50_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_50_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_50_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_50_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_50_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_50_chunk USING gin (tickers);


--
-- Name: _hyper_4_50_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_50_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_50_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_51_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_51_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_51_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_51_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_51_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_51_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_51_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_51_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_51_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_51_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_51_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_51_chunk USING gin (tickers);


--
-- Name: _hyper_4_51_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_51_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_51_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_52_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_52_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_52_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_52_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_52_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_52_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_52_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_52_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_52_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_52_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_52_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_52_chunk USING gin (tickers);


--
-- Name: _hyper_4_52_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_52_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_52_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_53_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_53_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_53_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_53_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_53_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_53_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_53_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_53_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_53_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_53_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_53_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_53_chunk USING gin (tickers);


--
-- Name: _hyper_4_53_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_53_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_53_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_54_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_54_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_54_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_54_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_54_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_54_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_54_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_54_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_54_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_54_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_54_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_54_chunk USING gin (tickers);


--
-- Name: _hyper_4_54_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_54_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_54_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_55_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_55_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_55_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_55_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_55_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_55_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_55_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_55_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_55_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_55_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_55_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_55_chunk USING gin (tickers);


--
-- Name: _hyper_4_55_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_55_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_55_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_56_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_56_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_56_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_56_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_56_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_56_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_56_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_56_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_56_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_56_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_56_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_56_chunk USING gin (tickers);


--
-- Name: _hyper_4_56_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_56_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_56_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_57_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_57_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_57_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_57_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_57_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_57_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_57_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_57_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_57_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_57_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_57_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_57_chunk USING gin (tickers);


--
-- Name: _hyper_4_57_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_57_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_57_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_58_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_58_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_58_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_58_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_58_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_58_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_58_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_58_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_58_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_58_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_58_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_58_chunk USING gin (tickers);


--
-- Name: _hyper_4_58_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_58_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_58_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_59_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_59_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_59_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_59_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_59_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_59_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_59_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_59_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_59_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_59_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_59_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_59_chunk USING gin (tickers);


--
-- Name: _hyper_4_59_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_59_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_59_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_5_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_5_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_5_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_5_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_5_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_5_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_5_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_5_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_5_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_5_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_5_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_5_chunk USING gin (tickers);


--
-- Name: _hyper_4_5_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_5_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_5_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_60_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_60_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_60_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_60_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_60_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_60_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_60_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_60_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_60_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_60_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_60_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_60_chunk USING gin (tickers);


--
-- Name: _hyper_4_60_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_60_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_60_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_61_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_61_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_61_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_61_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_61_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_61_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_61_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_61_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_61_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_61_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_61_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_61_chunk USING gin (tickers);


--
-- Name: _hyper_4_61_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_61_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_61_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_62_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_62_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_62_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_62_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_62_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_62_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_62_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_62_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_62_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_62_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_62_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_62_chunk USING gin (tickers);


--
-- Name: _hyper_4_62_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_62_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_62_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_63_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_63_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_63_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_63_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_63_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_63_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_63_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_63_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_63_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_63_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_63_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_63_chunk USING gin (tickers);


--
-- Name: _hyper_4_63_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_63_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_63_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_64_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_64_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_64_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_64_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_64_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_64_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_64_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_64_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_64_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_64_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_64_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_64_chunk USING gin (tickers);


--
-- Name: _hyper_4_64_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_64_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_64_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_65_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_65_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_65_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_65_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_65_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_65_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_65_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_65_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_65_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_65_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_65_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_65_chunk USING gin (tickers);


--
-- Name: _hyper_4_65_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_65_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_65_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_66_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_66_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_66_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_66_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_66_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_66_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_66_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_66_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_66_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_66_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_66_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_66_chunk USING gin (tickers);


--
-- Name: _hyper_4_66_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_66_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_66_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_67_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_67_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_67_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_67_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_67_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_67_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_67_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_67_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_67_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_67_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_67_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_67_chunk USING gin (tickers);


--
-- Name: _hyper_4_67_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_67_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_67_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_68_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_68_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_68_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_68_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_68_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_68_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_68_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_68_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_68_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_68_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_68_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_68_chunk USING gin (tickers);


--
-- Name: _hyper_4_68_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_68_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_68_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_69_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_69_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_69_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_69_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_69_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_69_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_69_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_69_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_69_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_69_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_69_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_69_chunk USING gin (tickers);


--
-- Name: _hyper_4_69_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_69_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_69_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_6_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_6_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_6_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_6_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_6_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_6_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_6_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_6_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_6_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_6_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_6_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_6_chunk USING gin (tickers);


--
-- Name: _hyper_4_6_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_6_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_6_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_70_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_70_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_70_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_70_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_70_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_70_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_70_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_70_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_70_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_70_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_70_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_70_chunk USING gin (tickers);


--
-- Name: _hyper_4_70_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_70_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_70_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_71_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_71_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_71_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_71_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_71_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_71_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_71_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_71_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_71_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_71_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_71_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_71_chunk USING gin (tickers);


--
-- Name: _hyper_4_71_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_71_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_71_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_72_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_72_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_72_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_72_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_72_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_72_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_72_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_72_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_72_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_72_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_72_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_72_chunk USING gin (tickers);


--
-- Name: _hyper_4_72_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_72_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_72_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_73_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_73_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_73_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_73_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_73_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_73_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_73_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_73_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_73_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_73_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_73_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_73_chunk USING gin (tickers);


--
-- Name: _hyper_4_73_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_73_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_73_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_74_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_74_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_74_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_74_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_74_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_74_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_74_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_74_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_74_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_74_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_74_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_74_chunk USING gin (tickers);


--
-- Name: _hyper_4_74_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_74_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_74_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_75_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_75_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_75_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_75_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_75_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_75_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_75_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_75_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_75_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_75_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_75_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_75_chunk USING gin (tickers);


--
-- Name: _hyper_4_75_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_75_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_75_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_76_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_76_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_76_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_76_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_76_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_76_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_76_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_76_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_76_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_76_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_76_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_76_chunk USING gin (tickers);


--
-- Name: _hyper_4_76_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_76_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_76_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_77_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_77_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_77_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_77_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_77_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_77_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_77_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_77_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_77_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_77_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_77_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_77_chunk USING gin (tickers);


--
-- Name: _hyper_4_77_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_77_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_77_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_78_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_78_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_78_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_78_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_78_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_78_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_78_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_78_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_78_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_78_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_78_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_78_chunk USING gin (tickers);


--
-- Name: _hyper_4_78_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_78_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_78_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_79_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_79_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_79_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_79_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_79_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_79_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_79_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_79_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_79_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_79_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_79_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_79_chunk USING gin (tickers);


--
-- Name: _hyper_4_79_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_79_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_79_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_7_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_7_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_7_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_7_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_7_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_7_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_7_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_7_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_7_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_7_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_7_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_7_chunk USING gin (tickers);


--
-- Name: _hyper_4_7_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_7_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_7_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_80_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_80_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_80_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_80_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_80_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_80_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_80_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_80_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_80_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_80_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_80_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_80_chunk USING gin (tickers);


--
-- Name: _hyper_4_80_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_80_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_80_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_81_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_81_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_81_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_81_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_81_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_81_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_81_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_81_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_81_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_81_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_81_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_81_chunk USING gin (tickers);


--
-- Name: _hyper_4_81_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_81_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_81_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_82_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_82_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_82_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_82_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_82_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_82_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_82_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_82_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_82_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_82_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_82_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_82_chunk USING gin (tickers);


--
-- Name: _hyper_4_82_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_82_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_82_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_83_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_83_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_83_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_83_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_83_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_83_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_83_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_83_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_83_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_83_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_83_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_83_chunk USING gin (tickers);


--
-- Name: _hyper_4_83_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_83_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_83_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_84_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_84_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_84_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_84_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_84_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_84_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_84_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_84_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_84_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_84_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_84_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_84_chunk USING gin (tickers);


--
-- Name: _hyper_4_84_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_84_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_84_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_85_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_85_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_85_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_85_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_85_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_85_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_85_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_85_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_85_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_85_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_85_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_85_chunk USING gin (tickers);


--
-- Name: _hyper_4_85_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_85_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_85_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_86_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_86_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_86_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_86_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_86_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_86_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_86_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_86_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_86_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_86_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_86_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_86_chunk USING gin (tickers);


--
-- Name: _hyper_4_86_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_86_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_86_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_87_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_87_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_87_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_87_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_87_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_87_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_87_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_87_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_87_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_87_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_87_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_87_chunk USING gin (tickers);


--
-- Name: _hyper_4_87_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_87_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_87_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_88_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_88_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_88_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_88_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_88_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_88_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_88_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_88_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_88_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_88_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_88_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_88_chunk USING gin (tickers);


--
-- Name: _hyper_4_88_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_88_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_88_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_89_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_89_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_89_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_89_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_89_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_89_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_89_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_89_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_89_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_89_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_89_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_89_chunk USING gin (tickers);


--
-- Name: _hyper_4_89_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_89_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_89_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_8_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_8_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_8_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_8_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_8_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_8_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_8_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_8_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_8_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_8_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_8_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_8_chunk USING gin (tickers);


--
-- Name: _hyper_4_8_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_8_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_8_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_90_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_90_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_90_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_90_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_90_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_90_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_90_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_90_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_90_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_90_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_90_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_90_chunk USING gin (tickers);


--
-- Name: _hyper_4_90_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_90_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_90_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_91_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_91_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_91_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_91_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_91_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_91_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_91_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_91_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_91_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_91_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_91_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_91_chunk USING gin (tickers);


--
-- Name: _hyper_4_91_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_91_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_91_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_92_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_92_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_92_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_92_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_92_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_92_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_92_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_92_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_92_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_92_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_92_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_92_chunk USING gin (tickers);


--
-- Name: _hyper_4_92_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_92_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_92_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_93_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_93_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_93_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_93_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_93_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_93_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_93_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_93_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_93_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_93_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_93_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_93_chunk USING gin (tickers);


--
-- Name: _hyper_4_93_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_93_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_93_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_94_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_94_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_94_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_94_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_94_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_94_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_94_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_94_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_94_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_94_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_94_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_94_chunk USING gin (tickers);


--
-- Name: _hyper_4_94_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_94_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_94_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_95_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_95_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_95_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_95_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_95_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_95_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_95_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_95_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_95_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_95_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_95_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_95_chunk USING gin (tickers);


--
-- Name: _hyper_4_95_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_95_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_95_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_96_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_96_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_96_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_96_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_96_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_96_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_96_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_96_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_96_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_96_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_96_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_96_chunk USING gin (tickers);


--
-- Name: _hyper_4_96_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_96_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_96_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_97_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_97_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_97_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_97_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_97_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_97_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_97_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_97_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_97_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_97_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_97_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_97_chunk USING gin (tickers);


--
-- Name: _hyper_4_97_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_97_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_97_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_98_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_98_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_98_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_98_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_98_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_98_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_98_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_98_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_98_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_98_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_98_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_98_chunk USING gin (tickers);


--
-- Name: _hyper_4_98_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_98_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_98_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_99_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_99_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_99_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_99_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_99_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_99_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_99_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_99_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_99_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_99_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_99_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_99_chunk USING gin (tickers);


--
-- Name: _hyper_4_99_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_99_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_99_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_4_9_chunk_idx_intel_embeddings_channel; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_9_chunk_idx_intel_embeddings_channel ON _timescaledb_internal._hyper_4_9_chunk USING btree (source_channel, "timestamp" DESC);


--
-- Name: _hyper_4_9_chunk_idx_intel_embeddings_hnsw; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_9_chunk_idx_intel_embeddings_hnsw ON _timescaledb_internal._hyper_4_9_chunk USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: _hyper_4_9_chunk_idx_intel_embeddings_source; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_9_chunk_idx_intel_embeddings_source ON _timescaledb_internal._hyper_4_9_chunk USING btree (source_type, "timestamp" DESC);


--
-- Name: _hyper_4_9_chunk_idx_intel_embeddings_tickers; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_9_chunk_idx_intel_embeddings_tickers ON _timescaledb_internal._hyper_4_9_chunk USING gin (tickers);


--
-- Name: _hyper_4_9_chunk_intel_embeddings_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_4_9_chunk_intel_embeddings_timestamp_idx ON _timescaledb_internal._hyper_4_9_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_154_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_154_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_154_chunk USING btree (id);


--
-- Name: _hyper_5_154_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_154_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_154_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_155_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_155_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_155_chunk USING btree (id);


--
-- Name: _hyper_5_155_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_155_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_155_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_156_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_156_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_156_chunk USING btree (id);


--
-- Name: _hyper_5_156_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_156_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_156_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_157_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_157_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_157_chunk USING btree (id);


--
-- Name: _hyper_5_157_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_157_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_157_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_158_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_158_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_158_chunk USING btree (id);


--
-- Name: _hyper_5_158_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_158_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_158_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_159_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_159_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_159_chunk USING btree (id);


--
-- Name: _hyper_5_159_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_159_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_159_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_160_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_160_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_160_chunk USING btree (id);


--
-- Name: _hyper_5_160_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_160_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_160_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_161_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_161_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_161_chunk USING btree (id);


--
-- Name: _hyper_5_161_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_161_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_161_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_162_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_162_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_162_chunk USING btree (id);


--
-- Name: _hyper_5_162_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_162_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_162_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_163_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_163_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_163_chunk USING btree (id);


--
-- Name: _hyper_5_163_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_163_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_163_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_164_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_164_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_164_chunk USING btree (id);


--
-- Name: _hyper_5_164_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_164_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_164_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_165_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_165_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_165_chunk USING btree (id);


--
-- Name: _hyper_5_165_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_165_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_165_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_166_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_166_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_166_chunk USING btree (id);


--
-- Name: _hyper_5_166_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_166_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_166_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_167_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_167_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_167_chunk USING btree (id);


--
-- Name: _hyper_5_167_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_167_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_167_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_168_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_168_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_168_chunk USING btree (id);


--
-- Name: _hyper_5_168_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_168_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_168_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_169_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_169_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_169_chunk USING btree (id);


--
-- Name: _hyper_5_169_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_169_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_169_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_170_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_170_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_170_chunk USING btree (id);


--
-- Name: _hyper_5_170_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_170_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_170_chunk USING btree ("timestamp" DESC);


--
-- Name: _hyper_5_171_chunk_idx_rmt_id; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_171_chunk_idx_rmt_id ON _timescaledb_internal._hyper_5_171_chunk USING btree (id);


--
-- Name: _hyper_5_171_chunk_raw_market_ticks_timestamp_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _hyper_5_171_chunk_raw_market_ticks_timestamp_idx ON _timescaledb_internal._hyper_5_171_chunk USING btree ("timestamp" DESC);


--
-- Name: _materialized_hypertable_6_bucket_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _materialized_hypertable_6_bucket_idx ON _timescaledb_internal._materialized_hypertable_6 USING btree (bucket DESC);


--
-- Name: _materialized_hypertable_6_symbol_bucket_idx; Type: INDEX; Schema: _timescaledb_internal; Owner: -
--

CREATE INDEX _materialized_hypertable_6_symbol_bucket_idx ON _timescaledb_internal._materialized_hypertable_6 USING btree (symbol, bucket DESC);


--
-- Name: discovery_audit_log_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX discovery_audit_log_timestamp_idx ON public.discovery_audit_log USING btree ("timestamp" DESC);


--
-- Name: idx_discovery_audit_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_audit_action ON public.discovery_audit_log USING btree (action, "timestamp" DESC);


--
-- Name: idx_discovery_audit_ticker; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_discovery_audit_ticker ON public.discovery_audit_log USING btree (ticker, "timestamp" DESC);


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
-- Name: idx_intel_embeddings_channel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intel_embeddings_channel ON public.intel_embeddings USING btree (source_channel, "timestamp" DESC);


--
-- Name: idx_intel_embeddings_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intel_embeddings_hnsw ON public.intel_embeddings USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: idx_intel_embeddings_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intel_embeddings_source ON public.intel_embeddings USING btree (source_type, "timestamp" DESC);


--
-- Name: idx_intel_embeddings_tickers; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_intel_embeddings_tickers ON public.intel_embeddings USING gin (tickers);


--
-- Name: idx_rmt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rmt_id ON public.raw_market_ticks USING btree (id);


--
-- Name: intel_embeddings_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX intel_embeddings_timestamp_idx ON public.intel_embeddings USING btree ("timestamp" DESC);


--
-- Name: raw_market_ticks_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX raw_market_ticks_timestamp_idx ON public.raw_market_ticks USING btree ("timestamp" DESC);


--
-- PostgreSQL database dump complete
--

\unrestrict dbmate


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20260307000000'),
    ('20260307000001'),
    ('20260307000003'),
    ('20260308000000'),
    ('20260313000000');
