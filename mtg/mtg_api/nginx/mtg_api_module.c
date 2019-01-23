#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>

#include "mtg_api.h"

typedef struct {
	ngx_str_t path_cards;
	ngx_str_t path_name_to_tags;
	ngx_str_t path_sets;
	ngx_str_t path_tags;
} UNIQUE_global_configuration;

static void *pointer_from_cpp = 0;

static char content_type_json[] = "application/json; charset=utf-8";

void *allocate_passed_to_cpp(void *cb_data, size_t size) {
	return ngx_palloc((struct ngx_pool_s *)cb_data, size);
}

void log_passed_to_cpp(void *log_cb_data, char const *string) {
	ngx_log_error(NGX_LOG_ERR, (ngx_log_t *)log_cb_data, 0,  string);
}

static ngx_int_t ngx_http_UNIQUE_generic_handler(ngx_http_request_t *r, cpp_api_function cpp_api) {
	ngx_chain_t out;
	interface_from_c_to_cpp_t interface = {
		.allocator = {
			.allocate = allocate_passed_to_cpp,
			.data = r->pool
		},
		.logger = {
			.log = log_passed_to_cpp,
			.data = r->connection->log
		}
	};
	bytes_view api_response = cpp_api(pointer_from_cpp, &interface, r->args.data, r->args.len);

	r->headers_out.content_type.len = sizeof(content_type_json) - 1;
	r->headers_out.content_type.data = (u_char *) content_type_json;

	if (api_response.data == NULL) {
		ngx_log_error(NGX_LOG_ERR, r->connection->log, 0,  "Failed to generate response.");
		return NGX_HTTP_INTERNAL_SERVER_ERROR;
	}

	ngx_log_error(NGX_LOG_CRIT, r->connection->log, 0,  "Generated response."); //TODO

	ngx_buf_t * const b = ngx_pcalloc(r->pool, sizeof(ngx_buf_t));
	if (b == NULL) {
		ngx_log_error(NGX_LOG_ERR, r->connection->log, 0,  "Failed to allocate response buffer.");
		return NGX_HTTP_INTERNAL_SERVER_ERROR;
	}

	out.buf = b;
	out.next = NULL;

	b->pos = api_response.data; /* first position in memory of the data */
	b->last = api_response.data + api_response.size; /* last position in memory of the data */
	b->memory = 1; /* content is in read-only memory */
	b->last_buf = 1; /* there will be no more buffers in the request */

	r->headers_out.status = NGX_HTTP_OK;
	r->headers_out.content_length_n = api_response.size;
	{
		ngx_int_t rc = ngx_http_send_header(r);
		if (rc == NGX_ERROR || rc > NGX_OK || r->header_only) {
			return rc;
		}
	}

	return ngx_http_output_filter(r, &out); /* Send the body, and return the status code of the output filter chain. */
}

static char *register_location_content_handler(ngx_conf_t *cf, ngx_command_t *cmd, void *conf, ngx_http_handler_pt handler) {
	ngx_http_core_loc_conf_t *clcf = ngx_http_conf_get_module_loc_conf(cf, ngx_http_core_module);
	clcf->handler = handler;
	return NGX_CONF_OK;
}

#define REGISTER_HANDLER(config_function, cpp_function) \
static ngx_int_t config_function ## handler(ngx_http_request_t *r) { \
	return ngx_http_UNIQUE_generic_handler(r, cpp_function); \
} \
static char *config_function(ngx_conf_t *cf, ngx_command_t *cmd, void *conf) { \
	return register_location_content_handler(cf, cmd, conf, config_function ## handler); \
}

REGISTER_HANDLER(mtg_api_info, mtg_api_f1)
REGISTER_HANDLER(mtg_api_query, mtg_api_f2)

static ngx_command_t ngx_http_UNIQUE_commands[] = {
	{
		ngx_string("mtg_api_path_cards"),
		NGX_HTTP_MAIN_CONF|NGX_CONF_TAKE1,
		ngx_conf_set_str_slot,
		NGX_HTTP_MAIN_CONF_OFFSET,
		offsetof(UNIQUE_global_configuration, path_cards),
		NULL
	},
	{
		ngx_string("mtg_api_path_name_to_tags"),
		NGX_HTTP_MAIN_CONF|NGX_CONF_TAKE1,
		ngx_conf_set_str_slot,
		NGX_HTTP_MAIN_CONF_OFFSET,
		offsetof(UNIQUE_global_configuration, path_name_to_tags),
		NULL
	},
	{
		ngx_string("mtg_api_path_sets"),
		NGX_HTTP_MAIN_CONF|NGX_CONF_TAKE1,
		ngx_conf_set_str_slot,
		NGX_HTTP_MAIN_CONF_OFFSET,
		offsetof(UNIQUE_global_configuration, path_sets),
		NULL
	},
	{
		ngx_string("mtg_api_path_tags"),
		NGX_HTTP_MAIN_CONF|NGX_CONF_TAKE1,
		ngx_conf_set_str_slot,
		NGX_HTTP_MAIN_CONF_OFFSET,
		offsetof(UNIQUE_global_configuration, path_tags),
		NULL
	},
	{
		ngx_string("mtg_api_query"),
		NGX_HTTP_LOC_CONF|NGX_CONF_NOARGS,
		mtg_api_query,
		0, /* No offset. Only one context is supported. */
		0, /* No offset when storing the module configuration on struct. */
		NULL
	},
	{
		ngx_string("mtg_api_info"),
		NGX_HTTP_LOC_CONF|NGX_CONF_NOARGS,
		mtg_api_info,
		0, /* No offset. Only one context is supported. */
		0, /* No offset when storing the module configuration on struct. */
		NULL
	},
	ngx_null_command
};

static ngx_int_t ngx_http_UNIQUE_init(ngx_conf_t *cf);
static void *ngx_http_UNIQUE_create_main_conf(ngx_conf_t *cf);
static void *ngx_http_UNIQUE_create_loc_conf(ngx_conf_t *cf); //unused
static char *ngx_http_UNIQUE_merge_loc_conf(ngx_conf_t *cf, void *parent, void *child); // unused

static ngx_http_module_t ngx_http_UNIQUE_module_ctx = {
	NULL, /* preconfiguration */
	ngx_http_UNIQUE_init, /* postconfiguration */

	ngx_http_UNIQUE_create_main_conf, /* create main */
	NULL, /* init main configuration */

	NULL, /* create server configuration */
	NULL, /* merge server configuration */

	NULL, //ngx_http_UNIQUE_create_loc_conf,
	NULL, //ngx_http_UNIQUE_merge_loc_conf
};

static ngx_int_t ngx_http_UNIQUE_process_init(ngx_cycle_t *cycle);
static void ngx_http_UNIQUE_process_exit(ngx_cycle_t *cycle);

ngx_module_t mtg_api_module = {
	NGX_MODULE_V1,
	&ngx_http_UNIQUE_module_ctx,
	ngx_http_UNIQUE_commands,
	NGX_HTTP_MODULE,
	NULL, /* init master */
	NULL, /* init module */
	ngx_http_UNIQUE_process_init,
	NULL, /* init thread */
	NULL, /* exit thread */
	ngx_http_UNIQUE_process_exit,
	NULL, /* exit master */
	NGX_MODULE_V1_PADDING
};

static ngx_int_t ngx_http_UNIQUE_init(ngx_conf_t *cf) {
	return NGX_OK;
}

static void *ngx_http_UNIQUE_create_main_conf(ngx_conf_t *cf) {
	ngx_log_error(NGX_LOG_CRIT, cf->log, 0, "create main");
	UNIQUE_global_configuration * const c = ngx_pcalloc(cf->pool, sizeof(UNIQUE_global_configuration));
	if (c == NULL) {
		return NGX_CONF_ERROR;
	}

	ngx_str_null(&c->path_cards);
	ngx_str_null(&c->path_name_to_tags);
	ngx_str_null(&c->path_sets);
	ngx_str_null(&c->path_tags);

	return c;
}

static void *ngx_http_UNIQUE_create_loc_conf(ngx_conf_t *cf) {
	return NULL;
}

static char *ngx_http_UNIQUE_merge_loc_conf(ngx_conf_t *cf, void *parent, void *child) {
	return NGX_CONF_OK;
}

static ngx_int_t ngx_http_UNIQUE_process_init(ngx_cycle_t *cycle) {
	ngx_log_error(NGX_LOG_INFO, cycle->log, 0, "mtg_api process_init");

	if (ngx_process != NGX_PROCESS_WORKER && ngx_process != NGX_PROCESS_SINGLE) {
		ngx_log_error(NGX_LOG_ERR, cycle->log, 0, "mtg_api only supports one process setup");
		return NGX_OK;
	}

	ngx_http_conf_ctx_t * const ctx = (ngx_http_conf_ctx_t *)ngx_get_conf(cycle->conf_ctx, ngx_http_module);
	UNIQUE_global_configuration * const c =  ngx_http_get_module_main_conf(ctx, mtg_api_module);

	mtg_api_args args;
	args.path_cards = c->path_cards.data;
	args.path_name_to_tags = c->path_name_to_tags.data;
	args.path_sets = c->path_sets.data;
	args.path_tags = c->path_tags.data;

	interface_from_c_to_cpp_t interface = {
		.allocator = {
			.allocate = allocate_passed_to_cpp,
			.data = cycle->pool
		},
		.logger = {
			.log = log_passed_to_cpp,
			.data = cycle->log
		}
	};

	pointer_from_cpp = construct(&interface, &args);
	if (pointer_from_cpp) {
		return NGX_OK;
	}

	ngx_log_error(NGX_LOG_ERR, cycle->log, 0,  "process init failed");
	return NGX_ERROR;
}

static void ngx_http_UNIQUE_process_exit(ngx_cycle_t *cycle) {
	ngx_log_error(NGX_LOG_CRIT, cycle->log, 0,  "process exit");
	destroy(pointer_from_cpp);
}
