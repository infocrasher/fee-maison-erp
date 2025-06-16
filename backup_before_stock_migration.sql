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
    created_at timestamp without time zone
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
    created_at timestamp without time zone
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
-- Name: recipe_ingredients id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients ALTER COLUMN id SET DEFAULT nextval('public.recipe_ingredients_id_seq'::regclass);


--
-- Name: recipes id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes ALTER COLUMN id SET DEFAULT nextval('public.recipes_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.alembic_version (version_num) FROM stdin;
9a043041c254
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.categories (id, name, description, created_at) FROM stdin;
1	Ingrédients		2025-06-12 01:27:09.229977
2	Salés		2025-06-12 03:24:09.875163
3	pates		2025-06-13 22:35:20.371224
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.employees (id, name, role, salaire_fixe, prime, is_active, created_at, notes) FROM stdin;
2	Rayan	production	40000.00	0.00	t	2025-06-15 01:58:21.728258	
1	Bara Yesmine	vendeur	30000.00	5000.00	t	2025-06-15 01:47:45.997165	
\.


--
-- Data for Name: order_employees; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.order_employees (order_id, employee_id, created_at) FROM stdin;
7	2	2025-06-15 22:54:39.37656
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
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.orders (id, user_id, order_type, customer_name, customer_phone, customer_address, delivery_option, due_date, delivery_cost, status, notes, total_amount, created_at) FROM stdin;
2	1	counter_production_request	\N	\N	\N	pickup	2025-06-17 00:00:00	0.00	ready_at_shop		0.00	2025-06-14 02:38:39.717227
5	1	counter_production_request	\N	\N	\N	pickup	2025-06-15 12:10:00	0.00	ready_at_shop		0.00	2025-06-14 03:11:33.014124
7	1	customer_order	Mr Harbi	0555242424		pickup	2025-06-15 10:40:00	0.00	delivered		160.00	2025-06-15 02:41:27.836076
6	1	counter_production_request	\N	\N	\N	pickup	2025-06-15 09:00:00	0.00	ready_at_shop		0.00	2025-06-14 03:30:50.436568
4	1	customer_order	Mohamed LIF	0556246858	Cheraga	delivery	2025-06-20 13:05:00	200.00	delivered		1000.00	2025-06-14 03:00:29.48839
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.products (id, name, product_type, description, price, cost_price, unit, sku, quantity_in_stock, category_id, created_at) FROM stdin;
3	Semoule Fin	ingredient		\N	42.00	KG	SEMLFIN	25	1	2025-06-12 03:29:52.368304
4	Sel	ingredient		\N	25.00	KG	SEL	12	1	2025-06-12 03:30:21.535612
2	Huile Civital	ingredient		\N	120.00	L	HUIL	12	1	2025-06-12 03:29:06.936089
1	Msamen Grand Taille	finished		70.00	\N	Pièce	MSMNG	30	2	2025-06-12 03:28:05.905087
5	Msamen Grand Taille 2	finished		80.00	\N	pièce	MSMNG2	0	2	2025-06-13 18:59:57.487407
\.


--
-- Data for Name: recipe_ingredients; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.recipe_ingredients (id, recipe_id, product_id, quantity_needed, unit, notes, created_at) FROM stdin;
4	2	2	1500.000	ML	\N	2025-06-13 19:00:49.527519
5	2	4	150.000	G	\N	2025-06-13 19:00:49.527524
6	2	3	8000.000	G	\N	2025-06-13 19:00:49.527527
7	3	2	1500.000	ML	\N	2025-06-13 19:14:39.606831
8	3	4	150.000	G	\N	2025-06-13 19:14:39.606869
9	3	3	8000.000	G	\N	2025-06-13 19:14:39.606876
\.


--
-- Data for Name: recipes; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.recipes (id, name, description, product_id, yield_quantity, yield_unit, preparation_time, cooking_time, difficulty_level, created_at) FROM stdin;
2	MSGT2		5	112	pièces	\N	\N	\N	2025-06-13 19:00:49.524766
3	MSGT		1	112	pièces	\N	\N	\N	2025-06-13 19:14:39.601269
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

SELECT pg_catalog.setval('public.categories_id_seq', 3, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.employees_id_seq', 2, true);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.order_items_id_seq', 8, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.orders_id_seq', 7, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.products_id_seq', 5, true);


--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.recipe_ingredients_id_seq', 9, true);


--
-- Name: recipes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.recipes_id_seq', 3, true);


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
-- PostgreSQL database dump complete
--

