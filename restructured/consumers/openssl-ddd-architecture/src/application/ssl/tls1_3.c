/**
 * @file tls1_3.c
 * @brief TLS 1.3 protocol implementation - Application Layer
 * 
 * This file contains the TLS 1.3 protocol state machine and orchestration
 * following DDD principles. This layer orchestrates domain objects to fulfill
 * business requirements without implementing crypto algorithms directly.
 * 
 * Layer: Application (SSL/TLS) - Use Case Orchestration
 * Dependencies: Domain layer interfaces, no crypto implementation
 */

#include "tls1_3.h"
#include "../domain/crypto/aes.h"
#include "../domain/crypto/sha256.h"
#include "../domain/crypto/rsa.h"
#include "../domain/crypto/ec.h"
#include <string.h>
#include <stdint.h>

/**
 * @brief TLS 1.3 handshake state machine
 */
typedef enum {
    TLS_STATE_CLIENT_HELLO,
    TLS_STATE_SERVER_HELLO,
    TLS_STATE_CHANGE_CIPHER_SPEC,
    TLS_STATE_FINISHED,
    TLS_STATE_APPLICATION_DATA,
    TLS_STATE_ERROR
} tls_handshake_state_t;

/**
 * @brief TLS 1.3 context structure
 */
typedef struct {
    tls_handshake_state_t state;
    uint8_t client_random[32];
    uint8_t server_random[32];
    uint8_t master_secret[48];
    uint8_t client_write_key[32];
    uint8_t server_write_key[32];
    uint8_t client_write_iv[12];
    uint8_t server_write_iv[12];
    aes_context_t *aes_ctx;
    sha256_context_t *sha256_ctx;
    rsa_context_t *rsa_ctx;
    ec_context_t *ec_ctx;
    uint64_t sequence_number;
    uint8_t handshake_hash[32];
} tls1_3_context_t;

/**
 * @brief TLS 1.3 handshake message types
 */
typedef enum {
    TLS_MSG_CLIENT_HELLO = 1,
    TLS_MSG_SERVER_HELLO = 2,
    TLS_MSG_CHANGE_CIPHER_SPEC = 20,
    TLS_MSG_FINISHED = 20
} tls_handshake_msg_type_t;

/**
 * @brief TLS 1.3 cipher suites
 */
typedef enum {
    TLS_CIPHER_SUITE_AES_128_GCM_SHA256 = 0x1301,
    TLS_CIPHER_SUITE_AES_256_GCM_SHA384 = 0x1302,
    TLS_CIPHER_SUITE_CHACHA20_POLY1305_SHA256 = 0x1303
} tls_cipher_suite_t;

/**
 * @brief TLS 1.3 supported groups
 */
typedef enum {
    TLS_GROUP_X25519 = 0x001d,
    TLS_GROUP_SECP256R1 = 0x0017,
    TLS_GROUP_SECP384R1 = 0x0018
} tls_supported_group_t;

/**
 * @brief Generate client random
 */
static tls_result_t tls_generate_client_random(tls1_3_context_t *ctx) {
    // In real implementation, this would use a cryptographically secure RNG
    // For DDD demonstration, we'll use a simple approach
    for (int i = 0; i < 32; i++) {
        ctx->client_random[i] = (uint8_t)(i * 7 + 13); // Simple PRNG for demo
    }
    return TLS_SUCCESS;
}

/**
 * @brief Generate server random
 */
static tls_result_t tls_generate_server_random(tls1_3_context_t *ctx) {
    // In real implementation, this would use a cryptographically secure RNG
    for (int i = 0; i < 32; i++) {
        ctx->server_random[i] = (uint8_t)(i * 11 + 17); // Simple PRNG for demo
    }
    return TLS_SUCCESS;
}

/**
 * @brief Derive master secret using HKDF
 */
static tls_result_t tls_derive_master_secret(tls1_3_context_t *ctx, 
                                           const uint8_t *shared_secret, 
                                           size_t shared_secret_len) {
    // In real implementation, this would use HKDF
    // For DDD demonstration, we'll use a simple approach
    uint8_t salt[] = "TLS 1.3, server to client";
    uint8_t info[] = "tls13 derived";
    
    // Simple key derivation for demo (not cryptographically secure)
    for (int i = 0; i < 48; i++) {
        ctx->master_secret[i] = (uint8_t)((salt[i % sizeof(salt)] + 
                                         shared_secret[i % shared_secret_len] + 
                                         info[i % sizeof(info)]) & 0xFF);
    }
    
    return TLS_SUCCESS;
}

/**
 * @brief Derive traffic keys
 */
static tls_result_t tls_derive_traffic_keys(tls1_3_context_t *ctx) {
    // In real implementation, this would use HKDF to derive keys
    // For DDD demonstration, we'll use a simple approach
    
    // Derive client write key
    for (int i = 0; i < 32; i++) {
        ctx->client_write_key[i] = (uint8_t)((ctx->master_secret[i % 48] + i) & 0xFF);
    }
    
    // Derive server write key
    for (int i = 0; i < 32; i++) {
        ctx->server_write_key[i] = (uint8_t)((ctx->master_secret[i % 48] + i + 128) & 0xFF);
    }
    
    // Derive IVs
    for (int i = 0; i < 12; i++) {
        ctx->client_write_iv[i] = (uint8_t)((ctx->master_secret[i % 48] + i + 64) & 0xFF);
        ctx->server_write_iv[i] = (uint8_t)((ctx->master_secret[i % 48] + i + 192) & 0xFF);
    }
    
    return TLS_SUCCESS;
}

/**
 * @brief Process client hello message
 */
static tls_result_t tls_process_client_hello(tls1_3_context_t *ctx, 
                                           const uint8_t *data, 
                                           size_t data_len) {
    if (ctx->state != TLS_STATE_CLIENT_HELLO) {
        return TLS_ERROR_INVALID_STATE;
    }
    
    // Parse client hello (simplified for DDD demonstration)
    if (data_len < 4) {
        return TLS_ERROR_INVALID_MESSAGE;
    }
    
    // Extract client random (simplified parsing)
    memcpy(ctx->client_random, data + 4, 32);
    
    // Move to server hello state
    ctx->state = TLS_STATE_SERVER_HELLO;
    
    return TLS_SUCCESS;
}

/**
 * @brief Process server hello message
 */
static tls_result_t tls_process_server_hello(tls1_3_context_t *ctx, 
                                           const uint8_t *data, 
                                           size_t data_len) {
    if (ctx->state != TLS_STATE_SERVER_HELLO) {
        return TLS_ERROR_INVALID_STATE;
    }
    
    // Parse server hello (simplified for DDD demonstration)
    if (data_len < 4) {
        return TLS_ERROR_INVALID_MESSAGE;
    }
    
    // Extract server random (simplified parsing)
    memcpy(ctx->server_random, data + 4, 32);
    
    // Move to change cipher spec state
    ctx->state = TLS_STATE_CHANGE_CIPHER_SPEC;
    
    return TLS_SUCCESS;
}

/**
 * @brief Process change cipher spec message
 */
static tls_result_t tls_process_change_cipher_spec(tls1_3_context_t *ctx, 
                                                  const uint8_t *data, 
                                                  size_t data_len) {
    if (ctx->state != TLS_STATE_CHANGE_CIPHER_SPEC) {
        return TLS_ERROR_INVALID_STATE;
    }
    
    // Process change cipher spec (simplified for DDD demonstration)
    if (data_len < 1 || data[0] != 1) {
        return TLS_ERROR_INVALID_MESSAGE;
    }
    
    // Derive keys (in real implementation, this would use the shared secret)
    uint8_t shared_secret[32] = {0}; // Placeholder for shared secret
    tls_result_t result = tls_derive_master_secret(ctx, shared_secret, sizeof(shared_secret));
    if (result != TLS_SUCCESS) {
        return result;
    }
    
    result = tls_derive_traffic_keys(ctx);
    if (result != TLS_SUCCESS) {
        return result;
    }
    
    // Initialize AES context for encryption/decryption
    result = aes_init(ctx->aes_ctx, ctx->client_write_key, AES_KEY_256);
    if (result != AES_SUCCESS) {
        return TLS_ERROR_CRYPTO_FAILURE;
    }
    
    // Move to finished state
    ctx->state = TLS_STATE_FINISHED;
    
    return TLS_SUCCESS;
}

/**
 * @brief Process finished message
 */
static tls_result_t tls_process_finished(tls1_3_context_t *ctx, 
                                       const uint8_t *data, 
                                       size_t data_len) {
    if (ctx->state != TLS_STATE_FINISHED) {
        return TLS_ERROR_INVALID_STATE;
    }
    
    // Process finished message (simplified for DDD demonstration)
    if (data_len < 32) {
        return TLS_ERROR_INVALID_MESSAGE;
    }
    
    // Verify finished message (in real implementation, this would verify MAC)
    // For DDD demonstration, we'll just check length
    
    // Move to application data state
    ctx->state = TLS_STATE_APPLICATION_DATA;
    
    return TLS_SUCCESS;
}

/**
 * @brief Initialize TLS 1.3 context
 */
tls_result_t tls1_3_init(tls1_3_context_t *ctx) {
    if (!ctx) {
        return TLS_ERROR_INVALID_PARAM;
    }
    
    memset(ctx, 0, sizeof(tls1_3_context_t));
    ctx->state = TLS_STATE_CLIENT_HELLO;
    
    // Initialize crypto contexts
    ctx->aes_ctx = malloc(sizeof(aes_context_t));
    ctx->sha256_ctx = malloc(sizeof(sha256_context_t));
    ctx->rsa_ctx = malloc(sizeof(rsa_context_t));
    ctx->ec_ctx = malloc(sizeof(ec_context_t));
    
    if (!ctx->aes_ctx || !ctx->sha256_ctx || !ctx->rsa_ctx || !ctx->ec_ctx) {
        tls1_3_cleanup(ctx);
        return TLS_ERROR_MEMORY_ALLOCATION;
    }
    
    // Initialize crypto contexts
    sha256_init(ctx->sha256_ctx);
    rsa_init(ctx->rsa_ctx);
    ec_init(ctx->ec_ctx);
    
    return TLS_SUCCESS;
}

/**
 * @brief Process TLS 1.3 handshake message
 */
tls_result_t tls1_3_process_handshake(tls1_3_context_t *ctx, 
                                     const uint8_t *data, 
                                     size_t data_len) {
    if (!ctx || !data) {
        return TLS_ERROR_INVALID_PARAM;
    }
    
    if (data_len < 4) {
        return TLS_ERROR_INVALID_MESSAGE;
    }
    
    uint8_t msg_type = data[0];
    
    switch (msg_type) {
        case TLS_MSG_CLIENT_HELLO:
            return tls_process_client_hello(ctx, data, data_len);
            
        case TLS_MSG_SERVER_HELLO:
            return tls_process_server_hello(ctx, data, data_len);
            
        case TLS_MSG_CHANGE_CIPHER_SPEC:
            return tls_process_change_cipher_spec(ctx, data, data_len);
            
        case TLS_MSG_FINISHED:
            return tls_process_finished(ctx, data, data_len);
            
        default:
            return TLS_ERROR_UNSUPPORTED_MESSAGE;
    }
}

/**
 * @brief Encrypt application data
 */
tls_result_t tls1_3_encrypt_data(tls1_3_context_t *ctx, 
                                const uint8_t *plaintext, 
                                size_t plaintext_len,
                                uint8_t *ciphertext, 
                                size_t *ciphertext_len) {
    if (!ctx || !plaintext || !ciphertext || !ciphertext_len) {
        return TLS_ERROR_INVALID_PARAM;
    }
    
    if (ctx->state != TLS_STATE_APPLICATION_DATA) {
        return TLS_ERROR_INVALID_STATE;
    }
    
    if (plaintext_len % 16 != 0) {
        return TLS_ERROR_INVALID_BLOCK_SIZE;
    }
    
    // Encrypt data using AES (simplified for DDD demonstration)
    size_t blocks = plaintext_len / 16;
    for (size_t i = 0; i < blocks; i++) {
        aes_result_t result = aes_encrypt_block(ctx->aes_ctx, 
                                              plaintext + i * 16, 
                                              ciphertext + i * 16);
        if (result != AES_SUCCESS) {
            return TLS_ERROR_CRYPTO_FAILURE;
        }
    }
    
    *ciphertext_len = plaintext_len;
    ctx->sequence_number++;
    
    return TLS_SUCCESS;
}

/**
 * @brief Decrypt application data
 */
tls_result_t tls1_3_decrypt_data(tls1_3_context_t *ctx, 
                                const uint8_t *ciphertext, 
                                size_t ciphertext_len,
                                uint8_t *plaintext, 
                                size_t *plaintext_len) {
    if (!ctx || !ciphertext || !plaintext || !plaintext_len) {
        return TLS_ERROR_INVALID_PARAM;
    }
    
    if (ctx->state != TLS_STATE_APPLICATION_DATA) {
        return TLS_ERROR_INVALID_STATE;
    }
    
    if (ciphertext_len % 16 != 0) {
        return TLS_ERROR_INVALID_BLOCK_SIZE;
    }
    
    // Decrypt data using AES (simplified for DDD demonstration)
    size_t blocks = ciphertext_len / 16;
    for (size_t i = 0; i < blocks; i++) {
        aes_result_t result = aes_decrypt_block(ctx->aes_ctx, 
                                              ciphertext + i * 16, 
                                              plaintext + i * 16);
        if (result != AES_SUCCESS) {
            return TLS_ERROR_CRYPTO_FAILURE;
        }
    }
    
    *plaintext_len = ciphertext_len;
    ctx->sequence_number++;
    
    return TLS_SUCCESS;
}

/**
 * @brief Get current handshake state
 */
tls_handshake_state_t tls1_3_get_state(const tls1_3_context_t *ctx) {
    if (!ctx) {
        return TLS_STATE_ERROR;
    }
    
    return ctx->state;
}

/**
 * @brief Clean up TLS 1.3 context
 */
void tls1_3_cleanup(tls1_3_context_t *ctx) {
    if (!ctx) {
        return;
    }
    
    if (ctx->aes_ctx) {
        aes_cleanup(ctx->aes_ctx);
        free(ctx->aes_ctx);
        ctx->aes_ctx = NULL;
    }
    
    if (ctx->sha256_ctx) {
        sha256_cleanup(ctx->sha256_ctx);
        free(ctx->sha256_ctx);
        ctx->sha256_ctx = NULL;
    }
    
    if (ctx->rsa_ctx) {
        rsa_cleanup(ctx->rsa_ctx);
        free(ctx->rsa_ctx);
        ctx->rsa_ctx = NULL;
    }
    
    if (ctx->ec_ctx) {
        ec_cleanup(ctx->ec_ctx);
        free(ctx->ec_ctx);
        ctx->ec_ctx = NULL;
    }
    
    // Clear sensitive data
    memset(ctx, 0, sizeof(tls1_3_context_t));
}