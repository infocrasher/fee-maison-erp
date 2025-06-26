--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

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
-- Name: purchasestatus; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.purchasestatus AS ENUM (
    'DRAFT',
    'REQUESTED',
    'APPROVED',
    'ORDERED',
    'PARTIALLY_RECEIVED',
    'RECEIVED',
    'INVOICED',
    'CANCELLED'
);


ALTER TYPE public.purchasestatus OWNER TO fee_maison_user;

--
-- Name: purchaseurgency; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.purchaseurgency AS ENUM (
    'LOW',
    'NORMAL',
    'HIGH',
    'URGENT'
);


ALTER TYPE public.purchaseurgency OWNER TO fee_maison_user;

--
-- Name: stocklocationtype; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.stocklocationtype AS ENUM (
    'COMPTOIR',
    'INGREDIENTS_LOCAL',
    'INGREDIENTS_MAGASIN',
    'CONSOMMABLES'
);


ALTER TYPE public.stocklocationtype OWNER TO fee_maison_user;

--
-- Name: stockmovementtype; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.stockmovementtype AS ENUM (
    'ENTREE',
    'SORTIE',
    'TRANSFERT_SORTIE',
    'TRANSFERT_ENTREE',
    'AJUSTEMENT_POSITIF',
    'AJUSTEMENT_NEGATIF',
    'PRODUCTION',
    'VENTE',
    'INVENTAIRE'
);


ALTER TYPE public.stockmovementtype OWNER TO fee_maison_user;

--
-- Name: transferstatus; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.transferstatus AS ENUM (
    'DRAFT',
    'REQUESTED',
    'APPROVED',
    'IN_TRANSIT',
    'COMPLETED',
    'CANCELLED'
);


ALTER TYPE public.transferstatus OWNER TO fee_maison_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO fee_maison_user;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp without time zone
);


ALTER TABLE public.categories OWNER TO fee_maison_user;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.categories_id_seq OWNER TO fee_maison_user;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    role character varying(50),
    salaire_fixe numeric(10,2),
    prime numeric(10,2),
    is_active boolean,
    created_at timestamp without time zone,
    notes text
);


ALTER TABLE public.employees OWNER TO fee_maison_user;

--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.employees_id_seq OWNER TO fee_maison_user;

--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: order_employees; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.order_employees (
    order_id integer NOT NULL,
    employee_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.order_employees OWNER TO fee_maison_user;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity numeric(10,3) NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.order_items OWNER TO fee_maison_user;

--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.order_items_id_seq OWNER TO fee_maison_user;

--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    user_id integer,
    order_type character varying(50) NOT NULL,
    customer_name character varying(200),
    customer_phone character varying(20),
    customer_address text,
    delivery_option character varying(20),
    due_date timestamp without time zone NOT NULL,
    delivery_cost numeric(10,2),
    status character varying(50),
    notes text,
    total_amount numeric(10,2),
    created_at timestamp without time zone
);


ALTER TABLE public.orders OWNER TO fee_maison_user;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.orders_id_seq OWNER TO fee_maison_user;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.products (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    product_type character varying(50) NOT NULL,
    description text,
    price numeric(10,2),
    cost_price numeric(10,2),
    unit character varying(20) NOT NULL,
    sku character varying(50),
    quantity_in_stock double precision,
    category_id integer,
    created_at timestamp without time zone,
    stock_comptoir double precision NOT NULL,
    stock_ingredients_local double precision NOT NULL,
    stock_ingredients_magasin double precision NOT NULL,
    stock_consommables double precision NOT NULL,
    seuil_min_comptoir double precision,
    seuil_min_ingredients_local double precision,
    seuil_min_ingredients_magasin double precision,
    seuil_min_consommables double precision,
    last_stock_update timestamp without time zone,
    total_stock_value numeric(12,4) DEFAULT 0.0 NOT NULL
);


ALTER TABLE public.products OWNER TO fee_maison_user;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.products_id_seq OWNER TO fee_maison_user;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: purchase_items; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.purchase_items (
    id integer NOT NULL,
    purchase_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_ordered numeric(10,3) NOT NULL,
    quantity_received numeric(10,3),
    unit_price numeric(10,2) NOT NULL,
    discount_percentage numeric(5,2),
    stock_location character varying(50) NOT NULL,
    description_override character varying(255),
    supplier_reference character varying(100),
    notes text,
    created_at timestamp without time zone,
    original_quantity numeric(10,3),
    original_unit_id integer,
    original_unit_price numeric(10,2),
    updated_at timestamp without time zone
);


ALTER TABLE public.purchase_items OWNER TO fee_maison_user;

--
-- Name: purchase_items_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.purchase_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.purchase_items_id_seq OWNER TO fee_maison_user;

--
-- Name: purchase_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.purchase_items_id_seq OWNED BY public.purchase_items.id;


--
-- Name: purchases; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.purchases (
    id integer NOT NULL,
    reference character varying(50) NOT NULL,
    supplier_name character varying(200) NOT NULL,
    supplier_contact character varying(100),
    supplier_phone character varying(20),
    supplier_email character varying(120),
    supplier_address text,
    status public.purchasestatus NOT NULL,
    urgency public.purchaseurgency NOT NULL,
    requested_by_id integer NOT NULL,
    approved_by_id integer,
    received_by_id integer,
    requested_date timestamp without time zone NOT NULL,
    approved_date timestamp without time zone,
    expected_delivery_date timestamp without time zone,
    received_date timestamp without time zone,
    subtotal_amount numeric(10,2),
    tax_amount numeric(10,2),
    shipping_cost numeric(10,2),
    total_amount numeric(10,2),
    notes text,
    internal_notes text,
    terms_conditions text,
    payment_terms character varying(100),
    default_stock_location character varying(50),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_paid boolean,
    payment_date date
);


ALTER TABLE public.purchases OWNER TO fee_maison_user;

--
-- Name: purchases_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.purchases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.purchases_id_seq OWNER TO fee_maison_user;

--
-- Name: purchases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.purchases_id_seq OWNED BY public.purchases.id;


--
-- Name: recipe_ingredients; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.recipe_ingredients (
    id integer NOT NULL,
    recipe_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_needed numeric(10,3) NOT NULL,
    unit character varying(50) NOT NULL,
    notes character varying(255),
    created_at timestamp without time zone
);


ALTER TABLE public.recipe_ingredients OWNER TO fee_maison_user;

--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.recipe_ingredients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recipe_ingredients_id_seq OWNER TO fee_maison_user;

--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.recipe_ingredients_id_seq OWNED BY public.recipe_ingredients.id;


--
-- Name: recipes; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.recipes (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    product_id integer,
    yield_quantity integer NOT NULL,
    yield_unit character varying(50) NOT NULL,
    preparation_time integer,
    cooking_time integer,
    difficulty_level character varying(20),
    created_at timestamp without time zone,
    production_location character varying(50) DEFAULT 'ingredients_magasin'::character varying NOT NULL
);


ALTER TABLE public.recipes OWNER TO fee_maison_user;

--
-- Name: recipes_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.recipes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recipes_id_seq OWNER TO fee_maison_user;

--
-- Name: recipes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.recipes_id_seq OWNED BY public.recipes.id;


--
-- Name: stock_movements; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.stock_movements (
    id integer NOT NULL,
    reference character varying(50) NOT NULL,
    product_id integer NOT NULL,
    stock_location public.stocklocationtype NOT NULL,
    movement_type public.stockmovementtype NOT NULL,
    quantity double precision NOT NULL,
    unit_cost double precision,
    total_value double precision,
    stock_before double precision,
    stock_after double precision,
    order_id integer,
    transfer_id integer,
    user_id integer NOT NULL,
    reason character varying(255),
    notes text,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.stock_movements OWNER TO fee_maison_user;

--
-- Name: stock_movements_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.stock_movements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_movements_id_seq OWNER TO fee_maison_user;

--
-- Name: stock_movements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.stock_movements_id_seq OWNED BY public.stock_movements.id;


--
-- Name: stock_transfer_lines; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.stock_transfer_lines (
    id integer NOT NULL,
    transfer_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_requested double precision NOT NULL,
    quantity_approved double precision,
    quantity_transferred double precision,
    unit_cost double precision,
    notes character varying(255),
    created_at timestamp without time zone
);


ALTER TABLE public.stock_transfer_lines OWNER TO fee_maison_user;

--
-- Name: stock_transfer_lines_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.stock_transfer_lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_transfer_lines_id_seq OWNER TO fee_maison_user;

--
-- Name: stock_transfer_lines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.stock_transfer_lines_id_seq OWNED BY public.stock_transfer_lines.id;


--
-- Name: stock_transfers; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.stock_transfers (
    id integer NOT NULL,
    reference character varying(50) NOT NULL,
    source_location public.stocklocationtype NOT NULL,
    destination_location public.stocklocationtype NOT NULL,
    status public.transferstatus NOT NULL,
    requested_by_id integer NOT NULL,
    approved_by_id integer,
    completed_by_id integer,
    requested_date timestamp without time zone NOT NULL,
    approved_date timestamp without time zone,
    scheduled_date timestamp without time zone,
    completed_date timestamp without time zone,
    reason character varying(255),
    notes text,
    priority character varying(20)
);


ALTER TABLE public.stock_transfers OWNER TO fee_maison_user;

--
-- Name: stock_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.stock_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_transfers_id_seq OWNER TO fee_maison_user;

--
-- Name: stock_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.stock_transfers_id_seq OWNED BY public.stock_transfers.id;


--
-- Name: units; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.units (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    base_unit character varying(10) NOT NULL,
    conversion_factor numeric(10,3) NOT NULL,
    unit_type character varying(20) NOT NULL,
    display_order integer,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.units OWNER TO fee_maison_user;

--
-- Name: units_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.units_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.units_id_seq OWNER TO fee_maison_user;

--
-- Name: units_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.units_id_seq OWNED BY public.units.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO fee_maison_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO fee_maison_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: purchase_items id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items ALTER COLUMN id SET DEFAULT nextval('public.purchase_items_id_seq'::regclass);


--
-- Name: purchases id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases ALTER COLUMN id SET DEFAULT nextval('public.purchases_id_seq'::regclass);


--
-- Name: recipe_ingredients id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients ALTER COLUMN id SET DEFAULT nextval('public.recipe_ingredients_id_seq'::regclass);


--
-- Name: recipes id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes ALTER COLUMN id SET DEFAULT nextval('public.recipes_id_seq'::regclass);


--
-- Name: stock_movements id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements ALTER COLUMN id SET DEFAULT nextval('public.stock_movements_id_seq'::regclass);


--
-- Name: stock_transfer_lines id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines ALTER COLUMN id SET DEFAULT nextval('public.stock_transfer_lines_id_seq'::regclass);


--
-- Name: stock_transfers id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers ALTER COLUMN id SET DEFAULT nextval('public.stock_transfers_id_seq'::regclass);


--
-- Name: units id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.units ALTER COLUMN id SET DEFAULT nextval('public.units_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.alembic_version (version_num) FROM stdin;
a00b20b5fd08
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.categories (id, name, description, created_at) FROM stdin;
1	Ingrédients		2025-06-12 01:27:09.229977
2	Salés		2025-06-12 03:24:09.875163
3	pates		2025-06-13 22:35:20.371224
4	Consommable		2025-06-20 00:18:47.983546
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.employees (id, name, role, salaire_fixe, prime, is_active, created_at, notes) FROM stdin;
2	Rayan	production	40000.00	0.00	t	2025-06-15 01:58:21.728258	\N
1	Bara Yesmine	vendeur	30000.00	5000.00	t	2025-06-15 01:47:45.997165	\N
3	Saida	production	35000.00	0.00	t	2025-06-19 02:50:55.822561	
4	Fatiha	production	35000.00	0.00	t	2025-06-19 02:52:10.546081	
\.


--
-- Data for Name: order_employees; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.order_employees (order_id, employee_id, created_at) FROM stdin;
7	2	2025-06-15 22:54:39.37656
8	2	2025-06-19 02:40:59.833403
9	3	2025-06-19 02:52:44.604805
10	3	2025-06-24 00:51:22.936653
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.order_items (id, order_id, product_id, quantity, unit_price, created_at) FROM stdin;
1	2	5	20.000	0.00	2025-06-14 02:38:39.769107
2	2	5	30.000	0.00	2025-06-14 02:38:39.769114
3	4	5	10.000	80.00	2025-06-14 03:00:29.49519
4	5	5	20.000	0.00	2025-06-14 03:11:33.021779
5	5	5	20.000	0.00	2025-06-14 03:11:33.021786
6	6	1	20.000	0.00	2025-06-14 03:30:50.442776
7	6	5	10.000	0.00	2025-06-14 03:30:50.445675
8	7	5	2.000	80.00	2025-06-15 02:41:27.884168
9	8	13	2.000	100.00	2025-06-19 02:37:10.801188
10	8	1	5.000	70.00	2025-06-19 02:37:10.805146
11	9	13	20.000	0.00	2025-06-19 02:45:12.257311
12	9	1	20.000	0.00	2025-06-19 02:45:12.260153
13	10	13	10.000	0.00	2025-06-19 03:13:33.91187
14	10	5	20.000	0.00	2025-06-19 03:13:33.915146
15	10	1	20.000	0.00	2025-06-19 03:13:33.917172
16	11	1	10.000	0.00	2025-06-24 00:14:22.73474
17	11	5	5.000	0.00	2025-06-24 00:14:22.772279
18	12	15	10.000	100.00	2025-06-24 01:20:21.337207
19	13	13	10.000	100.00	2025-06-25 01:34:34.393902
20	14	1	5.000	0.00	2025-06-25 01:42:53.447446
21	15	15	20.000	100.00	2025-06-25 01:45:24.462184
22	16	15	10.000	0.00	2025-06-25 02:02:30.810851
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.orders (id, user_id, order_type, customer_name, customer_phone, customer_address, delivery_option, due_date, delivery_cost, status, notes, total_amount, created_at) FROM stdin;
5	1	counter_production_request	\N	\N	\N	pickup	2025-06-15 12:10:00	0.00	ready_at_shop		0.00	2025-06-14 03:11:33.014124
7	1	customer_order	Mr Harbi	0555242424		pickup	2025-06-15 10:40:00	0.00	delivered		160.00	2025-06-15 02:41:27.836076
4	1	customer_order	Mohamed LIF	0556246858	Cheraga	delivery	2025-06-20 13:05:00	200.00	delivered		1000.00	2025-06-14 03:00:29.48839
8	1	customer_order	M Bouchri	0558222222		pickup	2025-06-20 16:00:00	0.00	delivered		550.00	2025-06-19 02:37:10.750754
11	1	counter_production_request	\N	\N	\N	pickup	2025-06-25 13:00:00	0.00	in_production		0.00	2025-06-24 00:14:22.725288
2	1	counter_production_request	\N	\N	\N	pickup	2025-06-17 00:00:00	0.00	completed		0.00	2025-06-14 02:38:39.717227
10	1	counter_production_request	\N	\N	\N	pickup	2025-06-19 10:00:00	0.00	completed		0.00	2025-06-19 03:13:33.905346
6	1	counter_production_request	\N	\N	\N	pickup	2025-06-15 09:00:00	0.00	completed		0.00	2025-06-14 03:30:50.436568
9	1	counter_production_request	\N	\N	\N	pickup	2025-06-19 08:00:00	0.00	delivered		0.00	2025-06-19 02:45:12.254387
12	1	customer_order	Mr x	0556525252		pickup	2025-06-25 16:00:00	0.00	in_production		1000.00	2025-06-24 01:20:21.322208
13	1	customer_order	Dr Bousalah	0556252525		pickup	2025-06-25 13:00:00	0.00	in_production		1000.00	2025-06-25 01:34:34.387156
14	1	counter_production_request	\N	\N	\N	pickup	2025-06-26 13:00:00	0.00	in_production		0.00	2025-06-25 01:42:53.401777
15	1	customer_order	Dr XX	052222525		pickup	2025-06-26 13:01:00	0.00	pending		2000.00	2025-06-25 01:45:24.417416
16	1	counter_production_request	\N	\N	\N	pickup	2025-06-26 13:30:00	0.00	pending		0.00	2025-06-25 02:02:30.805648
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.products (id, name, product_type, description, price, cost_price, unit, sku, quantity_in_stock, category_id, created_at, stock_comptoir, stock_ingredients_local, stock_ingredients_magasin, stock_consommables, seuil_min_comptoir, seuil_min_ingredients_local, seuil_min_ingredients_magasin, seuil_min_consommables, last_stock_update, total_stock_value) FROM stdin;
11	Tomate Conserve	ingredient		\N	280.00	KG	TOMTCNSV	10	1	2025-06-19 02:27:05.041514	0	0	36000	0	0	0	0	0	2025-06-19 02:27:05.041525	0.0000
9	Farine	ingredient		\N	80.00	KG	FARN	10	1	2025-06-18 01:43:15.115481	0	20000	36000	0	0	0	0	0	2025-06-18 01:43:15.115493	0.0000
13	Mehadjeb grande taille	finished		100.00	\N	pièce	MHDJB	10	2	2025-06-19 02:31:15.537257	20	0	0	0	0	0	0	0	2025-06-19 02:52:44.597025	0.0000
1	Msamen Grand Taille	finished		70.00	\N	Pièce	MSMNG	30	2	2025-06-12 03:28:05.905087	20	0	0	0	0	0	0	0	2025-06-19 02:52:44.600086	0.0000
3	Semoule Fin	ingredient		\N	42.00	KG	SEMLFIN	25	1	2025-06-12 03:29:52.368304	0	0	501000	0	0	0	0	0	2025-06-16 02:12:24.560498	0.0000
14	Levure Chimique 	ingredient		\N	6.00	Pièce	LEVCHMQ	50	1	2025-06-24 00:19:43.414742	0	0	0	0	0	0	0	0	2025-06-24 00:19:43.414753	0.0000
15	Galette simple	finished		100.00	\N	Pièce	GLTSMP	10	3	2025-06-24 00:20:50.944842	0	0	0	0	0	0	0	0	2025-06-24 00:20:50.944875	0.0000
17	Produit Teste	ingredient		\N	0.10	G	TST1	1000	1	2025-06-26 00:04:11.513345	0	0	0	0	0	0	0	0	2025-06-26 00:04:11.513357	0.0000
2	Huile Civital	ingredient		\N	120.00	L	HUIL	12	1	2025-06-12 03:29:06.936089	0	0	100000	0	0	0	0	0	2025-06-16 02:12:24.560498	0.0000
4	Sel	ingredient		\N	25.00	KG	SEL	12	1	2025-06-12 03:30:21.535612	0	0	24000	0	0	0	0	0	2025-06-16 02:12:24.560498	0.0000
8	Harrissa	ingredient		\N	260.00	KG	HARSA	10	1	2025-06-18 01:42:23.014487	0	10000	10000	5000	0	0	0	0	2025-06-18 01:42:23.014498	0.0000
10	Oignon	ingredient		\N	50.00	KG	Oign	10	1	2025-06-19 02:24:49.585136	0	0	50000	0	0	0	0	0	2025-06-19 02:24:49.585177	0.0000
12	Paprika	ingredient		\N	1500.00	KG	AKRI	10	1	2025-06-19 02:29:27.671765	0	5000	3000	0	0	0	0	0	2025-06-19 02:29:27.671773	0.0000
6	Semoule Grosse	ingredient		\N	26.00	KG		10	1	2025-06-18 01:41:33.318091	0	0	67000	0	0	0	0	0	2025-06-18 01:41:33.318107	0.0000
5	Msamen Grand Taille 2	finished		80.00	\N	pièce	MSMNG2	0	2	2025-06-13 18:59:57.487407	0	0	0	0	0	0	0	0	2025-06-16 02:12:24.560498	0.0000
\.


--
-- Data for Name: purchase_items; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.purchase_items (id, purchase_id, product_id, quantity_ordered, quantity_received, unit_price, discount_percentage, stock_location, description_override, supplier_reference, notes, created_at, original_quantity, original_unit_id, original_unit_price, updated_at) FROM stdin;
1	1	8	10000.000	0.000	0.26	0.00	ingredients_magasin	10.0 × kg	\N	\N	2025-06-18 03:45:49.038322	10.000	12	260.00	2025-06-18 03:45:49.038328
2	1	2	50000.000	0.000	0.12	0.00	ingredients_magasin	10.0 × 5L	\N	\N	2025-06-18 03:45:49.085231	10.000	10	600.00	2025-06-18 03:45:49.085238
3	2	8	10000.000	0.000	0.26	0.00	ingredients_magasin	10.0 × kg	\N	\N	2025-06-18 03:46:23.289972	10.000	12	260.00	2025-06-18 03:46:23.289978
4	2	2	50000.000	0.000	0.12	0.00	ingredients_magasin	10.0 × 5L	\N	\N	2025-06-18 03:46:23.293357	10.000	10	600.00	2025-06-18 03:46:23.293363
5	3	8	10000.000	0.000	0.26	0.00	ingredients_magasin	10.0 × kg	\N	\N	2025-06-18 03:46:36.914527	10.000	12	260.00	2025-06-18 03:46:36.914533
6	3	2	50000.000	0.000	0.12	0.00	ingredients_magasin	10.0 × 5L	\N	\N	2025-06-18 03:46:36.917684	10.000	10	600.00	2025-06-18 03:46:36.91769
7	4	9	5000.000	0.000	0.50	0.00	ingredients_magasin	\N	\N	\N	2025-06-19 03:30:52.163459	\N	\N	\N	2025-06-19 03:30:52.163465
8	5	6	60000.000	0.000	0.10	0.00	ingredients_magasin	6.0 × 10kg	\N	\N	2025-06-19 04:04:08.783456	6.000	7	950.00	2025-06-19 04:04:08.783461
9	5	10	30000.000	0.000	0.05	0.00	ingredients_magasin	30.0 × kg	\N	\N	2025-06-19 04:04:08.791031	30.000	12	50.00	2025-06-19 04:04:08.791036
10	5	11	24000.000	0.000	0.28	0.00	ingredients_magasin	24.0 × kg	\N	\N	2025-06-19 04:04:08.791039	24.000	12	280.00	2025-06-19 04:04:08.791041
11	6	9	30000.000	0.000	0.08	0.00	ingredients_magasin	3.0 × 10kg	\N	\N	2025-06-20 02:28:07.316004	3.000	7	800.00	2025-06-20 02:28:07.31601
12	6	11	12000.000	0.000	0.28	0.00	ingredients_magasin	12.0 × kg	\N	\N	2025-06-20 02:28:07.361845	12.000	12	280.00	2025-06-20 02:28:07.361864
13	7	2	25000.000	0.000	0.12	0.00	ingredients_magasin	5.0 × 5L	\N	\N	2025-06-20 02:38:57.847277	5.000	10	600.00	2025-06-20 02:38:57.847283
14	7	3	250000.000	0.000	0.04	0.00	ingredients_magasin	10.0 × 25kg	\N	\N	2025-06-20 02:38:57.852575	10.000	8	1050.00	2025-06-20 02:38:57.852608
15	7	4	12000.000	0.000	0.03	0.00	ingredients_magasin	12.0 × kg	\N	\N	2025-06-20 02:38:57.855564	12.000	12	25.00	2025-06-20 02:38:57.855569
16	8	2	25000.000	0.000	0.12	0.00	ingredients_magasin	5.0 × 5L	\N	\N	2025-06-20 02:39:56.636427	5.000	10	600.00	2025-06-20 02:39:56.636435
17	8	3	250000.000	0.000	0.04	0.00	ingredients_magasin	10.0 × 25kg	\N	\N	2025-06-20 02:39:56.639741	10.000	8	1050.00	2025-06-20 02:39:56.639747
18	8	4	12000.000	0.000	0.03	0.00	ingredients_magasin	12.0 × kg	\N	\N	2025-06-20 02:39:56.64191	12.000	12	25.00	2025-06-20 02:39:56.641916
19	9	12	5000.000	0.000	1.50	0.00	ingredients_local	5.0 × kg	\N	\N	2025-06-20 02:52:48.937341	5.000	12	1500.00	2025-06-20 02:52:48.937347
20	9	8	5000.000	0.000	0.26	0.00	consommables	5.0 × kg	\N	\N	2025-06-20 02:52:48.93735	5.000	12	260.00	2025-06-20 02:52:48.937351
21	10	12	2000.000	0.000	1.50	0.00	ingredients_magasin	2.0 × kg	\N	\N	2025-06-20 03:05:13.796936	2.000	12	1500.00	2025-06-20 03:05:13.797076
22	11	9	20000.000	0.000	0.06	0.00	ingredients_local	2.0 × 10kg	\N	\N	2025-06-22 01:17:32.225442	2.000	7	580.00	2025-06-22 01:17:32.225448
23	12	8	10000.000	0.000	0.28	0.00	ingredients_local	10.0 × kg	\N	\N	2025-06-22 01:44:00.630813	10.000	12	280.00	2025-06-22 01:44:00.630819
24	13	10	20000.000	0.000	0.05	0.00	ingredients_magasin	20.0 × kg	\N	\N	2025-06-22 02:06:35.010544	20.000	12	50.00	2025-06-22 02:06:35.01055
25	14	6	2000.000	0.000	0.05	0.00	ingredients_magasin	1.0 × 2kg	\N	\N	2025-06-22 02:14:55.771345	1.000	4	100.00	2025-06-22 02:14:55.771351
26	15	12	1000.000	0.000	1.50	0.00	ingredients_magasin	1.0 × kg	\N	\N	2025-06-22 02:26:11.672348	1.000	12	1500.00	2025-06-22 02:26:11.672355
27	16	6	5000.000	0.000	0.07	0.00	ingredients_magasin	1.0 × 5kg	\N	\N	2025-06-22 02:39:40.848051	1.000	6	350.00	2025-06-22 02:39:40.848057
28	17	11	1000.000	0.000	0.26	0.00	ingredients_magasin	1.0 × kg	\N	\N	2025-06-22 03:28:58.291269	1.000	12	260.00	2025-06-22 03:28:58.291275
29	18	9	1000.000	0.000	0.25	0.00	ingredients_magasin	1.0 × kg	\N	\N	2025-06-22 03:48:11.758375	1.000	12	250.00	2025-06-22 03:48:11.75838
31	19	3	1000.000	0.000	0.04	0.00	ingredients_magasin	1.0 × kg	\N	\N	2025-06-23 01:14:08.960153	1.000	12	42.00	2025-06-23 01:14:08.960158
\.


--
-- Data for Name: purchases; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.purchases (id, reference, supplier_name, supplier_contact, supplier_phone, supplier_email, supplier_address, status, urgency, requested_by_id, approved_by_id, received_by_id, requested_date, approved_date, expected_delivery_date, received_date, subtotal_amount, tax_amount, shipping_cost, total_amount, notes, internal_notes, terms_conditions, payment_terms, default_stock_location, created_at, updated_at, is_paid, payment_date) FROM stdin;
19	BA2025-CF2F3B81	Halim					RECEIVED	NORMAL	1	\N	\N	2025-06-01 00:42:00	\N	\N	\N	40.00	0.00	0.00	40.00		\N	\N	\N	ingredients_magasin	2025-06-23 00:43:13.628319	2025-06-23 01:14:08.957061	\N	\N
3	BA2025-EE60792E	Morad	\N	\N	\N	\N	REQUESTED	NORMAL	1	\N	\N	2025-06-18 03:46:36.911234	\N	\N	\N	8600.00	0.00	0.00	8600.00		\N	\N	\N	ingredients_magasin	2025-06-18 03:46:36.911241	2025-06-19 02:55:05.054793	\N	\N
2	BA2025-D489D8E3	Morad	\N	\N	\N	\N	DRAFT	NORMAL	1	\N	\N	2025-06-18 03:46:23.285474	\N	\N	\N	8600.00	0.00	0.00	8600.00		\N	\N	\N	ingredients_magasin	2025-06-18 03:46:23.285481	2025-06-19 02:55:57.619106	\N	\N
4	BA2025-18E95C4E	Test Fournisseur Automatique	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-19 03:30:52.139141	\N	\N	\N	0.00	0.00	0.00	0.00	\N	\N	\N	\N	ingredients_magasin	2025-06-19 03:30:52.13915	2025-06-19 03:30:52.139153	\N	\N
5	BA2025-DFB630D0	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-19 04:04:08.777545	\N	\N	\N	14220.00	0.00	0.00	14220.00		\N	\N	\N	ingredients_magasin	2025-06-19 04:04:08.777556	2025-06-19 04:04:50.568041	\N	\N
1	BA2025-0BEF929F	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-18 03:45:48.990233	\N	\N	\N	8600.00	0.00	0.00	8600.00		\N	\N	\N	ingredients_magasin	2025-06-18 03:45:48.990244	2025-06-19 04:05:29.691022	\N	\N
6	BA2025-1D14779D	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-20 02:28:07.22727	\N	\N	\N	5760.00	0.00	0.00	5760.00		\N	\N	\N	ingredients_magasin	2025-06-20 02:28:07.227282	2025-06-20 02:28:19.352206	\N	\N
7	BA2025-21EDC591	Civital	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-20 02:38:57.838392	\N	\N	\N	13300.00	0.00	0.00	13300.00		\N	\N	\N	ingredients_magasin	2025-06-20 02:38:57.838402	2025-06-20 02:38:57.860734	\N	\N
8	BA2025-AEE5D7D6	Civital	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-20 02:39:56.63243	\N	\N	\N	13300.00	0.00	0.00	13300.00		\N	\N	\N	ingredients_magasin	2025-06-20 02:39:56.632435	2025-06-20 02:39:56.644398	\N	\N
9	BA2025-6B28C231	Bilel	\N	\N	\N	\N	RECEIVED	HIGH	1	\N	\N	2025-06-20 02:52:48.928481	\N	\N	\N	8800.00	0.00	0.00	8800.00		\N	\N	\N	ingredients_magasin	2025-06-20 02:52:48.928493	2025-06-20 02:53:19.565577	\N	\N
10	BA2025-5918EFE1	Omar	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-20 04:05:13.783907	\N	\N	\N	3000.00	0.00	0.00	3000.00		\N	\N	\N	ingredients_magasin	2025-06-20 03:05:13.788139	2025-06-20 03:06:02.009572	\N	\N
11	BA2025-9F77B590	Amine	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-22 02:17:32.107198	\N	\N	\N	1160.00	0.00	0.00	1160.00		\N	\N	\N	ingredients_magasin	2025-06-22 01:17:32.11236	2025-06-22 01:42:13.145868	\N	\N
12	BA2025-ED622188	Sofiane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-22 02:44:00.62736	\N	\N	\N	2800.00	0.00	0.00	2800.00		\N	\N	\N	ingredients_magasin	2025-06-22 01:44:00.628002	2025-06-22 01:55:43.567104	\N	\N
13	BA2025-7E0AEA0F	Slimane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-22 03:06:34.995997	\N	\N	\N	1000.00	0.00	0.00	1000.00		\N	\N	\N	ingredients_magasin	2025-06-22 02:06:35.0015	2025-06-22 02:06:35.017363	\N	\N
14	BA2025-159E9222	Hakim	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-22 03:14:55.761046	\N	\N	\N	100.00	0.00	0.00	100.00		\N	\N	\N	ingredients_magasin	2025-06-22 02:14:55.76491	2025-06-22 02:14:55.776176	\N	\N
15	BA2025-0BC08675	Brahim	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-22 03:26:11.66206	\N	\N	\N	1500.00	0.00	0.00	1500.00		\N	\N	\N	ingredients_magasin	2025-06-22 02:26:11.666039	2025-06-22 02:26:11.67735	\N	\N
16	BA2025-C1B475E5	Hamza	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-22 02:39:40.743252	\N	\N	\N	350.00	0.00	0.00	350.00		\N	\N	\N	ingredients_magasin	2025-06-22 02:39:40.795746	2025-06-22 02:39:40.852573	\N	\N
17	BA2025-69A54E63	Samir	\N	\N	\N	\N	CANCELLED	NORMAL	1	\N	\N	2025-06-01 03:28:00	\N	\N	\N	260.00	0.00	0.00	260.00		\N	\N	\N	ingredients_magasin	2025-06-22 03:28:58.28631	2025-06-22 03:47:04.680095	\N	\N
18	BA2025-24EC841C	Sofiane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-02 03:47:00	\N	\N	\N	250.00	0.00	0.00	250.00		\N	\N	\N	ingredients_magasin	2025-06-22 03:48:11.753735	2025-06-22 03:48:11.761667	\N	\N
\.


--
-- Data for Name: recipe_ingredients; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.recipe_ingredients (id, recipe_id, product_id, quantity_needed, unit, notes, created_at) FROM stdin;
1	3	3	8000.000	G	\N	2025-06-25 23:09:09.611116
2	3	4	150.000	G	\N	2025-06-25 23:09:09.611128
3	3	2	1500.000	ML	\N	2025-06-25 23:09:09.61113
\.


--
-- Data for Name: recipes; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.recipes (id, name, description, product_id, yield_quantity, yield_unit, preparation_time, cooking_time, difficulty_level, created_at, production_location) FROM stdin;
2	MSGT2		5	112	pièces	\N	\N	\N	2025-06-13 19:00:49.524766	ingredients_magasin
3	MSGT		1	112	pièces	\N	\N	\N	2025-06-13 19:14:39.601269	ingredients_magasin
4	MHADJEBGT		13	112	pièces	\N	\N	\N	2025-06-19 02:34:26.181446	ingredients_magasin
5	Galette simple		15	12	pièces	\N	\N	\N	2025-06-24 00:24:58.687602	ingredients_magasin
\.


--
-- Data for Name: stock_movements; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.stock_movements (id, reference, product_id, stock_location, movement_type, quantity, unit_cost, total_value, stock_before, stock_after, order_id, transfer_id, user_id, reason, notes, created_at) FROM stdin;
\.


--
-- Data for Name: stock_transfer_lines; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.stock_transfer_lines (id, transfer_id, product_id, quantity_requested, quantity_approved, quantity_transferred, unit_cost, notes, created_at) FROM stdin;
\.


--
-- Data for Name: stock_transfers; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.stock_transfers (id, reference, source_location, destination_location, status, requested_by_id, approved_by_id, completed_by_id, requested_date, approved_date, scheduled_date, completed_date, reason, notes, priority) FROM stdin;
\.


--
-- Data for Name: units; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.units (id, name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at) FROM stdin;
1	250g	g	250.000	weight	1	t	2025-06-18 02:08:21.760421
2	500g	g	500.000	weight	2	t	2025-06-18 02:08:21.760429
3	1.8kg	g	1800.000	weight	3	t	2025-06-18 02:08:21.760431
4	2kg	g	2000.000	weight	4	t	2025-06-18 02:08:21.760433
5	3.8kg	g	3800.000	weight	5	t	2025-06-18 02:08:21.760434
6	5kg	g	5000.000	weight	6	t	2025-06-18 02:08:21.760436
7	10kg	g	10000.000	weight	7	t	2025-06-18 02:08:21.760437
8	25kg	g	25000.000	weight	8	t	2025-06-18 02:08:21.760438
9	2L	ml	2000.000	volume	9	t	2025-06-18 02:08:21.76044
10	5L	ml	5000.000	volume	10	t	2025-06-18 02:08:21.760441
11	g	g	1.000	weight	100	t	2025-06-18 02:21:56.730218
12	kg	g	1000.000	weight	101	t	2025-06-18 02:21:56.732513
13	ml	ml	1.000	volume	102	t	2025-06-18 02:21:56.733944
14	L	ml	1000.000	volume	103	t	2025-06-18 02:21:56.735716
15	Pièce	piece	1.000	count	104	t	2025-06-18 02:21:56.737549
16	unité	piece	1.000	count	105	t	2025-06-18 02:21:56.738721
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.users (id, username, email, password_hash, role, created_at) FROM stdin;
1	admin	admin@example.com	scrypt:32768:8:1$OEPzqJTeTSzTg2wh$bf77a339301f5993f93b4f3a16f1d56f9425ef0d6475badb38a1b7a96ed302fc6832721f4e54252742b71c87f8b5c6138f891a0f0fea0d15f3da88a501201988	admin	2025-06-11 03:27:09.437909
\.


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.categories_id_seq', 4, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.employees_id_seq', 4, true);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.order_items_id_seq', 22, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.orders_id_seq', 16, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.products_id_seq', 17, true);


--
-- Name: purchase_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.purchase_items_id_seq', 31, true);


--
-- Name: purchases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.purchases_id_seq', 19, true);


--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.recipe_ingredients_id_seq', 3, true);


--
-- Name: recipes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.recipes_id_seq', 5, true);


--
-- Name: stock_movements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.stock_movements_id_seq', 1, false);


--
-- Name: stock_transfer_lines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.stock_transfer_lines_id_seq', 1, false);


--
-- Name: stock_transfers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.stock_transfers_id_seq', 1, false);


--
-- Name: units_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.units_id_seq', 16, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: order_employees order_employees_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_employees
    ADD CONSTRAINT order_employees_pkey PRIMARY KEY (order_id, employee_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_sku_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_sku_key UNIQUE (sku);


--
-- Name: purchase_items purchase_items_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_pkey PRIMARY KEY (id);


--
-- Name: purchases purchases_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_pkey PRIMARY KEY (id);


--
-- Name: purchases purchases_reference_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_reference_key UNIQUE (reference);


--
-- Name: recipe_ingredients recipe_ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_product_id_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_product_id_key UNIQUE (product_id);


--
-- Name: stock_movements stock_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_pkey PRIMARY KEY (id);


--
-- Name: stock_movements stock_movements_reference_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_reference_key UNIQUE (reference);


--
-- Name: stock_transfer_lines stock_transfer_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines
    ADD CONSTRAINT stock_transfer_lines_pkey PRIMARY KEY (id);


--
-- Name: stock_transfers stock_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_pkey PRIMARY KEY (id);


--
-- Name: stock_transfers stock_transfers_reference_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_reference_key UNIQUE (reference);


--
-- Name: units units_name_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_name_key UNIQUE (name);


--
-- Name: units units_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: ix_orders_status; Type: INDEX; Schema: public; Owner: fee_maison_user
--

CREATE INDEX ix_orders_status ON public.orders USING btree (status);


--
-- Name: ix_products_name; Type: INDEX; Schema: public; Owner: fee_maison_user
--

CREATE INDEX ix_products_name ON public.products USING btree (name);


--
-- Name: order_employees order_employees_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_employees
    ADD CONSTRAINT order_employees_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: order_employees order_employees_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_employees
    ADD CONSTRAINT order_employees_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: purchase_items purchase_items_original_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_original_unit_id_fkey FOREIGN KEY (original_unit_id) REFERENCES public.units(id);


--
-- Name: purchase_items purchase_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: purchase_items purchase_items_purchase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES public.purchases(id);


--
-- Name: purchases purchases_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: purchases purchases_received_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_received_by_id_fkey FOREIGN KEY (received_by_id) REFERENCES public.users(id);


--
-- Name: purchases purchases_requested_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_requested_by_id_fkey FOREIGN KEY (requested_by_id) REFERENCES public.users(id);


--
-- Name: recipe_ingredients recipe_ingredients_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: recipe_ingredients recipe_ingredients_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: recipes recipes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: stock_movements stock_movements_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: stock_movements stock_movements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: stock_movements stock_movements_transfer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_transfer_id_fkey FOREIGN KEY (transfer_id) REFERENCES public.stock_transfers(id);


--
-- Name: stock_movements stock_movements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: stock_transfer_lines stock_transfer_lines_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines
    ADD CONSTRAINT stock_transfer_lines_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: stock_transfer_lines stock_transfer_lines_transfer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines
    ADD CONSTRAINT stock_transfer_lines_transfer_id_fkey FOREIGN KEY (transfer_id) REFERENCES public.stock_transfers(id);


--
-- Name: stock_transfers stock_transfers_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: stock_transfers stock_transfers_completed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_completed_by_id_fkey FOREIGN KEY (completed_by_id) REFERENCES public.users(id);


--
-- Name: stock_transfers stock_transfers_requested_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_requested_by_id_fkey FOREIGN KEY (requested_by_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

