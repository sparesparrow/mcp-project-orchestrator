/**
 * @file openssl_cli.h
 * @brief OpenSSL CLI header - Presentation Layer
 * 
 * This header defines the OpenSSL CLI interface
 * following DDD principles. This layer translates external requests
 * to application calls without containing business logic.
 * 
 * Layer: Presentation (Apps) - User Interface
 * Dependencies: Application layer interfaces, no business logic
 */

#ifndef OPENSSL_CLI_H
#define OPENSSL_CLI_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief OpenSSL CLI context structure (opaque)
 */
typedef struct openssl_cli_context openssl_cli_context_t;

/**
 * @brief Main OpenSSL CLI function
 * 
 * @param argc Argument count
 * @param argv Argument vector
 * @return int Exit code (0 for success, non-zero for error)
 */
int openssl_cli_main(int argc, char *argv[]);

/**
 * @brief Clean up CLI context
 * 
 * @param ctx CLI context to clean up
 */
void openssl_cli_cleanup(openssl_cli_context_t *ctx);

#ifdef __cplusplus
}
#endif

#endif // OPENSSL_CLI_H