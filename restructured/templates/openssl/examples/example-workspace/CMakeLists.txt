cmake_minimum_required(VERSION 3.15)
project(OpenSSLExample VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenSSL REQUIRED)
find_package(ZLIB REQUIRED)

# Include directories
include_directories(${OPENSSL_INCLUDE_DIR})
include_directories(${ZLIB_INCLUDE_DIRS})

# Source files
set(SOURCES
    src/main.cpp
    src/crypto_utils.cpp
)

# Create library
add_library(openssl_example ${SOURCES})

# Link libraries
target_link_libraries(openssl_example 
    OpenSSL::SSL 
    OpenSSL::Crypto 
    ZLIB::ZLIB
)

# Set properties
set_target_properties(openssl_example PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# Install targets
install(TARGETS openssl_example
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

# Install headers
install(DIRECTORY src/ DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)