/**
 * @file fips_provider.h
 * @brief FIPS Provider header - Infrastructure Layer
 * 
 * This header defines the FIPS provider interface
 * following DDD principles. This layer handles external concerns like
 * FIPS compliance validation and external service integrations.
 * 
 * Layer: Infrastructure (Providers) - External Concerns
 * Dependencies: Implements interfaces defined in domain/application layers
 */

#ifndef FIPS_PROVIDER_H
#define FIPS_PROVIDER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief FIPS operation results
 */
typedef enum {
    FIPS_SUCCESS = 0,
    FIPS_ERROR_INVALID_PARAM = -1,
    FIPS_ERROR_SELFTEST_FAILED = -2,
    FIPS_ERROR_SELFTEST_NOT_PASSED = -3,
    FIPS_ERROR_ALGORITHM_NOT_APPROVED = -4,
    FIPS_ERROR_INTEGRITY_CHECK_FAILED = -5,
    FIPS_ERROR_MEMORY_ALLOCATION = -6
} fips_result_t;

/**
 * @brief FIPS self-test status
 */
typedef enum {
    FIPS_SELFTEST_NOT_RUN,
    FIPS_SELFTEST_PASSED,
    FIPS_SELFTEST_FAILED
} fips_selftest_status_t;

/**
 * @brief FIPS module information structure
 */
typedef struct {
    uint8_t module_id[16];
    uint8_t module_version[4];
    char module_name[64];
    char certificate_number[32];
    uint8_t integrity_value[32];
} fips_module_info_t;

/**
 * @brief FIPS provider context structure (opaque)
 */
typedef struct fips_provider_context fips_provider_context_t;

/**
 * @brief Initialize FIPS provider
 * 
 * @param ctx FIPS provider context to initialize
 * @return fips_result_t Operation result
 */
fips_result_t fips_provider_init(fips_provider_context_t *ctx);

/**
 * @brief Check if algorithm is FIPS approved
 * 
 * @param algorithm_name Name of the algorithm to check
 * @return fips_result_t FIPS_SUCCESS if approved, error code otherwise
 */
fips_result_t fips_is_algorithm_approved(const char *algorithm_name);

/**
 * @brief Get FIPS module information
 * 
 * @param ctx FIPS provider context
 * @param info Structure to fill with module information
 * @return fips_result_t Operation result
 */
fips_result_t fips_get_module_info(fips_provider_context_t *ctx, fips_module_info_t *info);

/**
 * @brief Verify module integrity
 * 
 * @param ctx FIPS provider context
 * @return fips_result_t Operation result
 */
fips_result_t fips_verify_module_integrity(fips_provider_context_t *ctx);

/**
 * @brief Run continuous self-test
 * 
 * @param ctx FIPS provider context
 * @return fips_result_t Operation result
 */
fips_result_t fips_run_continuous_selftest(fips_provider_context_t *ctx);

/**
 * @brief Get self-test status
 * 
 * @param ctx FIPS provider context
 * @return fips_selftest_status_t Current self-test status
 */
fips_selftest_status_t fips_get_selftest_status(fips_provider_context_t *ctx);

/**
 * @brief Clean up FIPS provider
 * 
 * @param ctx FIPS provider context to clean up
 */
void fips_provider_cleanup(fips_provider_context_t *ctx);

#ifdef __cplusplus
}
#endif

#endif // FIPS_PROVIDER_H